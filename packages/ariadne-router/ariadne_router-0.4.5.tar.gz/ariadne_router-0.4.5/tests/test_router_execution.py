from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest
from qiskit import QuantumCircuit

from ariadne.core.resource_manager import ResourceRequirements
from ariadne.router import BackendType, RoutingDecision, _execute_simulation, _sample_statevector_counts, simulate


class _DummyResources:
    def __init__(self) -> None:
        self.available_memory_mb = 512.0
        self.total_memory_mb = 1024.0
        self.available_cpu_cores = 4
        self.total_cpu_cores = 4


class _DummyResourceManager:
    def __init__(self) -> None:
        self.reserved = False
        self.released = False
        self._resources = _DummyResources()

    def get_resources(self) -> _DummyResources:
        return self._resources

    def reserve_resources(self, circuit: QuantumCircuit, backend: str) -> ResourceRequirements:
        self.reserved = True
        return ResourceRequirements(memory_mb=8.0, cpu_cores=1, estimated_time_seconds=0.01, backend=backend)

    def release_resources(self, requirements: ResourceRequirements) -> None:
        self.released = True


@pytest.fixture(autouse=True)
def _patch_explain_routing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "ariadne.route.routing_tree.explain_routing",
        lambda _circuit: "explanation-path",
        raising=False,
    )


def _make_routing_decision(backend: BackendType) -> RoutingDecision:
    return RoutingDecision(
        circuit_entropy=0.1,
        recommended_backend=backend,
        confidence_score=0.9,
        expected_speedup=1.2,
        channel_capacity_match=0.85,
        alternatives=[],
    )


def test_execute_simulation_fallback_releases_resources(monkeypatch: pytest.MonkeyPatch) -> None:
    circuit = QuantumCircuit(1)
    circuit.x(0)

    routing_decision = _make_routing_decision(BackendType.CUDA)

    dummy_cfg = SimpleNamespace(analysis=SimpleNamespace(enable_resource_estimation=True))
    monkeypatch.setattr("ariadne.router.get_config", lambda: dummy_cfg)
    monkeypatch.setattr("ariadne.router.check_circuit_feasibility", lambda _c, _b: (True, "ok"))

    # Ensure resource checks are enabled for this test, regardless of CI environment
    monkeypatch.setenv("ARIADNE_DISABLE_RESOURCE_CHECKS", "0")

    manager = _DummyResourceManager()
    monkeypatch.setattr("ariadne.router.get_resource_manager", lambda: manager)

    def _fail_cuda(_circuit: QuantumCircuit, _shots: int) -> dict[str, int]:
        raise RuntimeError("matrix blowup")

    monkeypatch.setattr("ariadne.router._simulate_cuda", _fail_cuda)
    monkeypatch.setattr("ariadne.router._simulate_qiskit", lambda _c, s: {"0": s})

    result = _execute_simulation(circuit, shots=8, routing_decision=routing_decision)

    assert result.backend_used == BackendType.QISKIT
    assert result.counts == {"0": 8}
    assert result.fallback_reason == "Backend cuda failed: matrix blowup"
    assert manager.reserved and manager.released


def test_execute_simulation_adds_metal_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    circuit = QuantumCircuit(1)
    routing_decision = _make_routing_decision(BackendType.JAX_METAL)

    dummy_cfg = SimpleNamespace(analysis=SimpleNamespace(enable_resource_estimation=False))
    monkeypatch.setattr("ariadne.router.get_config", lambda: dummy_cfg)
    monkeypatch.setattr("ariadne.router.get_resource_manager", lambda: _DummyResourceManager())
    monkeypatch.setattr("ariadne.router.is_metal_available", lambda: True)
    monkeypatch.setattr("ariadne.router._simulate_jax_metal", lambda _c, _s: {"0": 1})

    result = _execute_simulation(circuit, shots=1, routing_decision=routing_decision)

    assert result.backend_used == BackendType.JAX_METAL
    assert result.warnings == ["JAX-Metal support is experimental and may show warnings"]
    assert result.fallback_reason is None


def test_sample_statevector_counts_behaviour(monkeypatch: pytest.MonkeyPatch) -> None:
    circuit = QuantumCircuit(1)
    circuit.h(0)

    class _DummyState:
        def __init__(self) -> None:
            self.data = np.array([np.sqrt(0.7), np.sqrt(0.3)])

    monkeypatch.setattr("ariadne.router.Statevector", SimpleNamespace(from_instruction=lambda _c: _DummyState()))

    counts = _sample_statevector_counts(circuit, shots=16, seed=123)
    assert sum(counts.values()) == 16
    assert set(counts.keys()) <= {"0", "1"}

    assert _sample_statevector_counts(circuit, shots=0) == {}

    with pytest.raises(ValueError):
        _sample_statevector_counts(circuit, shots=-4)


def test_simulate_handles_empty_circuit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("ariadne.route.routing_tree.explain_routing", lambda _circuit: "empty", raising=False)

    empty_circuit = QuantumCircuit()
    result = simulate(empty_circuit, shots=5)
    assert result.counts == {"": 5}
    assert result.backend_used == BackendType.QISKIT


def test_simulate_rejects_unknown_forced_backend() -> None:
    circuit = QuantumCircuit(1)
    with pytest.raises(ValueError):
        simulate(circuit, backend="unknown-backend")
