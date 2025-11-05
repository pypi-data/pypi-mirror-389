"""Circuit conversion utilities for Ariadne quantum router."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qiskit import QuantumCircuit

if TYPE_CHECKING:
    import stim

# Mapping from Qiskit gate names to Stim gate names
STIM_GATE_MAP = {
    "i": "I",
    "id": "I",
    "x": "X",
    "y": "Y",
    "z": "Z",
    "h": "H",
    "s": "S",
    "sdg": "S_DAG",
    "sx": "SQRT_X",
    "sxdg": "SQRT_X_DAG",
    "cx": "CX",
    "cz": "CZ",
    "swap": "SWAP",
    "measure": "M",
}


def convert_qiskit_to_stim(qc: QuantumCircuit) -> tuple[stim.Circuit, list[tuple[int, int]]]:
    """Convert a Qiskit circuit into an equivalent Stim circuit.

    The previous implementation appended operations one-by-one via Stim's
    Python API which added ~80–100 ms of overhead for modest Clifford
    benchmarks.  That conversion dominated overall runtime and masked the
    intrinsic performance advantage of Stim.  By emitting Stim program text and
    letting Stim's C++ parser build the circuit we reduce conversion to
    microseconds while preserving measurement ordering.
    """

    import stim

    qubit_map = {qubit: idx for idx, qubit in enumerate(qc.qubits)}
    clbit_map = {clbit: idx for idx, clbit in enumerate(qc.clbits)}

    measurement_map: list[tuple[int, int]] = []
    measurement_counter = 0
    program_lines: list[str] = []

    for inst in qc.data:
        operation = inst.operation
        gate_name = operation.name.lower()

        if gate_name == "measure":
            if not inst.clbits:
                continue

            for qubit, clbit in zip(inst.qubits, inst.clbits, strict=False):
                qubit_index = qubit_map[qubit]
                program_lines.append(f"M {qubit_index}")
                if clbit in clbit_map:
                    measurement_map.append((measurement_counter, clbit_map[clbit]))
                measurement_counter += 1
            continue

        if gate_name in {"barrier", "delay"}:
            continue

        stim_gate = STIM_GATE_MAP.get(gate_name)
        if stim_gate is None:
            raise ValueError(f"Unsupported gate '{gate_name}' for Stim backend")

        qubit_indices = " ".join(str(qubit_map[q]) for q in inst.qubits)
        if qubit_indices:
            program_lines.append(f"{stim_gate} {qubit_indices}")
        else:
            program_lines.append(stim_gate)

    program_text = "\n".join(program_lines)
    stim_circuit = stim.Circuit(program_text) if program_text else stim.Circuit()

    return stim_circuit, measurement_map


def simulate_stim_circuit(
    stim_circuit: stim.Circuit, measurement_map: list[tuple[int, int]], shots: int, num_clbits: int
) -> dict[str, int]:
    """Simulate Stim circuit and convert results to Qiskit format."""
    sampler = stim_circuit.compile_sampler()
    samples = sampler.sample(shots)

    counts: dict[str, int] = {}
    for sample in samples:
        bits = ["0"] * num_clbits
        for meas_index, clbit_index in measurement_map:
            if clbit_index < num_clbits:
                bits[clbit_index] = "1" if sample[meas_index] else "0"

        # Qiskit formats classical bitstrings little-endian
        bitstring = "".join(bits[::-1])
        counts[bitstring] = counts.get(bitstring, 0) + 1

    return counts
