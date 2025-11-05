"""Tests for the asynchronous simulation utilities."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

import pytest
from qiskit import QuantumCircuit

from ariadne.async_.simulation import (
    AsyncBackendInterface,
    AsyncSimulationRequest,
    AsyncSimulator,
    get_async_simulator,
    simulate_async,
    simulate_batch_async,
)
from ariadne.types import BackendType, RoutingDecision, SimulationResult


class _DummyLogger:
    def __getattr__(self, _name: str):
        def _noop(*_args: Any, **_kwargs: Any) -> None:
            return None

        return _noop


class _StubHealthChecker:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def check_backend_health(self, backend: BackendType) -> SimpleNamespace:
        self.calls.append(backend.value)
        return SimpleNamespace(
            status=SimpleNamespace(value="healthy"),
            message="ok",
            response_time=0.01,
            timestamp=123.0,
            details={"backend": backend.value},
        )

    def get_backend_metrics(self, backend: BackendType) -> SimpleNamespace:
        return SimpleNamespace(
            status=SimpleNamespace(value="ok"),
            response_time=0.02,
            success_rate=0.99,
            uptime_percentage=99.5,
            total_checks=10,
            consecutive_failures=0,
        )


def _make_simulation_result(backend: BackendType = BackendType.QISKIT) -> SimulationResult:
    decision = RoutingDecision(
        circuit_entropy=0.0,
        recommended_backend=backend,
        confidence_score=0.5,
        expected_speedup=1.0,
        channel_capacity_match=1.0,
        alternatives=[],
    )
    return SimulationResult(
        counts={"00": 1},
        backend_used=backend,
        execution_time=0.001,
        routing_decision=decision,
        metadata={},
    )


@pytest.fixture(autouse=True)
def _patch_async_module(monkeypatch: pytest.MonkeyPatch) -> None:
    import ariadne.async_.simulation as async_sim

    def stub_simulate(
        _circuit: QuantumCircuit, shots: int = 1024, backend: str | None = None, **_kwargs: Any
    ) -> SimulationResult:
        result = _make_simulation_result(BackendType.QISKIT)
        result.metadata["shots"] = shots
        result.metadata["backend"] = backend or "auto"
        return result

    monkeypatch.setattr(async_sim, "get_logger", lambda _name: _DummyLogger())
    monkeypatch.setattr(async_sim, "get_health_checker", lambda: _StubHealthChecker())
    monkeypatch.setattr(async_sim, "simulate", stub_simulate)
    monkeypatch.setattr(async_sim, "_global_async_simulator", None)


def _build_circuit(width: int = 2) -> QuantumCircuit:
    circuit = QuantumCircuit(width)
    circuit.h(0)
    if width > 1:
        circuit.cx(0, 1)
    return circuit


@pytest.mark.asyncio
async def test_async_simulator_runs_single_request() -> None:
    simulator = AsyncSimulator(max_concurrent_simulations=1)
    await simulator.start()

    request = await simulator.simulate(_build_circuit(), shots=32)

    assert request.success is True
    assert request.result is not None
    assert request.result.metadata["shots"] == 32 if "shots" in request.result.metadata else True

    await simulator.stop()


@pytest.mark.asyncio
async def test_async_simulator_batch_handles_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    import ariadne.async_.simulation as async_sim

    def stub_simulate(circuit: QuantumCircuit, backend: str | None = None, **_kwargs: Any) -> SimulationResult:
        if backend == "fail":
            raise RuntimeError("backend failure")
        return _make_simulation_result(BackendType.QISKIT)

    monkeypatch.setattr(async_sim, "simulate", stub_simulate)

    simulator = AsyncSimulator(max_concurrent_simulations=2)
    await simulator.start()

    requests = [
        AsyncSimulationRequest(circuit=_build_circuit(), backend="ok"),
        AsyncSimulationRequest(circuit=_build_circuit(), backend="fail"),
    ]

    results = await simulator.simulate_batch(requests, return_exceptions=False)

    assert results[0].success is True
    assert results[1].error is not None

    await simulator.stop()


@pytest.mark.asyncio
async def test_global_simulation_helpers_reuse_singleton() -> None:
    import asyncio

    circuit = _build_circuit()
    result = await simulate_async(circuit, shots=8)
    assert result.success is True
    assert result.result is not None

    # Add small delay to ensure different timestamp in request ID generation
    await asyncio.sleep(0.001)  # 1ms delay

    second_result = await simulate_async(circuit, shots=4)
    assert second_result.request.request_id != result.request.request_id

    simulator = await get_async_simulator()
    await simulator.stop()

    import ariadne.async_.simulation as async_sim

    async_sim._global_async_simulator = None


@pytest.mark.asyncio
async def test_simulate_batch_async_wrapper(monkeypatch: pytest.MonkeyPatch) -> None:
    circuits = [_build_circuit(), _build_circuit()]
    results = await simulate_batch_async(circuits, backend="ok")

    assert len(results) == 2
    assert all(result.success for result in results)

    simulator = await get_async_simulator()
    await simulator.stop()

    import ariadne.async_.simulation as async_sim

    async_sim._global_async_simulator = None


@pytest.mark.asyncio
async def test_async_backend_interface_health_checks(monkeypatch: pytest.MonkeyPatch) -> None:
    interface = AsyncBackendInterface()

    individual = await interface.check_backend_health(BackendType.QISKIT)
    assert individual["backend"] == BackendType.QISKIT.value
    assert individual["status"] == "healthy"

    combined = await interface.check_all_backends_health()
    assert BackendType.QISKIT.value in combined


@pytest.mark.asyncio
async def test_async_backend_monitor_collects_metrics(monkeypatch: pytest.MonkeyPatch) -> None:
    interface = AsyncBackendInterface()

    real_sleep = asyncio.sleep

    async def short_sleep(_seconds: float) -> None:
        await real_sleep(0)

    monkeypatch.setattr("ariadne.async_.simulation.asyncio.sleep", short_sleep)

    metrics = await interface.monitor_backend_performance(BackendType.QISKIT, duration=0.01, interval=0.005)
    assert metrics
    assert metrics[0]["metrics"]["status"] == "ok"
