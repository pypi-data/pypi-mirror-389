"""Lightweight performance regression tests for the router path."""

from __future__ import annotations

import time

import pytest
from qiskit import QuantumCircuit

from ariadne.router import simulate
from ariadne.types import BackendType


@pytest.mark.performance
def test_router_small_circuit_performance_budget() -> None:
    circuit = QuantumCircuit(3)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.cx(1, 2)
    circuit.measure_all()

    start = time.perf_counter()
    result = simulate(circuit, shots=64, backend="qiskit")
    duration = time.perf_counter() - start

    assert result.backend_used in {BackendType.QISKIT, BackendType.STIM}
    assert duration < 1.5
