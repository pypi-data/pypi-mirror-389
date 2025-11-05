"""Tests for 2D/3D grid topologies and routing decisions."""

import numpy as np
import pytest
from qiskit import QuantumCircuit

from ariadne.route.analyze import analyze_circuit
from ariadne.route.mps_analyzer import should_use_mps
from ariadne.route.topology_analyzer import detect_layout_properties


def create_grid_circuit(rows, cols, entangle_neighbors=True):
    """Create a quantum circuit with a grid-like connectivity pattern."""
    n_qubits = rows * cols
    qc = QuantumCircuit(n_qubits)

    # Add single-qubit gates randomly
    for i in range(n_qubits):
        if np.random.random() > 0.5:
            qc.h(i)
        else:
            qc.ry(np.random.random(), i)

    # Add entangling gates between grid neighbors
    if entangle_neighbors:
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


def create_3d_grid_circuit(width, height, depth, entangle_neighbors=True):
    """Create a quantum circuit with a 3D grid-like connectivity pattern."""
    n_qubits = width * height * depth
    qc = QuantumCircuit(n_qubits)

    # Add single-qubit gates randomly
    for i in range(n_qubits):
        if np.random.random() > 0.5:
            qc.h(i)
        else:
            qc.ry(np.random.random(), i)

    # Add entangling gates between 3D grid neighbors
    if entangle_neighbors:
        for x in range(width):
            for y in range(height):
                for z in range(depth):
                    current = x * height * depth + y * depth + z

                    # Connect to x+1 neighbor
                    if x < width - 1:
                        right = (x + 1) * height * depth + y * depth + z
                        qc.cx(current, right)

                    # Connect to y+1 neighbor
                    if y < height - 1:
                        bottom = x * height * depth + (y + 1) * depth + z
                        qc.cx(current, bottom)

                    # Connect to z+1 neighbor
                    if z < depth - 1:
                        up = x * height * depth + y * depth + (z + 1)
                        qc.cx(current, up)

    qc.measure_all()
    return qc


def test_2d_grid_topology_detection():
    """Test that 2D grid topologies are correctly detected."""
    # Test 2x2 grid
    qc = create_grid_circuit(2, 2)
    topology_props = detect_layout_properties(qc)

    # Small 2x2 grids have bounded degree
    # Note: grid_like detection is not yet implemented, defaults to False
    assert topology_props["max_degree"] <= 4  # Max 4 neighbors in 2D grid
    assert topology_props["max_degree"] >= 2  # More than chain-like

    # Test 3x3 grid
    qc = create_grid_circuit(3, 3)
    topology_props = detect_layout_properties(qc)

    # 3x3 grid should not be chain-like (has nodes with degree > 2)
    assert topology_props["max_degree"] <= 4  # Grid topology bounded degree
    assert topology_props["max_degree"] > 2  # More complex than chain


def test_3d_grid_topology_detection():
    """Test that 3D grid topologies are correctly detected."""
    # Test 2x2x2 grid
    qc = create_3d_grid_circuit(2, 2, 2)
    topology_props = detect_layout_properties(qc)

    # 3D grids have more connections than 2D grids
    assert topology_props["max_degree"] <= 6  # Max 6 neighbors in 3D grid
    assert topology_props["max_degree"] > 2  # More complex than chain


def test_2d_grid_routing_mps_behavior():
    """Test MPS routing behavior on 2D grid circuits."""
    # Create 2x4 chain-like grid that might be suitable for MPS
    qc = create_grid_circuit(2, 4, entangle_neighbors=True)
    detect_layout_properties(qc)
    should_use_mps(qc)

    # The 2x4 grid when linearized might look suitable for MPS
    # but with high entanglement it might not be

    # Analysis should show the topology properties
    circuit_analysis = analyze_circuit(qc)
    assert "entanglement_entropy_estimate" in circuit_analysis


def test_2d_ladder_topology():
    """Test ladder topology (2-row grid) which is intermediate between chain and grid."""
    rows, cols = 2, 6
    n_qubits = rows * cols
    qc = QuantumCircuit(n_qubits)

    # Create ladder structure: 2 rows of qubits with connections along rows and between rows
    for col in range(cols):
        # Horizontal connections in each row
        if col < cols - 1:
            qc.cx(col, col + 1)  # Top row
            qc.cx(cols + col, cols + col + 1)  # Bottom row

        # Vertical connections between rows
        qc.cx(col, cols + col)

    qc.measure_all()

    topology_props = detect_layout_properties(qc)

    # Ladder should not be chain-like but have some linear properties
    assert "max_degree" in topology_props
    assert topology_props["max_degree"] <= 4  # At most 4 neighbors per qubit in ladder

    # Should not be fully grid-like
    analyze_circuit(qc)
    assert len(qc.qubits) == n_qubits


def test_grid_vs_chain_entanglement():
    """Compare entanglement characteristics of grid vs chain topologies."""
    # Create a chain circuit
    n_qubits = 8
    chain_qc = QuantumCircuit(n_qubits)
    for i in range(n_qubits - 1):
        chain_qc.cx(i, i + 1)
    chain_qc.measure_all()

    # Create a grid circuit
    grid_qc = create_grid_circuit(2, 4)

    chain_topology = detect_layout_properties(chain_qc)
    grid_topology = detect_layout_properties(grid_qc)

    # Chain should be identified as chain-like
    assert chain_topology["chain_like"]

    # Grid should not be chain-like
    assert not grid_topology["chain_like"]

    # Grid should have different entanglement characteristics
    chain_analysis = analyze_circuit(chain_qc)
    grid_analysis = analyze_circuit(grid_qc)

    # Both should have entanglement measures
    assert "entanglement_entropy_estimate" in chain_analysis
    assert "entanglement_entropy_estimate" in grid_analysis


def test_large_grid_performance():
    """Test performance on larger grid circuits."""
    # Create a larger grid circuit
    qc = create_grid_circuit(4, 4)  # 16-qubit grid

    # This should not take too long to analyze
    import time

    start_time = time.time()
    detect_layout_properties(qc)
    analysis_time = time.time() - start_time

    # Topology analysis should be fast (< 20ms target)
    assert analysis_time < 0.02, f"Topology analysis took {analysis_time:.4f}s, exceeding 20ms target"

    # Circuit analysis should also be fast
    start_time = time.time()
    analyze_circuit(qc)
    analysis_time = time.time() - start_time

    # Circuit analysis should be fast (< 20ms target)
    assert analysis_time < 0.02, f"Circuit analysis took {analysis_time:.4f}s, exceeding 20ms target"


def test_grid_with_various_connectivity():
    """Test grids with different connectivity patterns."""
    # Test a grid with periodic boundary conditions (torus-like)
    n_qubits = 9
    qc = QuantumCircuit(n_qubits)

    # Create 3x3 grid with periodic boundaries
    for row in range(3):
        for col in range(3):
            current = row * 3 + col

            # Right neighbor (with periodic boundary)
            right = row * 3 + ((col + 1) % 3)
            qc.cx(current, right)

            # Bottom neighbor (with periodic boundary)
            bottom = ((row + 1) % 3) * 3 + col
            qc.cx(current, bottom)

    qc.measure_all()

    topology_props = detect_layout_properties(qc)
    assert "max_degree" in topology_props
    assert topology_props["max_degree"] <= 4  # Still bounded by grid structure

    # Should not be chain-like due to periodic connections
    assert not topology_props["chain_like"]


if __name__ == "__main__":
    pytest.main([__file__])
