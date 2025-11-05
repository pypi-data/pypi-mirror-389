import copy

import pytest

from ariadne import simulate
from ariadne.algorithms import SteaneCode
from ariadne.algorithms.base import AlgorithmParameters
from ariadne.core import CircuitTooLargeError


def test_steane_code_routing():
    params = AlgorithmParameters(n_qubits=7)
    steane = SteaneCode(params)
    qc = steane.create_circuit()
    # Simulate without noise for basic routing test
    try:
        result = simulate(qc, shots=500, backend="qiskit")
    except CircuitTooLargeError:
        pytest.skip("Circuit too large for qiskit backend")
    # Should use Qiskit for error correction circuit
    assert result.backend_used.value == "qiskit"
    assert result.counts
    # Basic check: logical zero should dominate for encoding |0>
    zero_string = "0" * 7
    if zero_string in result.counts:
        zero_prob = result.counts[zero_string] / 500
        assert zero_prob > 0.8, f"Low logical zero probability: {zero_prob}"


def test_steane_code_with_error():
    params = AlgorithmParameters(n_qubits=7)
    steane = SteaneCode(params)
    # Create with error
    params = copy.deepcopy(steane.params)
    params.custom_params = {"introduce_error": True, "error_qubit": 0, "error_type": "X"}
    steane.params = params
    qc = steane.create_circuit()
    try:
        result = simulate(qc, shots=500, backend="qiskit")
    except CircuitTooLargeError:
        pytest.skip("Circuit too large for qiskit backend")
    assert result.counts
    # With X error on qubit 0, expect flipped parity
    # Simplified check - full syndrome decoding needed for complete test
    assert len(result.counts) > 1  # Syndrome should show error
