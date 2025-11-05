"""Tests for the heuristic performance model and predictors."""

from __future__ import annotations

import math

import pytest
from qiskit import QuantumCircuit

from ariadne.route.performance_model import (
    CircuitFeatureExtractor,
    PerformanceModel,
    PerformancePredictor,
    find_optimal_backend,
    predict_circuit_performance,
)
from ariadne.types import BackendType


def _make_clifford_bell_pair() -> QuantumCircuit:
    circuit = QuantumCircuit(2)
    circuit.h(0)
    circuit.cx(0, 1)
    return circuit


def _make_non_clifford_trotter() -> QuantumCircuit:
    circuit = QuantumCircuit(2)
    circuit.h(0)
    circuit.t(0)
    circuit.cx(0, 1)
    circuit.t(1)
    circuit.rx(math.pi / 4, 0)
    circuit.cz(0, 1)
    return circuit


def test_feature_extractor_basic_metrics() -> None:
    extractor = CircuitFeatureExtractor()
    circuit = _make_non_clifford_trotter()
    features = extractor.extract_features(circuit)

    assert features.num_qubits == 2
    assert features.depth > 0
    assert features.gate_count == features.single_qubit_gate_count + features.two_qubit_gate_count
    assert 0.0 <= features.gate_entropy <= math.log2(features.gate_count or 1)
    assert 0.0 <= features.clifford_ratio <= 1.0
    assert features.entanglement_complexity >= 0.0


def test_performance_model_prefers_stim_for_clifford_circuits() -> None:
    circuit = _make_clifford_bell_pair()
    features = CircuitFeatureExtractor().extract_features(circuit)
    model = PerformanceModel()

    stim_time = model.predict_execution_time(features, BackendType.STIM)
    qiskit_time = model.predict_execution_time(features, BackendType.QISKIT)

    assert stim_time < qiskit_time
    assert model.predict_memory_usage(features, BackendType.STIM) <= model.predict_memory_usage(
        features, BackendType.QISKIT
    )


def test_performance_predictor_returns_consistent_predictions() -> None:
    circuit = _make_non_clifford_trotter()
    predictor = PerformancePredictor()

    stim_prediction = predictor.predict_performance(circuit, BackendType.STIM)
    cuda_prediction = predictor.predict_performance(circuit, BackendType.CUDA)

    assert stim_prediction.backend == BackendType.STIM
    assert cuda_prediction.backend == BackendType.CUDA
    assert stim_prediction.predicted_time != cuda_prediction.predicted_time
    assert stim_prediction.feature_importance["num_qubits"] == pytest.approx(0.4, rel=0.0, abs=1e-9)


def test_find_optimal_backend_chooses_fastest_option() -> None:
    circuit = _make_non_clifford_trotter()
    available_backends = [BackendType.STIM, BackendType.QISKIT, BackendType.CUDA]
    best_backend, prediction = find_optimal_backend(circuit, available_backends, optimize_for="time")

    assert best_backend in available_backends
    assert prediction.backend == best_backend
    assert prediction.predicted_time > 0


def test_predict_circuit_performance_faces_no_op_record() -> None:
    circuit = _make_clifford_bell_pair()

    # Ensure the warning path in record_actual_performance is exercised without polluting test output
    predictor = PerformancePredictor()
    with pytest.warns(UserWarning):
        predictor.record_actual_performance(circuit, BackendType.QISKIT, execution_time=0.01)

    # Convenience wrappers should still be usable after record operation
    result = predict_circuit_performance(circuit, BackendType.QISKIT)
    assert result.backend == BackendType.QISKIT
    assert result.predicted_memory_mb >= 1.0
