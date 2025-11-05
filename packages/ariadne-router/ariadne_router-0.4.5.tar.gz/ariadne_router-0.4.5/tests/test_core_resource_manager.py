from __future__ import annotations

from types import SimpleNamespace

import pytest
from qiskit import QuantumCircuit

from ariadne.core import resource_manager
from ariadne.core.resource_manager import (
    ResourceRequirements,
    SystemResources,
    check_circuit_feasibility,
)

pytest.importorskip("psutil")


@pytest.fixture
def fresh_manager(monkeypatch: pytest.MonkeyPatch) -> resource_manager.ResourceManager:
    monkeypatch.setattr(resource_manager.ResourceManager, "_instance", None, raising=False)
    monkeypatch.setattr(resource_manager, "_global_resource_manager", None, raising=False)

    def _virtual_memory() -> SimpleNamespace:
        total = 16 * 1024 * 1024 * 1024
        available = 12 * 1024 * 1024 * 1024
        return SimpleNamespace(total=total, available=available)

    monkeypatch.setattr(resource_manager.psutil, "virtual_memory", _virtual_memory, raising=False)
    monkeypatch.setattr(resource_manager.psutil, "cpu_count", lambda: 8, raising=False)
    monkeypatch.setattr(resource_manager.ResourceManager, "_get_gpu_info", lambda self: (2048.0, True), raising=False)

    manager = resource_manager.ResourceManager()
    manager.resources = SystemResources(
        available_memory_mb=12 * 1024,
        total_memory_mb=16 * 1024,
        available_cpu_cores=8,
        total_cpu_cores=8,
        gpu_memory_mb=2048.0,
        gpu_available=True,
        platform="Linux",
        architecture="x86_64",
    )
    manager._last_update = 0.0
    manager._update_interval = 60.0  # Prevent automatic refresh during tests
    return manager


def test_small_circuit_bypasses_checks(fresh_manager: resource_manager.ResourceManager) -> None:
    circuit = QuantumCircuit(2)
    circuit.h(0)
    can_handle, reason = fresh_manager.can_handle_circuit(circuit, backend="qiskit")
    assert can_handle
    assert reason == "Small circuit, resource checks bypassed"


def test_memory_shortage_detected(
    monkeypatch: pytest.MonkeyPatch, fresh_manager: resource_manager.ResourceManager
) -> None:
    def _high_memory(
        self: resource_manager.ResourceManager,
        circuit: QuantumCircuit,
        backend: str,
    ) -> ResourceRequirements:
        return ResourceRequirements(
            memory_mb=fresh_manager.resources.available_memory_mb * 2,
            cpu_cores=1,
            estimated_time_seconds=0.1,
            backend=backend,
        )

    monkeypatch.setattr(resource_manager.ResourceManager, "estimate_circuit_requirements", _high_memory, raising=False)

    circuit = QuantumCircuit(6)
    circuit.cx(0, 1)
    circuit.cx(1, 2)
    circuit.cx(2, 3)

    can_handle, reason = fresh_manager.can_handle_circuit(circuit, backend="qiskit")
    assert not can_handle
    assert "Insufficient memory" in reason


def test_cpu_soft_constraint_allows_execution(
    monkeypatch: pytest.MonkeyPatch, fresh_manager: resource_manager.ResourceManager
) -> None:
    fresh_manager.resources.available_cpu_cores = 1

    def _high_cpu(
        self: resource_manager.ResourceManager,
        circuit: QuantumCircuit,
        backend: str,
    ) -> ResourceRequirements:
        return ResourceRequirements(
            memory_mb=10.0,
            cpu_cores=4,
            estimated_time_seconds=0.1,
            backend=backend,
        )

    monkeypatch.setattr(resource_manager.ResourceManager, "estimate_circuit_requirements", _high_cpu, raising=False)

    circuit = QuantumCircuit(12)
    for qubit in range(12):
        circuit.h(qubit)
    circuit.cz(0, 1)
    circuit.cz(2, 3)

    fresh_manager._last_update = resource_manager.time.time()
    can_handle, reason = fresh_manager.can_handle_circuit(circuit, backend="qiskit")
    assert can_handle
    assert "CPU contention detected" in reason


