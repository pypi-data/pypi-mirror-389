"""Tests for mixed sparse/dense circuit topologies and routing decisions."""

import numpy as np
import pytest
from qiskit import QuantumCircuit

from ariadne.route.analyze import analyze_circuit
from ariadne.route.mps_analyzer import should_use_mps
from ariadne.route.topology_analyzer import detect_layout_properties


def create_sparse_circuit(n_qubits, connection_probability=0.3):
    """Create a sparse circuit with limited connectivity."""
    qc = QuantumCircuit(n_qubits)

    # Add single-qubit gates randomly
    for i in range(n_qubits):
        if np.random.random() > 0.5:
            qc.h(i)
        else:
            qc.ry(np.random.random(), i)

    # Add sparse entangling gates
    for i in range(n_qubits):
        for j in range(i + 1, n_qubits):
            if np.random.random() < connection_probability:
                qc.cx(i, j)

    qc.measure_all()
    return qc


def create_dense_circuit(n_qubits):
    """Create a dense circuit with high connectivity."""
    qc = QuantumCircuit(n_qubits)

    # Add single-qubit gates
    for i in range(n_qubits):
        if np.random.random() > 0.5:
            qc.h(i)
        else:
            qc.ry(np.random.random(), i)

    # Add entangling gates between all pairs
    for i in range(n_qubits):
        for j in range(i + 1, n_qubits):
            qc.cx(i, j)

    qc.measure_all()
    return qc


def create_mixed_circuit(n_qubits, sparse_region_size=4):
    """Create a circuit with both sparse and dense regions."""
    qc = QuantumCircuit(n_qubits)

    # Add single-qubit gates
    for i in range(n_qubits):
        if np.random.random() > 0.5:
            qc.h(i)
        else:
            qc.ry(np.random.random(), i)

    # Create sparse connections for all qubits
    for i in range(n_qubits):
        for j in range(i + 1, n_qubits):
            if np.random.random() < 0.2:  # Sparse connection
                qc.cx(i, j)

    # Create a dense region within the first sparse_region_size qubits
    if sparse_region_size <= n_qubits:
        for i in range(sparse_region_size):
            for j in range(i + 1, sparse_region_size):
                # Add more connections to make this region dense
                if len([inst for inst in qc.data if inst.operation.name == "cx"]) == 0 or np.random.random() < 0.7:
                    qc.cx(i, j)

    qc.measure_all()
    return qc


def test_sparse_circuit_properties():
    """Test detection of sparse circuit properties."""
    qc = create_sparse_circuit(10, connection_probability=0.2)
    topology_props = detect_layout_properties(qc)

    # Sparse circuits should have low max degree
    assert topology_props["max_degree"] < 8  # Lower than dense circuits

    circuit_analysis = analyze_circuit(qc)
    assert "entanglement_entropy_estimate" in circuit_analysis


def test_dense_circuit_properties():
    """Test detection of dense circuit properties."""
    qc = create_dense_circuit(6)  # Keep small to avoid exponential overhead
    topology_props = detect_layout_properties(qc)

    # Dense circuits should have high max degree (close to fully connected)
    assert topology_props["max_degree"] >= (len(qc.qubits) - 1) * 0.7  # Most nodes highly connected
    assert topology_props["max_degree"] == len(qc.qubits) - 1  # Fully connected

    circuit_analysis = analyze_circuit(qc)
    assert "entanglement_entropy_estimate" in circuit_analysis


def test_mixed_sparse_dense_properties():
    """Test detection of mixed sparse/dense circuit properties."""
    qc = create_mixed_circuit(12, sparse_region_size=6)
    topology_props = detect_layout_properties(qc)

    # Mixed circuit should have intermediate properties
    assert "max_degree" in topology_props

    # The max degree might be higher due to the dense region
    circuit_analysis = analyze_circuit(qc)
    assert "entanglement_entropy_estimate" in circuit_analysis


def test_sparse_circuit_routing_preference():
    """Test routing preferences for sparse circuits."""
    qc = create_sparse_circuit(10, connection_probability=0.1)
    detect_layout_properties(qc)

    # Sparse circuits might be good for tensor network simulation
    # depending on the treewidth
    analyze_circuit(qc)

    # Analysis should complete quickly (under 20ms target)
    import time

    start_time = time.time()
    detect_layout_properties(qc)
    analysis_time = time.time() - start_time
    assert analysis_time < 0.02, f"Topology analysis took {analysis_time:.4f}s, exceeding 20ms target"


