from __future__ import annotations

import sys
from collections.abc import Callable
from types import SimpleNamespace

import numpy as np
import pytest
from qiskit import QuantumCircuit

import ariadne.router as router
from ariadne.types import BackendType, RoutingDecision


class _StubBackend:
    def __init__(self, result_factory: Callable[[int], dict[str, int]] | None = None) -> None:
        self._result_factory = result_factory or (lambda shots: {"0": shots})

    def simulate(self, _circuit: QuantumCircuit, shots: int) -> dict[str, int]:
        return self._result_factory(shots)


@pytest.mark.parametrize(
    ("func_name", "module_path", "attribute"),
    [
        ("_simulate_mps", "ariadne.backends.mps_backend", "MPSBackend"),
        ("_simulate_cirq", "ariadne.backends.cirq_backend", "CirqBackend"),
        ("_simulate_pennylane", "ariadne.backends.pennylane_backend", "PennyLaneBackend"),
        ("_simulate_qulacs", "ariadne.backends.qulacs_backend", "QulacsBackend"),
        ("_simulate_pyquil", "ariadne.backends.experimental.pyquil_backend", "PyQuilBackend"),
        ("_simulate_braket", "ariadne.backends.experimental.braket_backend", "BraketBackend"),
        ("_simulate_aws_braket", "ariadne.backends.braket_backend", "AWSBraketBackend"),
        ("_simulate_azure_quantum", "ariadne.backends.azure_backend", "AzureQuantumBackend"),
        ("_simulate_qsharp", "ariadne.backends.experimental.qsharp_backend", "QSharpBackend"),
        ("_simulate_opencl", "ariadne.backends.experimental.opencl_backend", "OpenCLBackend"),
    ],
)
def test_optional_backends_success(
    monkeypatch: pytest.MonkeyPatch, func_name: str, module_path: str, attribute: str
) -> None:
    dummy_module = SimpleNamespace(**{attribute: _StubBackend})
    monkeypatch.setitem(sys.modules, module_path, dummy_module)

    circuit = QuantumCircuit(1)
    circuit.h(0)
    circuit.measure_all()

    simulate_fn = getattr(router, func_name)
    counts = simulate_fn(circuit, shots=5)
    assert counts == {"0": 5}


def test_tensor_network_wrapper_uses_cached_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[int] = []

    def _fake_sim(circuit: QuantumCircuit, shots: int) -> dict[str, int]:
        calls.append(shots)
        return {"1": shots}

    monkeypatch.setattr(router, "_real_tensor_network_simulation", _fake_sim)

    circuit = QuantumCircuit(1)
    circuit.measure_all()

    first = router._simulate_tensor_network(circuit, shots=3)
    second = router._simulate_tensor_network(circuit, shots=2)
    assert first == {"1": 3}
    assert second == {"1": 2}
    assert calls == [3, 2]


def test_cuda_warning_when_not_available(monkeypatch: pytest.MonkeyPatch) -> None:
    routing_decision = RoutingDecision(
        circuit_entropy=0.0,
        recommended_backend=BackendType.CUDA,
        confidence_score=0.9,
        expected_speedup=1.0,
        channel_capacity_match=1.0,
        alternatives=[],
    )
    dummy_cfg = SimpleNamespace(analysis=SimpleNamespace(enable_resource_estimation=False))
    monkeypatch.setattr("ariadne.router.get_config", lambda: dummy_cfg)
    monkeypatch.setattr("ariadne.router.get_resource_manager", lambda: SimpleNamespace())
    monkeypatch.setattr(router, "is_cuda_available", lambda: False)
    monkeypatch.setattr(router, "_simulate_cuda", lambda _circuit, shots: {"0": shots})
    monkeypatch.setattr("ariadne.route.routing_tree.explain_routing", lambda _c: "explain", raising=False)

    circuit = QuantumCircuit(1)
    circuit.measure_all()

    result = router._execute_simulation(circuit, shots=4, routing_decision=routing_decision)
    assert result.backend_used == BackendType.CUDA
    assert result.warnings == ["CUDA backend selected but CUDA not available"]


def test_apple_silicon_boost(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("platform.system", lambda: "Darwin")
    monkeypatch.setattr("platform.machine", lambda: "arm64")
    assert router._apple_silicon_boost() == pytest.approx(1.5)

    monkeypatch.setattr("platform.system", lambda: "Linux")
    assert router._apple_silicon_boost() == pytest.approx(1.0)


def test_ddsim_wrapper(monkeypatch: pytest.MonkeyPatch) -> None:
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
            assert name == "qasm_simulator"
            return _DummyBackend()

    dummy_module = SimpleNamespace(DDSIMProvider=lambda: _DummyProvider())
    monkeypatch.setitem(sys.modules, "mqt.ddsim", dummy_module)

    circuit = QuantumCircuit(1)
    circuit.measure_all()

    counts = router._simulate_ddsim(circuit, shots=7)
    assert counts == {"0": 7}


def test_sample_statevector_counts_with_mock_state(monkeypatch: pytest.MonkeyPatch) -> None:
    class _MockState:
        def __init__(self) -> None:
            self.data = np.array([np.sqrt(0.5), np.sqrt(0.5)])

    monkeypatch.setattr(router, "Statevector", SimpleNamespace(from_instruction=lambda _c: _MockState()))

    circuit = QuantumCircuit(1)
    circuit.h(0)

    counts = router._sample_statevector_counts(circuit, shots=8, seed=42)
    assert sum(counts.values()) == 8
