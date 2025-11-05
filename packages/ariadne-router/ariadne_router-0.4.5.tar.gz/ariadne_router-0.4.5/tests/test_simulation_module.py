from __future__ import annotations

import os
from types import SimpleNamespace

import numpy as np
import pytest
from qiskit import QuantumCircuit

import ariadne.simulation as simulation
from ariadne.router import BackendType, RoutingDecision, SimulationResult
from ariadne.simulation import (
    EnhancedSimulationResult,
    ErrorMitigation,
    OptimizationLevel,
    QuantumSimulator,
    SimulationOptions,
)


def _make_simulation_result(
    backend: BackendType, shots: int, metadata: dict[str, object] | None = None
) -> SimulationResult:
    routing_decision = RoutingDecision(
        circuit_entropy=0.0,
        recommended_backend=backend,
        confidence_score=0.9,
        expected_speedup=1.0,
        channel_capacity_match=1.0,
        alternatives=[],
    )
    result_metadata = {"shots": shots}
    if metadata:
        result_metadata.update(metadata)
    return SimulationResult(
        counts={"0": shots},
        backend_used=backend,
        execution_time=0.01,
        routing_decision=routing_decision,
        metadata=result_metadata,
    )


def test_execute_simulation_restores_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    simulator = QuantumSimulator()
    circuit = QuantumCircuit(1)
    options = SimulationOptions(
        backend_preference=["stim"],
        shots=7,
        budget_ms=250,
        precision="high",
    )

    prev_budget = os.environ.get("ARIADNE_ROUTING_BUDGET_MS")
    prev_ddsim = os.environ.get("ARIADNE_ROUTING_PREFER_DDSIM")

    os.environ["ARIADNE_ROUTING_BUDGET_MS"] = "original"
    os.environ["ARIADNE_ROUTING_PREFER_DDSIM"] = "0"

    def _fake_core_simulate(_circuit: QuantumCircuit, shots: int, backend: str | None = None) -> SimulationResult:
        assert os.environ["ARIADNE_ROUTING_BUDGET_MS"] == "250"
        assert os.environ["ARIADNE_ROUTING_PREFER_DDSIM"] == "1"
        return _make_simulation_result(BackendType.QISKIT, shots)

    monkeypatch.setattr("ariadne.simulation.core_simulate", _fake_core_simulate, raising=False)

    result = simulator._execute_simulation(circuit, options)

    assert result.metadata["shots"] == 7
    assert os.environ["ARIADNE_ROUTING_BUDGET_MS"] == "original"
    assert os.environ["ARIADNE_ROUTING_PREFER_DDSIM"] == "0"

    if prev_budget is None:
        os.environ.pop("ARIADNE_ROUTING_BUDGET_MS", None)
    else:
        os.environ["ARIADNE_ROUTING_BUDGET_MS"] = prev_budget

    if prev_ddsim is None:
        os.environ.pop("ARIADNE_ROUTING_PREFER_DDSIM", None)
    else:
        os.environ["ARIADNE_ROUTING_PREFER_DDSIM"] = prev_ddsim


def test_simulate_invokes_fallback_when_primary_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    simulator = QuantumSimulator()
    circuit = QuantumCircuit(1)
    options = SimulationOptions(shots=5)

    def _raise_error(
        _self: QuantumSimulator, _circuit: QuantumCircuit, _options: SimulationOptions
    ) -> SimulationResult:
        raise RuntimeError("primary failure")

    fallback_result = _make_simulation_result(BackendType.QISKIT, 5, metadata={"fallback": True})

    monkeypatch.setattr(QuantumSimulator, "_execute_simulation", _raise_error, raising=False)
    monkeypatch.setattr(QuantumSimulator, "_execute_fallback_simulation", lambda *_: fallback_result, raising=False)

    result = simulator.simulate(circuit, options)
    assert result.backend_used == BackendType.QISKIT.value
    assert result.backend_performance.get("fallback") is True


def test_execute_fallback_simulation_with_basic_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    simulator = QuantumSimulator()
    circuit = QuantumCircuit(1, 1)
    options = SimulationOptions(shots=3)

    class _DummyResult:
        def __init__(self, shots: int) -> None:
            self._shots = shots

        def get_counts(self) -> dict[str, int]:
            return {"0": self._shots}

    class _DummyJob:
        def __init__(self, shots: int) -> None:
            self._shots = shots

        def result(self) -> _DummyResult:
            return _DummyResult(self._shots)

    class _DummyBackend:
        def run(self, _circuit: QuantumCircuit, shots: int) -> _DummyJob:
            return _DummyJob(shots)

    class _DummyProvider:
        def get_backend(self, name: str) -> _DummyBackend:
            assert name == "basic_simulator"
            return _DummyBackend()

    monkeypatch.setattr("ariadne.simulation.BasicProvider", _DummyProvider, raising=False)

    circuit.h(0)
    circuit.measure(0, 0)

    result = simulator._execute_fallback_simulation(circuit, options)
    assert sum(result.counts.values()) == 3
    assert set(result.counts) <= {"0", "1"}
    assert result.metadata["fallback"]
    assert result.backend_used == BackendType.QISKIT


