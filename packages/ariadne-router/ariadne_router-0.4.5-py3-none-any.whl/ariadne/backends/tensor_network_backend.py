"""Tensor network backend built on top of Quimb and Cotengra."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from qiskit import QuantumCircuit


@dataclass
class TensorNetworkOptions:
    """Configuration for the tensor network contraction and sampling.

    Attributes:
        max_bond_dim: Optional maximum bond dimension for contraction.
        max_time: Optimizer time budget in seconds.
        max_repeats: Number of optimizer repeats.
        seed: RNG seed for reproducible sampling.
        bitstring_order: Output bitstring order for counts. "qiskit" (default)
            returns little-endian bitstrings matching Qiskit's convention.
            "msb" returns most-significant-bit-first strings that match the
            natural integer-to-binary mapping.
    """

    max_bond_dim: int | None = None
    max_time: float = 10.0
    max_repeats: int = 32
    seed: int | None = None
    bitstring_order: str = "qiskit"


class TensorNetworkBackend:
    """Perform circuit simulation via tensor network contraction."""

    def __init__(self, options: TensorNetworkOptions | None = None) -> None:
        self._options = options or TensorNetworkOptions()
        self._optimizer: Any | None = None

    def simulate(self, circuit: QuantumCircuit, shots: int) -> dict[str, int]:
        """Return measurement counts for ``circuit`` using tensor networks."""

        if shots < 0:
            raise ValueError("shots must be non-negative")

        if shots == 0:
            return {}

        num_qubits = circuit.num_qubits
        if num_qubits == 0:
            return {"": shots}

        try:
            quimb_circuit = self._compile_to_tensor_network(circuit)
            state = self._contract_statevector(quimb_circuit)
        except ImportError:
            # Optional deps missing; fall back to Qiskit's statevector path
            from qiskit.quantum_info import Statevector

            state = Statevector.from_instruction(circuit).data
        return self._sample_counts(state, shots, num_qubits)

    # ------------------------------------------------------------------
    # Internal helpers

    def _compile_to_tensor_network(self, circuit: QuantumCircuit) -> Any:
        try:
            import qiskit.qasm2 as qasm2
            import quimb.tensor as qtn
            from qiskit import transpile
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise ImportError("Tensor network dependencies not installed") from exc

        try:
            # Decompose to basic gates supported by OpenQASM 2 and quimb
            # This handles mcx, p gates and other complex operations
            decomposed = transpile(
                circuit,
                basis_gates=["u1", "u2", "u3", "cx", "id", "h", "x", "y", "z", "s", "t", "sdg", "tdg"],
                optimization_level=0,
            )
            qasm_str = qasm2.dumps(decomposed)
        except Exception as exc:  # pragma: no cover - depends on qiskit feature set
            raise RuntimeError(f"Failed to decompose/export circuit to OpenQASM 2: {exc}") from exc

        try:
            return qtn.Circuit.from_openqasm2_str(qasm_str)
        except Exception as exc:  # pragma: no cover - conversion can fail for unsupported ops
            raise RuntimeError(f"Failed to convert circuit to tensor network: {exc}") from exc

    def _contract_statevector(self, quimb_circuit: Any) -> np.ndarray:
        try:
            import cotengra as ctg
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise ImportError("Cotengra must be installed for tensor network simulation") from exc

        if self._optimizer is None:
            self._optimizer = ctg.HyperOptimizer(
                methods=("greedy", "random"),
                max_time=self._options.max_time,
                max_repeats=self._options.max_repeats,
                progbar=False,
            )

        contract_opts = {"optimize": self._optimizer}
        if self._options.max_bond_dim is not None:
            contract_opts["max_bond"] = self._options.max_bond_dim

        try:
            dense_state = quimb_circuit.to_dense(**contract_opts)
        except Exception as exc:  # pragma: no cover - contraction failures are rare but possible
            raise RuntimeError("Tensor network contraction failed") from exc

        return np.asarray(dense_state).reshape(-1)

    def _sample_counts(self, statevector: np.ndarray, shots: int, num_qubits: int) -> dict[str, int]:
        if shots == 0:
            return {}

        if statevector.ndim != 1:
            raise ValueError("Statevector must be one-dimensional")

        probabilities = np.abs(statevector) ** 2
        total = float(probabilities.sum())
        if total == 0.0:
            raise RuntimeError("Invalid statevector produced by tensor network")
        if not np.isclose(total, 1.0):
            probabilities = probabilities / total

        rng = np.random.default_rng(self._options.seed)
        outcomes = rng.choice(len(probabilities), size=shots, p=probabilities)

        counts: dict[str, int] = {}
        for outcome in outcomes:
            bits = format(int(outcome), f"0{num_qubits}b")
            if (self._options.bitstring_order or "qiskit").lower() == "qiskit":
                # Qiskit's little-endian bitstring convention requires reversing
                bitstring = bits[::-1]
            else:
                bitstring = bits
            counts[bitstring] = counts.get(bitstring, 0) + 1
        return counts
