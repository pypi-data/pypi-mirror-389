"""Tests for the advanced performance prediction planner."""

from __future__ import annotations

import pytest
from qiskit import QuantumCircuit

from ariadne.route.performance_prediction import PerformancePredictor
from ariadne.types import BackendType


def _make_mixed_circuit() -> QuantumCircuit:
    circuit = QuantumCircuit(3)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.t(1)
    circuit.cx(1, 2)
    circuit.s(2)
    circuit.t(0)
    return circuit


def _make_deep_circuit() -> QuantumCircuit:
    circuit = QuantumCircuit(3)
    for _ in range(60):
        circuit.h(0)
        circuit.cx(0, 1)
        circuit.cx(1, 2)
    return circuit


def _make_wide_circuit(qubits: int = 24) -> QuantumCircuit:
    circuit = QuantumCircuit(qubits)
    for index in range(qubits - 1):
        circuit.cx(index, index + 1)
    return circuit


def _make_clifford_chain() -> QuantumCircuit:
    circuit = QuantumCircuit(3)
    for _ in range(10):
        circuit.h(0)
        circuit.cx(0, 1)
        circuit.cx(1, 2)
    return circuit


def _make_partition_friendly_wide_circuit(qubits: int = 24) -> QuantumCircuit:
    circuit = QuantumCircuit(qubits)
    mid = qubits // 2
    for index in range(mid - 1):
        circuit.cx(index, index + 1)
    for index in range(mid, qubits - 1):
        circuit.cx(index, index + 1)
    return circuit


def _make_mutable_circuit(source: QuantumCircuit) -> QuantumCircuit:
    """Clone circuit with mutable instructions that expose ``operation`` attribute like heuristics expect."""

    clone = QuantumCircuit(source.num_qubits)
    for instruction, qubits, clbits in source.data:
        mutable = instruction.to_mutable() if hasattr(instruction, "to_mutable") else instruction
        if not hasattr(mutable, "operation"):
            mutable.operation = mutable  # type: ignore[attr-defined]
        clone.append(mutable, qubits, clbits)
    return clone


@pytest.fixture()
def planner() -> PerformancePredictor:
    return PerformancePredictor()


def test_memory_score_prefers_memory_efficient_backends(planner: PerformancePredictor) -> None:
    small = QuantumCircuit(3)
    large = _make_wide_circuit(25)

    tensor_score_small = planner.calculate_memory_score(small, BackendType.TENSOR_NETWORK)
    tensor_score_large = planner.calculate_memory_score(large, BackendType.TENSOR_NETWORK)

    assert 0.0 <= tensor_score_small <= 1.0
    assert 0.0 <= tensor_score_large <= 1.0
    assert tensor_score_large <= tensor_score_small


def test_gate_complexity_scores_reward_clifford_backends(planner: PerformancePredictor) -> None:
    circuit = _make_clifford_chain()

    stim_score = planner.calculate_gate_complexity_score(circuit, BackendType.STIM)
    qiskit_score = planner.calculate_gate_complexity_score(circuit, BackendType.QISKIT)

    assert stim_score > qiskit_score


def test_cost_score_penalizes_cloud_backends(planner: PerformancePredictor) -> None:
    circuit = _make_mixed_circuit()

    local_cost = planner.calculate_cost_score(circuit, BackendType.QISKIT)
    cloud_cost = planner.calculate_cost_score(circuit, BackendType.AWS_BRAKET, shots=2000)

    assert local_cost == 1.0
    assert 0.0 < cloud_cost < 1.0


def test_speed_score_accounts_for_parallelization(planner: PerformancePredictor) -> None:
    circuit = _make_mixed_circuit()

    # Parallelizable backend should score at least as high as general backend
    tensor_speed = planner.calculate_speed_score(circuit, BackendType.TENSOR_NETWORK)
    qiskit_speed = planner.calculate_speed_score(circuit, BackendType.QISKIT)

    assert tensor_speed >= qiskit_speed


def test_predict_backend_performance_respects_capabilities(planner: PerformancePredictor) -> None:
    large_circuit = _make_wide_circuit(40)
    limited_backend_scores = planner.predict_backend_performance(large_circuit, BackendType.QISKIT)

    assert limited_backend_scores.total_score == 0.0
    assert limited_backend_scores.confidence == 0.0


def test_should_use_hybrid_execution_for_complex_circuits(planner: PerformancePredictor) -> None:
    assert planner.should_use_hybrid_execution(_make_deep_circuit()) is True
    assert planner.should_use_hybrid_execution(_make_wide_circuit(30)) is True
    assert planner.should_use_hybrid_execution(QuantumCircuit(2)) is False


def test_create_hybrid_execution_plan_for_mixed_circuit(planner: PerformancePredictor) -> None:
    circuit = _make_mutable_circuit(_make_mixed_circuit())
    plan = planner.create_hybrid_execution_plan(circuit)

    assert plan.segments
    assert len(plan.segments) == 2
    assert plan.expected_speedup >= 1.0


def test_create_hybrid_execution_plan_depth_partition(planner: PerformancePredictor) -> None:
    circuit = _make_mutable_circuit(_make_deep_circuit())
    plan = planner.create_hybrid_execution_plan(circuit)

    # Deep circuits should trigger depth partitioning, yielding multiple segments
    assert len(plan.segments) > 1
    assert plan.cost_estimate >= 0.0


def test_create_hybrid_execution_plan_qubit_partition(planner: PerformancePredictor) -> None:
    circuit = _make_mutable_circuit(_make_partition_friendly_wide_circuit(32))
    plan = planner.create_hybrid_execution_plan(circuit)

    assert plan.segments
    # The simple qubit-based split should result in two segments when threshold exceeded
    assert len(plan.segments) >= 2


def test_partition_helpers_generate_valid_segments(planner: PerformancePredictor) -> None:
    circuit = _make_mutable_circuit(_make_mixed_circuit())
    clifford, non_clifford = planner._partition_by_clifford_regions(circuit)

    assert clifford is not None
    assert non_clifford is not None
    assert clifford.num_qubits == circuit.num_qubits

    deep_circuit = _make_mutable_circuit(_make_deep_circuit())
    depth_segments = planner._partition_by_depth(deep_circuit, max_depth=10)
    assert len(depth_segments) > 1
    assert all(seg.num_qubits == deep_circuit.num_qubits for seg in depth_segments)

    wide_circuit = _make_mutable_circuit(_make_partition_friendly_wide_circuit(20))
    qubit_segments = planner._partition_by_qubits(wide_circuit, max_qubits=5)
    assert len(qubit_segments) == 2
