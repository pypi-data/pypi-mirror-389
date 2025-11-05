#!/usr/bin/env python3
"""
Ariadne in 10 lines - the simplest possible quantum computing example.

This demonstrates Ariadne's core value proposition: automatic backend selection
for quantum circuit simulation with zero configuration required.
"""

from ariadne import simulate
from qiskit import QuantumCircuit

# Create a Bell state (maximally entangled 2-qubit state)
qc = QuantumCircuit(2, 2)
qc.h(0)        # Put first qubit in superposition
qc.cx(0, 1)    # Entangle qubits
qc.measure_all()  # Measure both qubits

# Ariadne automatically selects the optimal backend
result = simulate(qc, shots=1000)

print(f"Backend: {result.backend_used}")
print(f"Results: {dict(result.counts)}")
print(f"Time: {result.execution_time:.3f}s")