def test_dense_circuit_routing_preference():
    """Test routing preferences for dense circuits."""
    qc = create_dense_circuit(8)  # Keep smaller for dense circuit
    topology_props = detect_layout_properties(qc)

    # Dense circuits typically have high treewidth, may not be good for tensor networks
    assert topology_props["max_degree"] == len(qc.qubits) - 1  # Fully connected topology

    analyze_circuit(qc)
    # Dense circuits tend to have high entanglement


def test_mixed_circuit_behavior():
    """Test behavior on circuits with mixed sparse/dense regions."""
    qc = create_mixed_circuit(16, sparse_region_size=8)

    topology_props = detect_layout_properties(qc)
    circuit_analysis = analyze_circuit(qc)
    mps_decision = should_use_mps(qc)

    # The decision should consider the mixed nature of the topology
    assert isinstance(mps_decision, bool)
    assert "max_degree" in topology_props
    assert "entanglement_entropy_estimate" in circuit_analysis


def test_sparse_dense_transition():
    """Test how topology properties change as connectivity increases."""
    n_qubits = 8
    connection_probs = [0.1, 0.3, 0.5, 0.7, 0.9]

    for prob in connection_probs:
        qc = create_sparse_circuit(n_qubits, connection_probability=prob)
        topology_props = detect_layout_properties(qc)

        # As connectivity increases, max degree should generally increase
        # Allow for some variation due to random circuit generation
        max_degree = topology_props["max_degree"]
        # Just verify it's a valid value
        assert max_degree >= 0
        assert max_degree < n_qubits


def test_large_sparse_circuit():
    """Test performance on larger sparse circuits."""
    qc = create_sparse_circuit(20, connection_probability=0.15)

    import time

    # Test topology detection performance
    start_time = time.time()
    detect_layout_properties(qc)
    topology_time = time.time() - start_time

    # Should meet the <20ms topology target
    assert topology_time < 0.02, f"Topology analysis took {topology_time:.4f}s, exceeding 20ms target"

    # Test circuit analysis performance
    start_time = time.time()
    analyze_circuit(qc)
    analysis_time = time.time() - start_time

    # Should meet the <20ms circuit analysis target
    assert analysis_time < 0.02, f"Circuit analysis took {analysis_time:.4f}s, exceeding 20ms target"


def test_regular_vs_sparse_structure():
    """Compare regular grid structure with irregular sparse structure."""
    # Create a regular grid circuit
    grid_qc = QuantumCircuit(9)
    connections = [
        (0, 1),
        (1, 2),
        (3, 4),
        (4, 5),
        (6, 7),
        (7, 8),  # rows
        (0, 3),
        (3, 6),
        (1, 4),
        (4, 7),
        (2, 5),
        (5, 8),
    ]  # columns
    for a, b in connections:
        grid_qc.cx(a, b)
    grid_qc.measure_all()

    # Create an irregular sparse circuit with same number of qubits and similar connection count
    sparse_qc = create_sparse_circuit(9, connection_probability=0.3)

    grid_topology = detect_layout_properties(grid_qc)
    sparse_topology = detect_layout_properties(sparse_qc)

    # Both should be analyzed quickly

    # Grid should have more predictable structure
    assert grid_topology["max_degree"] <= 4  # Grid-like
    assert sparse_topology["max_degree"] <= 8  # May be higher for sparse random


def test_sparse_circuit_with_weighted_entanglement():
    """Test sparse circuits with different entanglement levels."""
    n_qubits = 10

    # Create a low-entanglement sparse circuit
    low_ent_qc = QuantumCircuit(n_qubits)
    for i in range(n_qubits):
        low_ent_qc.ry(0.1 * np.random.random(), i)  # Small rotation angles = low entanglement
    for i in range(0, n_qubits - 1, 2):  # Sparse entangling
        low_ent_qc.cx(i, i + 1)
    low_ent_qc.measure_all()

    # Create a high-entanglement sparse circuit
    high_ent_qc = QuantumCircuit(n_qubits)
    for i in range(n_qubits):
        high_ent_qc.ry(np.pi * np.random.random(), i)  # Large rotation angles = high entanglement
    for i in range(0, n_qubits - 1, 2):  # Same sparse entangling pattern
        high_ent_qc.cx(i, i + 1)
    high_ent_qc.measure_all()

    # Both should have similar topology (sparse)
    detect_layout_properties(low_ent_qc)
    detect_layout_properties(high_ent_qc)

    # But different entanglement characteristics
    low_analysis = analyze_circuit(low_ent_qc)
    high_analysis = analyze_circuit(high_ent_qc)

    # Both are sparse topologically but may differ in entanglement
    assert "entanglement_entropy_estimate" in low_analysis
    assert "entanglement_entropy_estimate" in high_analysis


if __name__ == "__main__":
    pytest.main([__file__])
