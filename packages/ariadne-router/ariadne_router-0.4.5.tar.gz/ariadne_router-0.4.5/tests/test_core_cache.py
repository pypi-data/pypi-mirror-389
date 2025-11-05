"""Tests for the circuit analysis cache utilities."""

from __future__ import annotations

import itertools
from collections import Counter

import pytest
from qiskit import QuantumCircuit

from ariadne.core.cache import (
    CacheError,
    CircuitAnalysisCache,
    cached_analyze,
    get_global_cache,
    set_global_cache,
)


@pytest.fixture(autouse=True)
def reset_global_cache() -> None:
    """Ensure each test runs with a clean global cache."""

    original_cache = get_global_cache()
    set_global_cache(CircuitAnalysisCache())
    try:
        yield
    finally:
        set_global_cache(original_cache)


def _make_circuit(width: int = 2) -> QuantumCircuit:
    circuit = QuantumCircuit(width)
    for index in range(width - 1):
        circuit.h(index)
        circuit.cx(index, index + 1)
    return circuit


def test_store_and_retrieve_analysis() -> None:
    cache = CircuitAnalysisCache(max_size=4, ttl_seconds=100.0)
    circuit = _make_circuit(3)
    analysis = {"depth": circuit.depth(), "gate_count": circuit.size()}

    cache.store_analysis(circuit, analysis)
    retrieved = cache.get_analysis(circuit)

    assert retrieved == analysis
    assert retrieved is not analysis  # ensure defensive copy supplied
    assert cache.get_stats()["hits"] == 1


def test_cache_respects_ttl(monkeypatch: pytest.MonkeyPatch) -> None:
    cache = CircuitAnalysisCache(max_size=2, ttl_seconds=5.0)
    circuit = _make_circuit(2)
    analysis = {"value": 1}

    times = itertools.count(start=100)
    monkeypatch.setattr("ariadne.core.cache.time.time", lambda: next(times))

    cache.store_analysis(circuit, analysis)
    assert cache.get_analysis(circuit) == analysis

    # Fast-forward beyond TTL
    for _ in range(10):
        next(times)

    assert cache.get_analysis(circuit) is None
    assert cache.cleanup_expired() == 0  # already evicted by stale access


def test_cache_eviction_policy() -> None:
    cache = CircuitAnalysisCache(max_size=1, ttl_seconds=100.0)
    first = _make_circuit(2)
    second = _make_circuit(3)

    cache.store_analysis(first, {"id": "first"})
    cache.store_analysis(second, {"id": "second"})

    assert cache.get_analysis(first) is None
    assert cache.get_analysis(second)["id"] == "second"
    assert cache.get_stats()["evictions"] == 1


def test_get_entry_info_reports_metadata() -> None:
    cache = CircuitAnalysisCache(max_size=2, ttl_seconds=100.0)
    circuit = _make_circuit(2)
    cache.store_analysis(circuit, {"depth": 3})
    info = cache.get_entry_info(circuit)

    assert info is not None
    assert info["access_count"] == 1
    assert info["expired"] is False


def test_cached_analyze_invokes_underlying_once() -> None:
    cache = CircuitAnalysisCache(max_size=3, ttl_seconds=100.0)
    set_global_cache(cache)

    circuit = _make_circuit(2)
    calls = Counter()

    def analyzer(qc: QuantumCircuit, scale: int) -> dict[str, int]:
        calls["count"] += 1
        return {"scaled_depth": qc.depth() * scale}

    first = cached_analyze(circuit, analyzer, 2)
    second = cached_analyze(circuit, analyzer, 2)

    assert first == second
    assert calls["count"] == 1


def test_circuit_hash_error_raises_cache_error(monkeypatch: pytest.MonkeyPatch) -> None:
    cache = CircuitAnalysisCache()
    circuit = _make_circuit(2)

    def broken_hash(_circuit: QuantumCircuit) -> str:
        raise ValueError("broken lookup")

    monkeypatch.setattr(cache, "_circuit_hash", broken_hash)

    with pytest.raises(CacheError):
        cache.store_analysis(circuit, {"depth": 2})