def test_reserve_and_release_resources(
    monkeypatch: pytest.MonkeyPatch, fresh_manager: resource_manager.ResourceManager
) -> None:
    def _requirements(
        self: resource_manager.ResourceManager,
        circuit: QuantumCircuit,
        backend: str,
    ) -> ResourceRequirements:
        return ResourceRequirements(
            memory_mb=64.0,
            cpu_cores=2,
            estimated_time_seconds=0.1,
            backend=backend,
        )

    monkeypatch.setattr(resource_manager.ResourceManager, "estimate_circuit_requirements", _requirements, raising=False)

    circuit = QuantumCircuit(7)
    circuit.x(0)
    circuit.cx(0, 1)

    before_memory = fresh_manager.resources.available_memory_mb
    before_cores = fresh_manager.resources.available_cpu_cores

    requirements = fresh_manager.reserve_resources(circuit, backend="qiskit")
    assert fresh_manager.resources.available_memory_mb == before_memory - 64.0
    assert fresh_manager.resources.available_cpu_cores == before_cores - 2

    fresh_manager.release_resources(requirements)
    assert fresh_manager.resources.available_memory_mb == before_memory
    assert fresh_manager.resources.available_cpu_cores == before_cores


def test_get_recommendations_flags_large_circuit(fresh_manager: resource_manager.ResourceManager) -> None:
    fresh_manager.resources.available_memory_mb = fresh_manager.resources.total_memory_mb * 0.15
    fresh_manager.resources.available_cpu_cores = 1

    circuit = QuantumCircuit(28)
    for _ in range(120):
        circuit.cx(0, 1)

    recommendations = fresh_manager.get_recommendations(circuit)
    assert any("tensor network" in rec for rec in recommendations)
    assert any("memory usage is high" in rec for rec in recommendations)


def test_check_circuit_feasibility_uses_global_manager(
    monkeypatch: pytest.MonkeyPatch, fresh_manager: resource_manager.ResourceManager
) -> None:
    monkeypatch.setattr(resource_manager, "_global_resource_manager", fresh_manager, raising=False)
    circuit = QuantumCircuit(2)
    feasible, _ = check_circuit_feasibility(circuit, backend="stim")
    assert feasible


def test_memory_usage_percent_property() -> None:
    resources = SystemResources(
        available_memory_mb=2048,
        total_memory_mb=4096,
        available_cpu_cores=4,
        total_cpu_cores=8,
        gpu_memory_mb=None,
        gpu_available=False,
        platform="Linux",
        architecture="x86_64",
    )
    assert resources.memory_usage_percent == pytest.approx(50.0)


def test_estimate_circuit_requirements_variants(
    monkeypatch: pytest.MonkeyPatch, fresh_manager: resource_manager.ResourceManager
) -> None:
    circuit = QuantumCircuit(5)
    for qubit in range(5):
        circuit.h(qubit)

    stim_requirements = fresh_manager.estimate_circuit_requirements(circuit, backend="stim")
    assert stim_requirements.memory_mb > 0

    tensor_requirements = fresh_manager.estimate_circuit_requirements(circuit, backend="tensor_network")
    assert tensor_requirements.memory_mb <= stim_requirements.memory_mb

    cuda_requirements = fresh_manager.estimate_circuit_requirements(circuit, backend="cuda")
    assert cuda_requirements.estimated_time_seconds > 0


def test_get_resource_manager_returns_singleton(
    monkeypatch: pytest.MonkeyPatch, fresh_manager: resource_manager.ResourceManager
) -> None:
    monkeypatch.setattr(resource_manager, "_global_resource_manager", fresh_manager, raising=False)
    assert resource_manager.get_resource_manager() is fresh_manager
