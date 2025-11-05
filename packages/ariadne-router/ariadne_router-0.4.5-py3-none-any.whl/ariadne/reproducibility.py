"""Reproducibility utilities for cross-backend validation.

This module provides helpers to:
- Load circuits from the benchmark datasets
- Run a circuit across multiple backends
- Compare result distributions for consistency

The default comparison metric is Jensen–Shannon divergence (JSD) over
measurement count distributions. Lower is better; values below ~0.05 are
typically considered consistent for finite-shot experiments.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from qiskit import QuantumCircuit

from .router import is_cuda_available, is_metal_available, simulate
from .types import BackendType

DATASETS_DIR = Path("benchmarks/datasets")
HOME_DATASETS_DIR = Path.home() / ".ariadne" / "datasets"


@dataclass
class BackendComparison:
    backend: str
    counts: dict[str, int]
    success: bool
    error: str | None = None


def _normalize_counts(counts: dict[str, int]) -> tuple[np.ndarray, list[str]]:
    """Return probability vector and ordered keys for counts dict."""
    if not counts:
        return np.array([], dtype=float), []
    keys = sorted(counts.keys())
    total = float(sum(counts.values())) or 1.0
    vec = np.array([counts[k] / total for k in keys], dtype=float)
    return vec, keys


def jensen_shannon_divergence(c1: dict[str, int], c2: dict[str, int]) -> float:
    """Compute Jensen–Shannon divergence between two count dictionaries.

    Returns value in [0, 1]. 0 indicates identical distributions.
    """
    # Align keys
    all_keys = sorted(set(c1.keys()) | set(c2.keys()))
    if not all_keys:
        return 0.0

    def probs(counts: dict[str, int]) -> np.ndarray:
        total = float(sum(counts.values())) or 1.0
        return np.array([counts.get(k, 0) / total for k in all_keys], dtype=float)

    p = probs(c1)
    q = probs(c2)
    m = 0.5 * (p + q)

    def _kl(a: np.ndarray, b: np.ndarray) -> float:
        mask = (a > 0) & (b > 0)
        return float(np.sum(a[mask] * (np.log2(a[mask]) - np.log2(b[mask]))))

    jsd = 0.5 * _kl(p, m) + 0.5 * _kl(q, m)
    # Return the square root (Jensen–Shannon distance) for interpretability
    return float(np.sqrt(jsd))


def load_circuit(path_or_name: str | Path) -> QuantumCircuit:
    """Load a circuit from a QASM file or dataset name.

    If ``path_or_name`` is a bare name (e.g., "ghz_20"), the function searches
    under ``benchmarks/datasets`` for a matching file with ".qasm" or ".qasm2".
    """
    path = Path(path_or_name)
    if not path.exists():
        # Try dataset lookup
        candidates: list[Path] = []
        for base in (DATASETS_DIR, HOME_DATASETS_DIR):
            for ext in (".qasm", ".qasm2"):
                candidates.append(base / f"{path_or_name}{ext}")
        for candidate in candidates:
            if candidate.exists():
                path = candidate
                break
    if not path.exists():
        raise FileNotFoundError(f"Circuit not found: {path_or_name}")

    return QuantumCircuit.from_qasm_file(str(path))


def default_backends() -> list[str]:
    """Return a reasonable set of backends for cross-validation on this system."""
    backends: list[str] = [BackendType.QISKIT.value, BackendType.TENSOR_NETWORK.value]
    # Stim only supports Clifford; include if present in environment
    backends.append(BackendType.STIM.value)
    if is_cuda_available():
        backends.append(BackendType.CUDA.value)
    if is_metal_available():
        backends.append(BackendType.JAX_METAL.value)
    return backends


def run_across_backends(
    circuit: QuantumCircuit,
    backends: Iterable[str] | None = None,
    shots: int = 1000,
) -> list[BackendComparison]:
    """Run ``circuit`` across ``backends`` and collect counts."""
    if backends is None:
        backends = default_backends()

    results: list[BackendComparison] = []
    for backend in backends:
        try:
            b_arg: str | None = None if backend == "auto" else backend
            sim = simulate(circuit, shots=shots, backend=b_arg)
            results.append(BackendComparison(backend=backend, counts=sim.counts, success=True))
        except Exception as exc:  # pragma: no cover - env dependent
            results.append(BackendComparison(backend=backend, counts={}, success=False, error=str(exc)))
    return results


def compare_results(results: list[BackendComparison], metric: str = "jsd") -> dict[str, float]:
    """Compute pairwise distances across backend results.

    Returns a mapping ``"backendA|backendB" -> distance``.
    """
    distances: dict[str, float] = {}
    ok = [r for r in results if r.success]
    for i in range(len(ok)):
        for j in range(i + 1, len(ok)):
            a, b = ok[i], ok[j]
            if metric == "jsd":
                d = jensen_shannon_divergence(a.counts, b.counts)
            else:
                raise ValueError(f"Unsupported metric: {metric}")
            distances[f"{a.backend}|{b.backend}"] = d
    return distances


def cross_validate(
    circuit_or_path: QuantumCircuit | str | Path,
    backends: Iterable[str] | None = None,
    shots: int = 1000,
    tolerance: float = 0.05,
    metric: str = "jsd",
) -> dict[str, object]:
    """Run cross-backend validation for a circuit.

    Returns a report with per-backend results and pairwise distances.
    """
    circuit = circuit_or_path if isinstance(circuit_or_path, QuantumCircuit) else load_circuit(circuit_or_path)

    runs = run_across_backends(circuit, backends=backends, shots=shots)
    distances = compare_results(runs, metric=metric)

    max_distance = max(distances.values()) if distances else 0.0
    consistent = max_distance <= tolerance if distances else len([r for r in runs if r.success]) > 0

    return {
        "consistent": consistent,
        "metric": metric,
        "tolerance": tolerance,
        "max_distance": max_distance,
        "distances": distances,
        "results": [r.__dict__ for r in runs],
    }


__all__ = [
    "BackendComparison",
    "cross_validate",
    "default_backends",
    "jensen_shannon_divergence",
    "load_circuit",
    "run_across_backends",
    "compare_results",
]