def test_enhanced_simulation_result_helpers() -> None:
    counts = {"0": 3, "1": 1}
    result = EnhancedSimulationResult(
        counts=counts,
        execution_time=0.05,
        backend_used="qiskit",
        circuit_analysis={},
        warnings=["note"],
    )

    expectation = result.get_expectation_value("Z")
    assert expectation == pytest.approx(0.5)

    probabilities = result.get_probability_distribution()
    assert probabilities["0"] == pytest.approx(0.75)
    assert probabilities["1"] == pytest.approx(0.25)

    as_dict = result.to_dict()
    assert as_dict["counts"] == counts
    assert as_dict["warnings"] == ["note"]


def test_simulate_batch_uses_shared_options(monkeypatch: pytest.MonkeyPatch) -> None:
    simulator = QuantumSimulator()
    circuits = [QuantumCircuit(1), QuantumCircuit(1)]
    options = SimulationOptions(shots=2)

    call_history: list[SimpleNamespace] = []

    def _fake_simulate(
        self: QuantumSimulator,
        circuit: QuantumCircuit,
        opts: SimulationOptions,
    ) -> EnhancedSimulationResult:
        call_history.append(SimpleNamespace(circuit=circuit, index=opts.backend_options.get("circuit_index")))
        return EnhancedSimulationResult(
            counts={"0": opts.shots},
            execution_time=0.0,
            backend_used="qiskit",
            circuit_analysis={},
        )

    monkeypatch.setattr(QuantumSimulator, "simulate", _fake_simulate, raising=False)

    simulator.simulate_batch(circuits, options)

    assert len(call_history) == 2
    assert [call.index for call in call_history] == [0, 1]


def test_optimize_circuit_returns_copy(monkeypatch: pytest.MonkeyPatch) -> None:
    simulator = QuantumSimulator()
    circuit = QuantumCircuit(1)

    optimized = simulator.optimize_circuit(circuit, level=OptimizationLevel.MEDIUM)
    assert optimized is not circuit

    # Ensures NONE level returns original circuit without modifications.
    no_opt = simulator.optimize_circuit(circuit, level=OptimizationLevel.NONE)
    assert no_opt is circuit


def test_resource_estimate_and_error_mitigation_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    simulator = QuantumSimulator()
    circuit = QuantumCircuit(1)

    options = SimulationOptions(
        shots=4,
        error_mitigation=ErrorMitigation.ZNE,
        analyze_quantum_advantage=False,
        estimate_resources=False,
    )

    monkeypatch.setattr(
        QuantumSimulator,
        "_execute_simulation",
        lambda *_: _make_simulation_result(BackendType.QISKIT, 4),
        raising=False,
    )

    result = simulator.simulate(circuit, options)
    assert result.counts["0"] == 4


def test_simulate_statevector_and_probabilities(monkeypatch: pytest.MonkeyPatch) -> None:
    simulator = QuantumSimulator()
    circuit = QuantumCircuit(1)
    circuit.h(0)

    options = SimulationOptions(
        shots=4,
        return_statevector=True,
        return_probabilities=True,
        analyze_quantum_advantage=False,
        estimate_resources=False,
    )

    monkeypatch.setattr(
        QuantumSimulator,
        "_execute_simulation",
        lambda *_: _make_simulation_result(BackendType.QISKIT, 4),
        raising=False,
    )
    monkeypatch.setattr(QuantumSimulator, "_get_statevector", lambda *_: np.array([1.0, 0.0]), raising=False)

    result = simulator.simulate(circuit, options)
    assert np.array_equal(result.statevector, np.array([1.0, 0.0]))
    assert np.isclose(result.probabilities.sum(), 1.0)


def test_get_performance_stats(monkeypatch: pytest.MonkeyPatch) -> None:
    simulator = QuantumSimulator()
    stats = simulator.get_performance_stats()
    assert stats["simulation_count"] == 0

    simulator.simulation_count = 2
    simulator.total_execution_time = 1.0
    simulator.backend_usage = {"qiskit": 2}

    stats = simulator.get_performance_stats()
    assert stats["average_execution_time"] == 0.5


def test_convenience_wrappers(monkeypatch: pytest.MonkeyPatch) -> None:
    result = EnhancedSimulationResult(
        counts={"0": 1},
        execution_time=0.0,
        backend_used="qiskit",
        circuit_analysis={},
    )

    def _stub_simulate(
        self: QuantumSimulator, circuit: QuantumCircuit, options: SimulationOptions
    ) -> EnhancedSimulationResult:
        return result

    monkeypatch.setattr(QuantumSimulator, "simulate", _stub_simulate, raising=False)

    qc = QuantumCircuit(1)
    qc.h(0)

    assert simulation.simulate(qc).counts == {"0": 1}
    assert simulation.simulate_with_analysis(qc).counts == {"0": 1}
