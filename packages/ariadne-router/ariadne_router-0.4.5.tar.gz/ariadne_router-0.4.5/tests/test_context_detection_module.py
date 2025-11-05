from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from qiskit import QuantumCircuit

from ariadne.route.context_detection import (
    CircuitFamilyDetector,
    CircuitPattern,
    ContextDetector,
    HardwareProfile,
    HardwareProfiler,
    UsagePattern,
    WorkflowDetector,
)
from ariadne.route.enhanced_router import PerformancePreferences, WorkflowType
from ariadne.router import BackendType


def test_circuit_family_detector_identifies_variational_family() -> None:
    circuit = QuantumCircuit(2)
    circuit.ry(0.1, 0)
    circuit.cx(0, 1)
    circuit.rz(0.2, 1)
    circuit.cx(1, 0)

    detector = CircuitFamilyDetector()
    families = detector.detect_circuit_family(circuit)
    assert "optimization" in families


def test_workflow_detector_classifies_education_pattern() -> None:
    workflow_detector = WorkflowDetector()
    pattern = CircuitPattern(
        avg_qubits=4,
        avg_depth=8,
        clifford_ratio=0.5,
        common_gates=["h", "cx"],
        entanglement_complexity=0.2,
        circuit_families=["basic_algorithms"],
    )
    usage = UsagePattern(
        session_count=8,
        total_circuits=12,
        preferred_shot_counts=[512, 1024],
        time_of_day_preferences=[9],
        backend_success_rates={"qiskit": 0.95},
        average_session_length=25.0,
    )

    workflow = workflow_detector.detect_workflow_type([pattern], usage)
    assert workflow == WorkflowType.EDUCATION


def test_context_detector_analyze_user_context(tmp_path: Path) -> None:
    cache_path = tmp_path / "context_cache.json"
    detector = ContextDetector(cache_file=str(cache_path))

    profile = HardwareProfile(
        cpu_cores=8,
        total_memory_gb=32.0,
        gpu_available=True,
        apple_silicon=False,
        cuda_capable=True,
        platform_name="Linux",
        rocm_capable=False,
        oneapi_capable=False,
        opencl_available=False,
    )

    detector.hardware_profiler = SimpleNamespace(detect_hardware_profile=lambda: profile)

    circuits = []
    for _ in range(3):
        qc = QuantumCircuit(3)
        qc.h(0)
        qc.cx(0, 1)
        qc.cx(1, 2)
        circuits.append(qc)

    backend_usage = {BackendType.QISKIT: 5, BackendType.CUDA: 2}
    execution_times = {BackendType.QISKIT: [0.1, 0.2], BackendType.CUDA: [0.05]}

    context = detector.analyze_user_context(circuits, backend_usage=backend_usage, execution_times=execution_times)

    assert context.hardware_profile.cpu_cores == 8
    assert context.preferred_backends[0] == BackendType.QISKIT
    assert isinstance(context.performance_preferences, PerformancePreferences)

    assert cache_path.exists()
    with open(cache_path) as cache_file:
        data = json.load(cache_file)
        assert "context" in data
        workflow_entry = data["context"]["workflow_type"]
        valid_values = {wt.value for wt in WorkflowType} | {str(wt) for wt in WorkflowType}
        assert workflow_entry in valid_values


def test_update_performance_history_keeps_recent_entries(tmp_path: Path) -> None:
    detector = ContextDetector(cache_file=str(tmp_path / "cache.json"))
    backend = BackendType.QISKIT

    for idx in range(105):
        detector.update_performance_history(backend, execution_time=float(idx))

    history = detector.performance_history.backend_performance[backend]
    assert len(history) == 100
    assert history[0] == 5.0


def test_analyze_circuit_patterns_produces_family_statistics(tmp_path: Path) -> None:
    detector = ContextDetector(cache_file=str(tmp_path / "tmp_context.json"))
    circuits = []
    for _ in range(3):
        qc = QuantumCircuit(4)
        qc.h(range(4))
        qc.cx(0, 1)
        qc.cx(1, 2)
        qc.cz(2, 3)
        circuits.append(qc)

    patterns = detector._analyze_circuit_patterns(circuits)
    assert patterns
    pattern = patterns[0]
    assert pattern.avg_qubits == pytest.approx(4)
    assert pattern.common_gates
    assert pattern.entanglement_complexity > 0


def test_determine_preferred_backends_returns_top_three(tmp_path: Path) -> None:
    usage = {
        BackendType.CUDA: 10,
        BackendType.QISKIT: 5,
        BackendType.TENSOR_NETWORK: 3,
        BackendType.MPS: 1,
    }
    detector = ContextDetector(cache_file=str(tmp_path / "cache.json"))
    preferred = detector._determine_preferred_backends(usage)
    assert preferred == [BackendType.CUDA, BackendType.QISKIT, BackendType.TENSOR_NETWORK]


def test_hardware_profiler_detection(monkeypatch: pytest.MonkeyPatch) -> None:
    profiler = HardwareProfiler()
    monkeypatch.setattr(HardwareProfiler, "_detect_cpu_cores", lambda self: 16, raising=False)
    monkeypatch.setattr(HardwareProfiler, "_detect_memory_gb", lambda self: 64.0, raising=False)
    monkeypatch.setattr(HardwareProfiler, "_detect_gpu_available", lambda self: True, raising=False)
    monkeypatch.setattr(HardwareProfiler, "_detect_apple_silicon", lambda self: False, raising=False)
    monkeypatch.setattr(HardwareProfiler, "_detect_cuda_capable", lambda self: True, raising=False)
    monkeypatch.setattr(HardwareProfiler, "_detect_rocm_capable", lambda self: True, raising=False)
    monkeypatch.setattr(HardwareProfiler, "_detect_oneapi_capable", lambda self: False, raising=False)
    monkeypatch.setattr(HardwareProfiler, "_detect_opencl_available", lambda self: True, raising=False)

    profile = profiler.detect_hardware_profile()
    assert profile.cpu_cores == 16
    assert profile.total_memory_gb == 64.0
    assert profile.gpu_available is True
    assert profile.rocm_capable is True
