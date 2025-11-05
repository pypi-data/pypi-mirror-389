"""Tests for hardware-specific layouts (IBM heavy-hex, IonQ chains, Rigetti square)."""

import os
import time

import numpy as np
import pytest
from qiskit import QuantumCircuit

from ariadne.route.analyze import analyze_circuit
from ariadne.route.mps_analyzer import should_use_mps
from ariadne.route.topology_analyzer import detect_layout_properties


def _running_with_coverage() -> bool:
    try:
        import coverage  # type: ignore

        if coverage.Coverage.current():  # pragma: no cover - low-level hook
            return True
    except Exception:
        pass

    coverage_markers = (
        "PYTEST_COV_SOURCE",
        "COV_CORE_SOURCE",
        "COVERAGE_RUN",
        "COVERAGE_PROCESS_START",
    )
    return any(key in os.environ for key in coverage_markers)


_PERF_BUDGET = 0.02 if not _running_with_coverage() else 0.12


def create_ionq_chain_circuit(n_qubits):
    """Create a circuit mimicking IonQ's linear chain connectivity."""
    qc = QuantumCircuit(n_qubits)

    # Add single-qubit gates
    for i in range(n_qubits):
        if np.random.random() > 0.5:
            qc.h(i)
        else:
            qc.ry(np.random.random(), i)

    # Add entangling gates in a chain pattern (nearest neighbors only)
    for i in range(n_qubits - 1):
        qc.cx(i, i + 1)

    qc.measure_all()
    return qc


def create_heavy_hex_circuit(n_qubits_per_side=3):
    """Create a circuit mimicking IBM's heavy-hex lattice."""
    # Heavy-hex lattice: hexagons connected in a specific pattern
    # For simplicity, we'll create a subset that maintains the heavy-hex connectivity property
    total_qubits = 2 * n_qubits_per_side * (n_qubits_per_side + 1)
    qc = QuantumCircuit(total_qubits)

    # Add single-qubit gates
    for i in range(total_qubits):
        if np.random.random() > 0.5:
            qc.h(i)
        else:
            qc.ry(np.random.random(), i)

    # Create heavy-hex like connectivity (simplified version)
    # This implementation creates a pattern similar to heavy-hex
    for row in range(n_qubits_per_side):
        # Horizontal connections
        for col in range(2 * (row + 1) - 1):
            if col < 2 * (row + 1) - 2:
                qc.cx(row * 2 * (n_qubits_per_side + 1) + col, row * 2 * (n_qubits_per_side + 1) + col + 1)

        # Vertical connections between rows
        if row < n_qubits_per_side - 1:
            for col in range(0, 2 * (row + 1), 2):  # Even indices
                lower_row_start = (row + 1) * 2 * (n_qubits_per_side + 1)
                if lower_row_start + col < total_qubits and row * 2 * (n_qubits_per_side + 1) + col < total_qubits:
                    qc.cx(row * 2 * (n_qubits_per_side + 1) + col, lower_row_start + col)

    qc.measure_all()
    return qc


def create_rigetti_square_circuit(rows=4, cols=4):
    """Create a circuit mimicking Rigetti's square lattice connectivity."""
    n_qubits = rows * cols
    qc = QuantumCircuit(n_qubits)

    # Add single-qubit gates
    for i in range(n_qubits):
        if np.random.random() > 0.5:
            qc.h(i)
        else:
            qc.ry(np.random.random(), i)

    # Add entangling gates in square grid pattern
    for row in range(rows):
        for col in range(cols):
            current = row * cols + col

            # Connect to right neighbor
            if col < cols - 1:
                right = row * cols + (col + 1)
                qc.cx(current, right)

            # Connect to bottom neighbor
            if row < rows - 1:
                bottom = (row + 1) * cols + col
                qc.cx(current, bottom)

    qc.measure_all()
    return qc


