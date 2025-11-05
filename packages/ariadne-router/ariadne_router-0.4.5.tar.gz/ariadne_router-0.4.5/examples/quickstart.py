#!/usr/bin/env python3
"""
Ariadne Quickstart Example

This example demonstrates the basic usage of Ariadne for automatic
quantum circuit simulation with intelligent backend selection.
"""

from ariadne import simulate, explain_routing
from qiskit import QuantumCircuit


def main():
    """Run the quickstart example."""
    print("=" * 60)
    print("Ariadne Quickstart: Intelligent Quantum Simulator Router")
    print("=" * 60)

    # Example 1: Simple Bell State
    print("\n📌 Example 1: Bell State")
    print("-" * 60)

    qc = QuantumCircuit(2, 2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure([0, 1], [0, 1])

    print("Circuit created:")
    print(qc.draw(output="text"))

    result = simulate(qc, shots=1000)
    print(f"\nBackend used: {result.backend_used}")
    print(f"Execution time: {result.execution_time:.4f}s")
    print(f"Results: {dict(result.counts)}")

    # Example 2: Large GHZ State with Routing Explanation
    print("\n\n📌 Example 2: 40-Qubit GHZ State")
    print("-" * 60)

    qc_large = QuantumCircuit(40, 40)
    qc_large.h(0)
    for i in range(39):
        qc_large.cx(i, i + 1)
    qc_large.measure_all()

    print(f"Circuit size: {qc_large.num_qubits} qubits, {qc_large.size()} gates")

    # Get routing explanation
    explanation = explain_routing(qc_large)
    print(f"\nRouting explanation: {explanation}")

    result_large = simulate(qc_large, shots=1000)
    print(f"\nBackend used: {result_large.backend_used}")
    print(f"Execution time: {result_large.execution_time:.4f}s")
    print(f"Number of unique outcomes: {len(result_large.counts)}")

    # Example 3: Non-Clifford Circuit
    print("\n\n📌 Example 3: Non-Clifford Circuit (with T gates)")
    print("-" * 60)

    qc_non_clifford = QuantumCircuit(3, 3)
    qc_non_clifford.h(0)
    qc_non_clifford.t(0)  # T gate makes this non-Clifford
    qc_non_clifford.cx(0, 1)
    qc_non_clifford.t(1)
    qc_non_clifford.cx(1, 2)
    qc_non_clifford.measure_all()

    print("Circuit created with T gates (non-Clifford)")
    print(f"\nRouting explanation: {explain_routing(qc_non_clifford)}")

    result_non_clifford = simulate(qc_non_clifford, shots=1000)
    print(f"\nBackend used: {result_non_clifford.backend_used}")
    print(f"Execution time: {result_non_clifford.execution_time:.4f}s")

    print("\n" + "=" * 60)
    print("✓ Quickstart complete! Ariadne automatically selected")
    print("  the optimal backend for each circuit type.")
    print("\nNext steps:")
    print("  • Explore examples/education/ for learning resources")
    print("  • Read docs/GETTING_STARTED.md for detailed guide")
    print("  • Try examples/enhanced_routing_demo.py for advanced features")
    print("=" * 60)


if __name__ == "__main__":
    main()
