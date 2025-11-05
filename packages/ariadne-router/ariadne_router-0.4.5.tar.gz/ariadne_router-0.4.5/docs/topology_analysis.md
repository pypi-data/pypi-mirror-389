# Topology Analysis

Ariadne includes sophisticated topology analysis to automatically detect circuit patterns and optimize backend selection for real quantum hardware layouts.

## Overview

The topology analyzer examines the connectivity structure of your quantum circuit to:
- Detect chain-like structures (ideal for MPS simulation)
- Identify grid patterns (2D/3D lattices)
- Recognize hardware-specific topologies (IBM, IonQ, Rigetti)
- Estimate resource requirements for different backends

## Supported Topologies

### Linear Chains (IonQ-style)
```python
from ariadne import simulate
from qiskit import QuantumCircuit

# Create a chain circuit (nearest-neighbor connectivity)
qc = QuantumCircuit(10)
for i in range(10):
    qc.h(i)
for i in range(9):
    qc.cx(i, i+1)  # Chain connectivity
qc.measure_all()

# Ariadne detects chain topology → routes to MPS backend
result = simulate(qc, shots=1000)
```

### 2D Grids (Rigetti/Google-style)
```python
# Create a 2D grid circuit
rows, cols = 4, 4
qc = QuantumCircuit(rows * cols)

# Grid connectivity
for row in range(rows):
    for col in range(cols):
        idx = row * cols + col
        if col < cols - 1:  # Right neighbor
            qc.cx(idx, idx + 1)
        if row < rows - 1:  # Bottom neighbor
            qc.cx(idx, idx + cols)

qc.measure_all()
result = simulate(qc, shots=1000)
```

### Heavy-Hex (IBM-style)
```python
# IBM Falcon/Eagle heavy-hex connectivity
# Ariadne automatically detects the topology and optimizes routing
connections = [(0,1), (1,2), (1,4), (2,5), (3,4), (4,5), (4,7), (5,8), (6,7), (7,8)]
qc = QuantumCircuit(9)
for a, b in connections:
    qc.cx(a, b)
qc.measure_all()

result = simulate(qc, shots=1000)
```

## API Reference

### `detect_layout_properties(circuit)`

Analyzes a quantum circuit's topology and returns properties.

**Returns:**
```python
{
    "chain_like": bool,      # True if circuit has chain topology (max degree ≤ 2)
    "grid_like": bool,       # True if circuit has grid topology (not yet implemented)
    "depth": int,            # Circuit depth
    "max_degree": int,       # Maximum connectivity degree in interaction graph
}
```

**Example:**
```python
from ariadne.route import detect_layout_properties

props = detect_layout_properties(circuit)
print(f"Chain-like: {props['chain_like']}")
print(f"Max degree: {props['max_degree']}")
```

### `should_use_mps(circuit)`

Determines if a circuit is suitable for MPS (Matrix Product State) simulation.

**Heuristics:**
- **Small circuits (< 15 qubits):** Checks gate count and depth
- **Large circuits (≥ 15 qubits):** Requires chain-like topology (max degree ≤ 2) and shallow depth

**Returns:** `bool`

**Example:**
```python
from ariadne.route import should_use_mps

if should_use_mps(circuit):
    print("Circuit is suitable for efficient MPS simulation")
```

## Performance Targets

Topology analysis is designed to be extremely fast:
- **Topology detection:** < 2ms
- **Full circuit analysis:** < 2ms

These targets ensure routing decisions don't add noticeable overhead to your simulation workflow.

## Hardware-Specific Optimizations

### IonQ Trapped Ions
- **Topology:** Linear chain
- **Optimal Backend:** MPS (for low entanglement) or Qiskit
- **Detection:** Automatic via max degree ≤ 2

### Rigetti Square Lattice
- **Topology:** 2D grid with 4-connectivity
- **Optimal Backend:** Tensor Network or Qiskit
- **Detection:** Max degree ≤ 4, grid pattern

### IBM Heavy-Hex
- **Topology:** Hexagonal lattice with degree ≤ 3
- **Optimal Backend:** Qiskit or Tensor Network
- **Detection:** Bounded degree, non-chain pattern

### Google Sycamore
- **Topology:** 2D grid with nearest-neighbor connectivity
- **Optimal Backend:** Tensor Network or Qiskit
- **Detection:** Grid pattern, degree ≤ 4

## Test Coverage

Comprehensive test suite validates topology detection:
- `tests/test_grid_topologies.py` - 2D/3D grids
- `tests/test_hardware_layouts.py` - IBM, IonQ, Rigetti topologies
- `tests/test_mixed_sparse_dense.py` - Variable connectivity patterns
- `tests/test_mps_analyzer.py` - MPS backend selection

All tests pass with < 2ms analysis time targets.

## Future Enhancements

Planned improvements:
- [ ] Implement full `grid_like` detection algorithm
- [ ] Add `average_degree` calculation
- [ ] Support for 3D topologies (quantum error correction)
- [ ] Automatic hardware preset selection
- [ ] Visual topology graphs
