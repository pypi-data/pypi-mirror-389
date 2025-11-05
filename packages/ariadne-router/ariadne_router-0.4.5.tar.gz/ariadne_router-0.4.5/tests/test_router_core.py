"""Targeted unit tests for the high-level routing interface."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from qiskit import QuantumCircuit

from ariadne.router import _execute_simulation, simulate
from ariadne.types import BackendType, RoutingDecision, SimulationResult


class _DummyLogger:
    def __getattr__(self, _name: str):
        def _noop(*_args, **_kwargs):
            return None

        return _noop


def _make_routing_decision(backend: BackendType) -> RoutingDecision:
    return RoutingDecision(
        circuit_entropy=0.0,
        recommended_backend=backend,
        confidence_score=1.0,
        expected_speedup=1.0,
        channel_capacity_match=1.0,
        alternatives=[],
    )


def _make_simulation_result(backend: BackendType) -> SimulationResult:
    return SimulationResult(
        counts={"0": 1},
        backend_used=backend,
        execution_time=0.01,
        routing_decision=_make_routing_decision(backend),
        metadata={"shots": 32},
    )


@pytest.fixture(autouse=True)
def stub_router_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    import ariadne.router as router

    # Stubs to avoid touching global state or heavy dependencies
    monkeypatch.setattr(router, "get_logger", lambda _name: _DummyLogger())
    monkeypatch.setattr(
        router,
        "get_config",
        lambda: SimpleNamespace(analysis=SimpleNamespace(enable_resource_estimation=False)),
    )

    class StubResourceManager:
        def get_resources(self):
            return SimpleNamespace(available_memory_mb=1024)

        def reserve_resources(self, *_args, **_kwargs):
            return "token"

        def release_resources(self, *_args, **_kwargs):
            return None

    monkeypatch.setattr(router, "get_resource_manager", lambda: StubResourceManager())
    monkeypatch.setattr(router, "check_circuit_feasibility", lambda circuit, backend: (True, "ok"))

    # Avoid loading tensor backend globally
    monkeypatch.setattr(router, "TensorNetworkBackend", object, raising=False)


def test_simulate_forced_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    import ariadne.router as router

    circuit = QuantumCircuit(1)
    circuit.h(0)

    # Ensure forced backend path bypasses router logic
    def stub_execute(circuit, shots, decision):
        result = _make_simulation_result(decision.recommended_backend)
        result.metadata["shots"] = shots
        return result

    monkeypatch.setattr(router, "_execute_simulation", stub_execute)

    result = simulate(circuit, shots=8, backend="stim")

    assert result.backend_used == BackendType.STIM
    assert result.metadata["shots"] == 8


def test_simulate_uses_predictive_model(monkeypatch: pytest.MonkeyPatch) -> None:
    import ariadne.router as router

    circuit = QuantumCircuit(2)
    circuit.cx(0, 1)

    monkeypatch.setenv("ARIADNE_ROUTING_PREDICT", "1")
    monkeypatch.setattr("ariadne.route.routing_tree.get_available_backends", lambda: ["qiskit", "cuda"])

    class DummyPrediction:
        backend = BackendType.CUDA
        predicted_time = 0.1
        predicted_memory_mb = 10
        predicted_success_rate = 0.9
        confidence_score = 0.6
        feature_importance = {}

    monkeypatch.setattr(
        "ariadne.route.performance_model.find_optimal_backend",
        lambda circuit, available, optimize_for="time": (BackendType.CUDA, DummyPrediction()),
    )

    def stub_execute(circuit, shots, decision):
        result = _make_simulation_result(decision.recommended_backend)
        result.metadata["shots"] = shots
        return result

    monkeypatch.setattr(router, "_execute_simulation", stub_execute)

    result = simulate(circuit, shots=4)
    assert result.backend_used == BackendType.CUDA


def test_execute_simulation_fallback_to_qiskit(monkeypatch: pytest.MonkeyPatch) -> None:
    import ariadne.router as router

    circuit = QuantumCircuit(2)
    circuit.cx(0, 1)

    def failing_tensor(circ, shots):
        raise RuntimeError("tensor backend failure")

    monkeypatch.setattr(router, "_simulate_tensor_network", failing_tensor)
    monkeypatch.setattr(router, "_simulate_qiskit", lambda circuit, shots: {"11": shots})

    decision = _make_routing_decision(BackendType.TENSOR_NETWORK)
    result = _execute_simulation(circuit, 16, decision)

    assert result.backend_used == BackendType.QISKIT
    assert result.fallback_reason is not None


def test_execute_simulation_resource_exhaustion(monkeypatch: pytest.MonkeyPatch) -> None:
    import ariadne.router as router
    from ariadne.core import ResourceExhaustionError

    circuit = QuantumCircuit(3)
    circuit.h(0)

    monkeypatch.setattr(
        router, "get_config", lambda: SimpleNamespace(analysis=SimpleNamespace(enable_resource_estimation=True))
    )
    monkeypatch.setattr(router, "check_circuit_feasibility", lambda circuit, backend: (False, "too large"))

    # Ensure resource checks are enabled for this test, regardless of CI environment
    monkeypatch.setenv("ARIADNE_DISABLE_RESOURCE_CHECKS", "0")

    with pytest.raises(ResourceExhaustionError):
        _execute_simulation(circuit, 4, _make_routing_decision(BackendType.QISKIT))


def test_simulate_handles_empty_circuit(monkeypatch: pytest.MonkeyPatch) -> None:
    empty = QuantumCircuit()
    result = simulate(empty, shots=0)

    assert result.backend_used == BackendType.QISKIT
    assert result.counts == {}
