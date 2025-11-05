"""
Test validation module typing and edge cases to improve coverage.
"""

import pytest
from qiskit import QuantumCircuit

from ariadne.validation import (
    CircuitValidator,
    check_simulation_requirements,
    validate_circuit_for_simulation,
    validate_measurement_indices,
)


class TestValidationTyping:
    """Test validation module with focus on typing and edge cases."""

    def test_circuit_validator_comprehensive(self):
        """Test CircuitValidator with various scenarios."""
        validator = CircuitValidator()

        # Test empty validator
        assert len(validator.checks) == 0

        # Test adding custom checks
        def custom_check(circuit):
            return True, "Custom check passed"

        validator.add_check(custom_check, "Custom validation")
        assert len(validator.checks) == 1

        # Test validation with simple circuit
        qc = QuantumCircuit(2)
        qc.h(0)
        qc.cx(0, 1)

        results = validator.validate(qc)
        assert results["valid"] is True
        assert len(results["passed_checks"]) == 1
        assert len(results["failed_checks"]) == 0

    def test_circuit_validator_with_failing_check(self):
        """Test CircuitValidator with a failing check."""
        validator = CircuitValidator()

        def failing_check(circuit):
            return False, "This check always fails"

        validator.add_check(failing_check, "Failing validation")

        qc = QuantumCircuit(2)
        results = validator.validate(qc)

        assert results["valid"] is False
        assert len(results["passed_checks"]) == 0
        assert len(results["failed_checks"]) == 1

    def test_circuit_validator_with_exception(self):
        """Test CircuitValidator when a check raises an exception."""
        validator = CircuitValidator()

        def exception_check(circuit):
            raise ValueError("Test exception")

        validator.add_check(exception_check, "Exception validation")

        qc = QuantumCircuit(2)
        results = validator.validate(qc)

        assert results["valid"] is False
        assert len(results["failed_checks"]) == 1
        assert "Check failed with error" in results["failed_checks"][0][1]

    def test_check_simulation_requirements_comprehensive(self):
        """Test check_simulation_requirements with various circuits."""

        # Test small circuit
        qc_small = QuantumCircuit(2)
        qc_small.h(0)
        qc_small.cx(0, 1)

        result = check_simulation_requirements(qc_small)
        assert result["valid"] is True
        assert isinstance(result["warnings"], list)
        assert isinstance(result["errors"], list)
        assert result["recommended_backend"] in ["auto", None]

        # Test with specific backend
        result_with_backend = check_simulation_requirements(qc_small, backend="stim")
        assert result_with_backend["recommended_backend"] == "stim"

        # Test large circuit warnings
        qc_large = QuantumCircuit(25)  # Should trigger warning for non-specialized backends
        qc_large.h(0)
        for i in range(24):
            qc_large.cx(i, i + 1)

        result_large = check_simulation_requirements(qc_large, backend="qiskit")
        warnings = result_large["warnings"]
        assert len(warnings) > 0
        assert any("specialized backends" in warning for warning in warnings)

    def test_validate_circuit_for_simulation(self):
        """Test the backward compatibility validation function."""
        qc = QuantumCircuit(2)
        qc.h(0)
        qc.cx(0, 1)

        # Should return True for valid circuit
        result = validate_circuit_for_simulation(qc)
        assert result is True

        # Test with backend specification
        result_with_backend = validate_circuit_for_simulation(qc, backend="stim")
        assert result_with_backend is True

    def test_validate_measurement_indices(self):
        """Test measurement indices validation."""
        # Test valid measurement indices
        qubit_indices = [0, 1]
        classical_indices = [0, 1]
        max_qubits = 3
        max_classical_bits = 2

        # Should not raise for valid indices
        validate_measurement_indices(qubit_indices, classical_indices, max_qubits, max_classical_bits)

        # Test with invalid classical bit index
        with pytest.raises(ValueError, match="Classical bit index"):
            validate_measurement_indices([0, 1], [0, 2], 2, 1)  # classical bit 2 doesn't exist

    def test_edge_cases(self):
        """Test edge cases and error conditions."""

        # Single qubit circuit
        qc_single = QuantumCircuit(1)
        result = check_simulation_requirements(qc_single)
        assert result["valid"] is True  # Single qubit circuits are valid

        # Very deep circuit
        qc_deep = QuantumCircuit(2)
        for _ in range(150):  # Should trigger depth warning
            qc_deep.h(0)
            qc_deep.cx(0, 1)

        result_deep = check_simulation_requirements(qc_deep)
        warnings = result_deep["warnings"]
        assert len(warnings) > 0  # Should have warnings for deep circuit
