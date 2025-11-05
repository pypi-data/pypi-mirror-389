# Getting Started with Ariadne

This guide will help you get up and running with Ariadne, the intelligent quantum simulator router.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Your First Simulation](#your-first-simulation)
- [Understanding Routing](#understanding-routing)
- [Working with Different Circuit Types](#working-with-different-circuit-types)
- [Next Steps](#next-steps)

---

## Prerequisites

Before installing Ariadne, ensure you have:

- **Python 3.11 or 3.12** installed
- **pip** package manager (comes with Python)
- Basic understanding of quantum computing concepts (recommended but not required)

### Check Your Python Version

```bash
python --version
# or
python3 --version
```

If you need to install Python, visit [python.org/downloads](https://www.python.org/downloads/).

---

## Installation

### Basic Installation

Install Ariadne with the default backends (Stim, Qiskit Aer, MPS, Tensor Networks):

```bash
pip install ariadne-router
```

### Installation with Optional Features

Depending on your needs, you can install additional features:

#### For Apple Silicon Users (M1/M2/M3/M4)

```bash
pip install ariadne-router[apple]
```

This enables hardware-accelerated simulation using Metal (experimental).

#### For NVIDIA GPU Users

```bash
pip install ariadne-router[cuda]
```

This enables CUDA-accelerated simulation (experimental).

#### For All Quantum Platforms

```bash
pip install ariadne-router[quantum_platforms]
```

This includes PennyLane, PyQuil, Amazon Braket, Q#, and OpenCL support.

#### For Development

```bash
pip install ariadne-router[dev]
```

This includes testing tools, linters, and documentation generators.

### Verify Installation

```bash
python -c "import ariadne; print('Ariadne installed successfully!')"
```

---

## Your First Simulation

Let's create and simulate a simple quantum circuit.

### Example 1: Bell State

Create a file called `first_simulation.py`:

```python
from ariadne import simulate
from qiskit import QuantumCircuit

# Create a Bell state circuit
qc = QuantumCircuit(2, 2)
qc.h(0)  # Hadamard on qubit 0
qc.cx(0, 1)  # CNOT from qubit 0 to qubit 1
qc.measure([0, 1], [0, 1])  # Measure both qubits

# Simulate with Ariadne
result = simulate(qc, shots=1000)

# Display results
print(f"Backend used: {result.backend_used}")
print(f"Execution time: {result.execution_time:.4f} seconds")
print(f"Results: {dict(result.counts)}")
```

Run it:

```bash
python first_simulation.py
```

**Expected output:**
```
Backend used: stim
Execution time: 0.0015 seconds
Results: {'00': 503, '11': 497}
```

The results show approximately equal probabilities for |00⟩ and |11⟩, which is expected for a Bell state. The exact counts will vary due to statistical sampling.

---

## Understanding Routing

Ariadne automatically selects the best backend for your circuit. Let's explore how this works.

### Example 2: Routing Explanation

```python
from ariadne import simulate, explain_routing
from qiskit import QuantumCircuit

# Create a Clifford circuit
clifford_qc = QuantumCircuit(5, 5)
clifford_qc.h(0)
clifford_qc.cx(0, 1)
clifford_qc.cx(1, 2)
clifford_qc.cx(2, 3)
clifford_qc.cx(3, 4)
clifford_qc.measure_all()

# Get routing explanation before simulating
explanation = explain_routing(clifford_qc)
print(f"Routing decision: {explanation}")

# Simulate
result = simulate(clifford_qc, shots=1000)
print(f"Backend used: {result.backend_used}")
print(f"Execution time: {result.execution_time:.4f}s")
```

**Output:**
```
Routing decision: Clifford circuit detected → routed to Stim for optimal performance
Backend used: stim
Execution time: 0.0012s
```

### How Routing Works

Ariadne analyzes your circuit based on:

1. **Gate Types**: Detects Clifford vs. non-Clifford gates
2. **Circuit Size**: Considers number of qubits and gates
3. **Topology**: Analyzes qubit connectivity patterns
4. **Entanglement**: Estimates entanglement complexity
5. **Available Hardware**: Checks for GPU/accelerator availability

---

## Working with Different Circuit Types

### Example 3: Non-Clifford Circuit

```python
from ariadne import simulate, explain_routing
from qiskit import QuantumCircuit
import numpy as np

# Create a circuit with T gates (non-Clifford)
qc = QuantumCircuit(3, 3)
qc.h(0)
qc.t(0)  # T gate (non-Clifford)
qc.cx(0, 1)
qc.t(1)
qc.cx(1, 2)
qc.measure_all()

print(f"Routing: {explain_routing(qc)}")
result = simulate(qc, shots=1000)
print(f"Backend: {result.backend_used}")
print(f"Time: {result.execution_time:.4f}s")
```

**Expected output:**
```
Routing: Non-Clifford circuit → routed to MPS backend
Backend: mps
Time: 0.0245s
```

### Example 4: Large GHZ State

```python
from ariadne import simulate
from qiskit import QuantumCircuit

# Create a 40-qubit GHZ state
qc = QuantumCircuit(40, 40)
qc.h(0)
for i in range(39):
    qc.cx(i, i + 1)
qc.measure_all()

result = simulate(qc, shots=1000)
print(f"Backend: {result.backend_used}")
print(f"Time: {result.execution_time:.4f}s")

# Count results (should mainly be all 0s or all 1s)
counts = dict(result.counts)
print(f"Number of unique outcomes: {len(counts)}")
```

### Example 5: Manual Backend Selection

Sometimes you want to override automatic routing:

```python
from ariadne import simulate
from qiskit import QuantumCircuit

qc = QuantumCircuit(5, 5)
qc.h(range(5))
qc.measure_all()

# Force Qiskit backend
result = simulate(qc, backend='qiskit', shots=1000)
print(f"Backend: {result.backend_used}")
```

---

## Using Educational Features

Ariadne includes educational tools to help you learn quantum computing.

### Example 6: Interactive Circuit Builder

```python
from ariadne import InteractiveCircuitBuilder, simulate

# Build a circuit with explanations
builder = InteractiveCircuitBuilder(3, "Three-Qubit GHZ")
builder.add_hadamard(0, "Superposition", "Create equal superposition on qubit 0")
builder.add_cnot(0, 1, "Entangle 0-1", "Entangle qubits 0 and 1")
builder.add_cnot(1, 2, "Entangle 1-2", "Extend entanglement to qubit 2")

# Get the circuit
circuit = builder.get_circuit()

# Simulate it
result = simulate(circuit, shots=1000)
print(f"Results: {dict(result.counts)}")
```

### Example 7: Algorithm Library

```python
from ariadne import list_algorithms, get_algorithm, simulate

# List all available algorithms
algorithms = list_algorithms()
print(f"Available algorithms: {algorithms[:5]}...")  # Show first 5

# Get details about a specific algorithm
bell_info = get_algorithm('bell')
print(f"\nBell State Algorithm:")
print(f"Description: {bell_info['metadata'].description}")
print(f"Category: {bell_info['metadata'].category}")

# Create and simulate the circuit
bell_circuit = bell_info['function']()
result = simulate(bell_circuit, shots=1000)
print(f"\nResults: {dict(result.counts)}")
```

---

## Advanced Features

### Routing Strategies

You can specify routing strategies for specific optimization goals:

```python
from ariadne import ComprehensiveRoutingTree, RoutingStrategy
from qiskit import QuantumCircuit

qc = QuantumCircuit(10, 10)
qc.h(range(10))
qc.measure_all()

router = ComprehensiveRoutingTree()

# Optimize for speed
result_speed = router.simulate(qc, strategy=RoutingStrategy.SPEED_FIRST)
print(f"Speed-first: {result_speed.backend_used}, {result_speed.execution_time:.4f}s")

# Optimize for memory
result_memory = router.simulate(qc, strategy=RoutingStrategy.MEMORY_EFFICIENT)
print(f"Memory-efficient: {result_memory.backend_used}, {result_memory.execution_time:.4f}s")
```

### Backend Comparison

Compare performance across different backends:

```python
from ariadne.enhanced_benchmarking import EnhancedBenchmarkSuite
from qiskit import QuantumCircuit

qc = QuantumCircuit(5, 5)
qc.h(range(5))
qc.measure_all()

suite = EnhancedBenchmarkSuite()
comparison = suite.benchmark_backend_comparison(
    circuit=qc,
    backends=['auto', 'qiskit', 'stim'],
    shots=1000
)

print("Backend Comparison:")
for backend, result in comparison.items():
    print(f"  {backend:15s}: {result.execution_time:.4f}s")
```

---

## Next Steps

Now that you've learned the basics, here's what to explore next:

### For Students & Educators
- Explore the [educational examples](../examples/education/)
- Review the [quantum computing primer](quantum_computing_primer.md)

### For Researchers
- Learn about [topology analysis](topology_analysis.md)
- Explore [reproducibility tools](../benchmarks/datasets/README.md)
- Read about [routing decisions](router_decisions.md)

### For Developers
- Check the [developer guide](guides/developer_guide.md)
- Review the [API reference](source/)
- Explore [advanced routing strategies](../examples/06_enhanced_routing_demo.ipynb)

### Additional Resources
- [Performance optimization guide](PERFORMANCE_GUIDE.md)
- [Troubleshooting common issues](troubleshooting.md)
- [Configuration options](options.md)
- [Contributing guidelines](../CONTRIBUTING.md)

---

## Getting Help

If you encounter issues:

1. Check the [Troubleshooting Guide](troubleshooting.md)
2. Search [existing issues](https://github.com/Hmbown/ariadne/issues)
3. Ask questions in [GitHub Discussions](https://github.com/Hmbown/ariadne/discussions)
4. Open a [new issue](https://github.com/Hmbown/ariadne/issues/new) if needed

## Quick Reference

### Most Common Commands

```python
# Basic simulation
from ariadne import simulate
result = simulate(circuit, shots=1000)

# Explain routing
from ariadne import explain_routing
explanation = explain_routing(circuit)

# List available algorithms
from ariadne import list_algorithms
algorithms = list_algorithms()

# Check available backends
from ariadne import get_available_backends
backends = get_available_backends()
```

### CLI Commands

```bash
# Run a circuit from a file
ariadne run circuit.qasm --shots 1000

# Explain routing for a circuit
ariadne explain circuit.qasm

# Benchmark a circuit
ariadne benchmark --circuit ghz_20 --backends auto,qiskit,stim

# List available datasets
ariadne datasets list
```

---

Happy quantum computing with Ariadne!
