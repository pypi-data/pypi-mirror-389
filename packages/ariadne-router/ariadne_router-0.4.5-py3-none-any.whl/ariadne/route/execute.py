"""Legacy routing helpers retained for compatibility with older tests."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from time import perf_counter
from typing import Literal

from qiskit import QuantumCircuit

from ..router import SimulationResult
from ..router import simulate as core_simulate
from .analyze import analyze_circuit

Backend = Literal["stim", "tn", "sv", "dd"]


def decide_backend(circuit: QuantumCircuit) -> Backend:
    metrics = analyze_circuit(circuit)

    if metrics.get("is_clifford", False):
        return "stim"

    treewidth = metrics.get("treewidth_estimate", 0)
    num_qubits = metrics.get("num_qubits", 0)
    depth = metrics.get("depth", 0)
    two_qubit_depth = metrics.get("two_qubit_depth", 0)
    edges = metrics.get("edges", 0)

    if treewidth <= 10 and edges <= num_qubits * 2:
        return "tn"

    if num_qubits <= 20 or two_qubit_depth >= max(1, depth // 2):
        return "sv"

    return "dd"


def _simulate_with_router(circuit: QuantumCircuit, shots: int) -> dict[str, object]:
    result: SimulationResult = core_simulate(circuit, shots=shots)
    return {
        "counts": result.counts,
        "backend": result.backend_used.value,
    }


@dataclass
class Trace:
    backend: Backend
    wall_time_s: float
    metrics: dict[str, float | int | bool]
    shots: int
    mem_cap_bytes: int | None = None
    seed: int | None = None


def execute(
    circuit: QuantumCircuit,
    shots: int = 1024,
    *,
    mem_cap_bytes: int | None = None,
    seed: int | None = None,
) -> dict[str, object]:  # pragma: no cover - integration helper
    backend = decide_backend(circuit)
    metrics = analyze_circuit(circuit)

    start = perf_counter()

    # Use router for actual simulation
    if backend == "stim" and metrics.get("is_clifford", False):
        result = _simulate_with_router(circuit, shots)
        payload = result
    else:
        # Fallback to qiskit or other backends
        try:
            from qiskit.quantum_info import Statevector

            statevector = Statevector.from_instruction(circuit)
            payload = {"statevector": statevector.data}
        except Exception as exc:
            payload = {"error": str(exc)}

    wall_time = perf_counter() - start

    trace = Trace(
        backend=backend,
        wall_time_s=wall_time,
        metrics=metrics,
        shots=shots,
        mem_cap_bytes=mem_cap_bytes,
        seed=seed,
    )
    return {"trace": asdict(trace), **payload}


@dataclass
class _SegmentRecord:
    segment_id: int
    segment_backend: Backend
    segment_depth: int
    active_qubits: int
    boundary_adapter: dict[str, int | float | str] | None = None

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        if payload["boundary_adapter"] is None:
            payload.pop("boundary_adapter")
        return payload


def execute_segmented(
    circuit: QuantumCircuit,
    *,
    mem_cap_bytes: int | None = None,
    samples: int = 1024,
    seed: int | None = None,
) -> dict[str, object]:
    """Heuristic segmented execution helper used by demos.

    The original segmented routing prototype modeled separate Clifford and
    non-Clifford regions.  That logic was removed when the main router was
    rebuilt, but the educational demo in ``examples/segmented_demo.py`` still
    depends on the legacy API.  Rather than breaking the demo, we provide a
    lightweight shim that synthesises reasonable segment metadata directly from
    the analyzer metrics, giving the example enough structure to render its
    tables and narrative.
    """

    metrics = analyze_circuit(circuit)
    num_qubits = metrics.get("num_qubits", circuit.num_qubits)
    depth = metrics.get("depth", circuit.depth())
    clifford_ratio = float(metrics.get("clifford_ratio", 0.0))

    segments: list[_SegmentRecord] = []

    # Always include an initial segment; if the circuit is mostly Clifford we
    # mark it as ``stim``, otherwise fall back to a tensor network description.
    initial_backend: Backend = "stim" if clifford_ratio >= 0.5 else "tn"
    segments.append(
        _SegmentRecord(
            segment_id=0,
            segment_backend=initial_backend,
            segment_depth=max(1, depth // 3),
            active_qubits=num_qubits,
        )
    )

    # If there is a meaningful non-Clifford portion, add a second segment that
    # represents the heavier simulation workload.  We surface a boundary
    # adapter payload so the tutorial can discuss entanglement preservation.
    non_clifford_ratio = 1.0 - clifford_ratio
    if non_clifford_ratio > 0.1:
        adapter = {
            "adapter": "exact-entanglement",
            "cut_rank": max(1, min(num_qubits // 2, 4)),
            "active_width": min(num_qubits, 32),
        }
        heavy_backend: Backend
        if num_qubits <= 18:
            heavy_backend = "sv"
        elif num_qubits <= 28:
            heavy_backend = "tn"
        else:
            heavy_backend = "dd"

        segments.append(
            _SegmentRecord(
                segment_id=1,
                segment_backend=heavy_backend,
                segment_depth=max(1, depth - segments[0].segment_depth),
                active_qubits=num_qubits,
                boundary_adapter=adapter,
            )
        )

    # Compute a lightweight trace summary for the demo output.
    trace_summary = {
        "schema_version": 1,
        "decided_backend": decide_backend(circuit),
        "segments": len(segments),
        "depth": depth,
        "num_qubits": num_qubits,
        "clifford_ratio": clifford_ratio,
        "mem_cap_bytes": mem_cap_bytes,
        "samples": samples,
        "seed": seed,
    }

    return {
        "schema_version": 1,
        "segments": [segment.as_dict() for segment in segments],
        "summary": trace_summary,
    }