def create_ibm_falcon_circuit():
    """Create a circuit mimicking IBM Falcon's connectivity (simplified)."""
    # IBM Falcon has a heavy-hexagon like structure but with some modifications
    # Using a small subset for testing

    # Define a small heavy-hex inspired graph
    connections = [
        (0, 1),
        (1, 2),  # Top row
        (1, 4),
        (2, 5),  # Connections down
        (3, 4),
        (4, 5),  # Middle row
        (4, 7),
        (5, 8),  # Connections down
        (6, 7),
        (7, 8),  # Bottom row
    ]

    max_qubit = max(max(conn) for conn in connections)
    qc = QuantumCircuit(max_qubit + 1)

    # Add single-qubit gates
    for i in range(max_qubit + 1):
        if np.random.random() > 0.5:
            qc.h(i)
        else:
            qc.ry(np.random.random(), i)

    # Add entangling gates based on topology
    for a, b in connections:
        qc.cx(a, b)

    qc.measure_all()
    return qc


def test_ionq_chain_topology():
    """Test topology detection for IonQ-like chain circuits."""
    qc = create_ionq_chain_circuit(10)
    topology_props = detect_layout_properties(qc)

    # Chain-like topology should be detected
    assert topology_props["chain_like"]
    assert topology_props["max_degree"] <= 2  # Chain has max 2 neighbors

    # For MPS simulation
    mps_decision = should_use_mps(qc)
    # Chain-like circuits with low entanglement might be good for MPS
    assert isinstance(mps_decision, bool)


def test_heavy_hex_topology():
    """Test topology detection for heavy-hex circuits."""
    qc = create_heavy_hex_circuit(n_qubits_per_side=2)
    topology_props = detect_layout_properties(qc)

    # Heavy-hex should not be chain-like
    assert not topology_props.get("chain_like", False)

    # Heavy-hex typically has bounded degree (each node connected to few others)
    assert "max_degree" in topology_props
    assert topology_props["max_degree"] <= 4  # Heavy-hex has bounded degree

    circuit_analysis = analyze_circuit(qc)
    assert "entanglement_entropy_estimate" in circuit_analysis


def test_rigetti_square_topology():
    """Test topology detection for Rigetti square lattice circuits."""
    qc = create_rigetti_square_circuit(rows=3, cols=3)
    topology_props = detect_layout_properties(qc)

    # Should not be chain-like (grid structure)
    assert not topology_props.get("chain_like", True)

    # Grid topology: max 4 neighbors for internal nodes
    assert "max_degree" in topology_props
    assert topology_props["max_degree"] <= 4

    circuit_analysis = analyze_circuit(qc)
    assert "entanglement_entropy_estimate" in circuit_analysis


def test_ibm_falcon_topology():
    """Test topology detection for IBM Falcon-like circuits."""
    qc = create_ibm_falcon_circuit()
    topology_props = detect_layout_properties(qc)

    # Should not be chain-like (more complex topology)
    assert not topology_props.get("chain_like", True)

    # Should have bounded degree (like heavy-hex)
    assert "max_degree" in topology_props
    assert topology_props["max_degree"] <= 4  # Heavy-hex derivatives have low max degree

    circuit_analysis = analyze_circuit(qc)
    assert "entanglement_entropy_estimate" in circuit_analysis


def test_hardware_layout_routing_decisions():
    """Test routing decisions for different hardware layouts."""
    # Test IonQ chain
    ionq_qc = create_ionq_chain_circuit(8)
    ionq_topology = detect_layout_properties(ionq_qc)
    ionq_mps = should_use_mps(ionq_qc)
    analyze_circuit(ionq_qc)

    # Test Rigetti square
    rigetti_qc = create_rigetti_square_circuit(3, 3)
    rigetti_topology = detect_layout_properties(rigetti_qc)
    rigetti_mps = should_use_mps(rigetti_qc)
    analyze_circuit(rigetti_qc)

    # Test IBM-like
    ibm_qc = create_ibm_falcon_circuit()
    ibm_topology = detect_layout_properties(ibm_qc)
    ibm_mps = should_use_mps(ibm_qc)
    analyze_circuit(ibm_qc)

    # All should produce valid results
    assert isinstance(ionq_mps, bool)
    assert isinstance(rigetti_mps, bool)
    assert isinstance(ibm_mps, bool)

    # All should have topology properties
    assert "max_degree" in ionq_topology
    assert "max_degree" in rigetti_topology
    assert "max_degree" in ibm_topology


