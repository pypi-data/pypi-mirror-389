"""Tests for the benchmarking utilities."""

from __future__ import annotations

import pytest
from qiskit import QuantumCircuit

from ariadne.algorithms import AlgorithmParameters
from ariadne.benchmarking import export_benchmark_report
from ariadne.types import BackendType, RoutingDecision, SimulationResult


def _make_result(backend: BackendType) -> SimulationResult:
    decision = RoutingDecision(
        circuit_entropy=0.0,
        recommended_backend=backend,
        confidence_score=1.0,
        expected_speedup=1.0,
        channel_capacity_match=1.0,
        alternatives=[],
    )
    return SimulationResult(
        counts={"00": 1}, backend_used=backend, execution_time=0.01, routing_decision=decision, metadata={}
    )


@pytest.fixture(autouse=True)
def stub_benchmark_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    import ariadne.benchmarking as benchmarking

    class DummyAlgorithm:
        def __init__(self, params: AlgorithmParameters):
            self.params = params

        def create_circuit(self) -> QuantumCircuit:
            circuit = QuantumCircuit(self.params.n_qubits)
            if self.params.n_qubits > 0:
                circuit.h(0)
            circuit.measure_all()
            return circuit

    def fake_get_algorithm(_name: str) -> type[DummyAlgorithm]:
        return DummyAlgorithm

    def fake_simulate(circuit: QuantumCircuit, shots: int = 1024, backend: str | None = None) -> SimulationResult:
        backend_type = (
            BackendType.QISKIT
            if backend is None
            else BackendType(backend)
            if backend in BackendType._value2member_map_
            else BackendType.QISKIT
        )
        result = _make_result(backend_type)
        result.metadata["shots"] = shots
        return result

    monkeypatch.setattr(benchmarking, "get_algorithm", fake_get_algorithm)
    monkeypatch.setattr(benchmarking, "simulate", fake_simulate)


def test_export_benchmark_report_json() -> None:
    report = export_benchmark_report(["bell", "qaoa"], ["qiskit"], shots=16, fmt="json")

    assert "results" in report
    assert set(report["results"].keys()) == {"bell", "qaoa"}
    assert report["results"]["bell"]["backends"]["qiskit"]["success"] is True


def test_export_benchmark_report_invalid_format() -> None:
    with pytest.raises(ValueError):
        export_benchmark_report(["bell"], ["qiskit"], fmt="xml")


def test_export_benchmark_report_csv_and_latex() -> None:
    csv_report = export_benchmark_report(["bell"], ["qiskit", "stim"], fmt="csv")
    assert csv_report["format"] == "csv"
    assert csv_report["data"]

    latex_report = export_benchmark_report(["bell"], ["qiskit"], fmt="latex")
    assert "\\section*" in latex_report["content"]