def test_chain_vs_grid_entanglement():
    """Compare entanglement characteristics of chain vs grid topologies."""
    chain_qc = create_ionq_chain_circuit(12)
    grid_qc = create_rigetti_square_circuit(3, 4)

    chain_topology = detect_layout_properties(chain_qc)
    grid_topology = detect_layout_properties(grid_qc)

    # Chain should be chain-like
    assert chain_topology["chain_like"]

    # Grid should not be chain-like
    assert not grid_topology["chain_like"]

    # Both should be analyzed quickly
    import time

    start = time.time()
    analyze_circuit(chain_qc)
    chain_analysis_time = time.time() - start
    assert chain_analysis_time < _PERF_BUDGET, f"Chain analysis took {chain_analysis_time:.4f}s"

    start = time.time()
    analyze_circuit(grid_qc)
    grid_analysis_time = time.time() - start
    assert grid_analysis_time < _PERF_BUDGET, f"Grid analysis took {grid_analysis_time:.4f}s"


def test_heavy_hex_properties():
    """Test specific properties of heavy-hex topology."""
    qc = create_heavy_hex_circuit(n_qubits_per_side=3)
    topology_props = detect_layout_properties(qc)

    # Heavy-hex should have specific properties
    assert "max_degree" in topology_props
    assert topology_props["max_degree"] <= 4  # Bounded degree property
    assert not topology_props.get("chain_like", True)  # Not a chain

    # Circuit analysis should work
    circuit_analysis = analyze_circuit(qc)
    assert "entanglement_entropy_estimate" in circuit_analysis


def test_performance_on_hardware_topologies():
    """Test performance targets on hardware topology circuits."""
    # Test all hardware layouts meet performance targets

    # IonQ chain
    ionq_qc = create_ionq_chain_circuit(15)
    start = time.time()
    detect_layout_properties(ionq_qc)
    time_taken = time.time() - start
    assert time_taken < _PERF_BUDGET, f"IonQ topology detection took {time_taken:.4f}s"

    start = time.time()
    analyze_circuit(ionq_qc)
    time_taken = time.time() - start
    assert time_taken < _PERF_BUDGET, f"IonQ circuit analysis took {time_taken:.4f}s"

    # Rigetti square
    rigetti_qc = create_rigetti_square_circuit(4, 4)
    start = time.time()
    detect_layout_properties(rigetti_qc)
    time_taken = time.time() - start
    assert time_taken < _PERF_BUDGET, f"Rigetti topology detection took {time_taken:.4f}s"

    start = time.time()
    analyze_circuit(rigetti_qc)
    time_taken = time.time() - start
    assert time_taken < _PERF_BUDGET, f"Rigetti circuit analysis took {time_taken:.4f}s"

    # IBM-like
    ibm_qc = create_ibm_falcon_circuit()
    start = time.time()
    detect_layout_properties(ibm_qc)
    time_taken = time.time() - start
    assert time_taken < _PERF_BUDGET, f"IBM topology detection took {time_taken:.4f}s"

    start = time.time()
    analyze_circuit(ibm_qc)
    time_taken = time.time() - start
    assert time_taken < _PERF_BUDGET, f"IBM circuit analysis took {time_taken:.4f}s"


def test_weighted_entanglement_thresholds():
    """Test weighted entanglement thresholds on hardware layouts."""
    import time

    # Low entanglement version
    low_ent_qc = QuantumCircuit(10)
    for i in range(10):
        low_ent_qc.ry(0.1 * np.random.random(), i)
    for i in range(9):
        low_ent_qc.cx(i, i + 1)
    low_ent_qc.measure_all()

    # High entanglement version
    high_ent_qc = QuantumCircuit(10)
    for i in range(10):
        low_ent_qc.ry(np.pi * np.random.random(), i)  # Higher rotation angles
    for i in range(9):
        low_ent_qc.cx(i, i + 1)
    high_ent_qc.measure_all()

    # Check that both can be analyzed quickly
    start = time.time()
    analyze_circuit(low_ent_qc)
    low_time = time.time() - start
    assert low_time < _PERF_BUDGET, f"Low entanglement analysis took {low_time:.4f}s"

    start = time.time()
    analyze_circuit(high_ent_qc)
    high_time = time.time() - start
    assert high_time < _PERF_BUDGET, f"High entanglement analysis took {high_time:.4f}s"


if __name__ == "__main__":
    import time

    pytest.main([__file__])
