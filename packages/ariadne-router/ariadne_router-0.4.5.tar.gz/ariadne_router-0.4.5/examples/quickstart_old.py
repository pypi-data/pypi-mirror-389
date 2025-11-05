#!/usr/bin/env python3
"""
Ariadne Quickstart Example

This example demonstrates Ariadne's intelligent routing capabilities
with a practical quantum algorithm simulation.
"""

from qiskit import QuantumCircuit

from ariadne import explain_routing, simulate


def create_ghz_circuit(n_qubits: int) -> QuantumCircuit:
    """Create a GHZ (Greenberger-Horne-Zeilinger) state circuit.

    This creates a maximally entangled state that is particularly
    efficient to simulate with Clifford simulators like Stim.
    """
    qc = QuantumCircuit(n_qubits, n_qubits)
    qc.h(0)  # Put first qubit in superposition
    for i in range(n_qubits - 1):
        qc.cx(i, i + 1)  # Entangle all qubits
    qc.measure_all()  # Measure all qubits
    return qc


def main() -> None:
    """Demonstrate Ariadne's automatic backend selection."""
    print("🌟 Ariadne: Intelligent Quantum Simulator Router")
    print("=" * 50)

    # Example 1: Large Clifford circuit (optimal for Stim)
    print("\nExample 1: 40-qubit GHZ Circuit")
    print("-" * 30)

    ghz_circuit = create_ghz_circuit(40)
    print(f"Circuit: {ghz_circuit.num_qubits} qubits, {ghz_circuit.size()} gates")

    # Simulate with Ariadne's automatic routing
    result = simulate(ghz_circuit, shots=1000)

    print(f"Backend selected: {result.backend_used}")
    print(f"⚡ Execution time: {result.execution_time:.4f}s")
    print(f"🔍 Why this backend: {explain_routing(ghz_circuit)}")

    # Example 2: Small general circuit
    print("\nExample 2: Small General Circuit")
    print("-" * 30)

    small_circuit = QuantumCircuit(3, 3)
    small_circuit.h(0)
    small_circuit.ry(0.5, 1)  # Non-Clifford gate
    small_circuit.cx(0, 1)
    small_circuit.cx(1, 2)
    small_circuit.measure_all()

    result2 = simulate(small_circuit, shots=1000)

    print(f"Backend selected: {result2.backend_used}")
    print(f"⚡ Execution time: {result2.execution_time:.4f}s")
    print(f"🔍 Why this backend: {explain_routing(small_circuit)}")

    print("\n" + "=" * 50)
    print("Key Takeaway:")
    print("Ariadne automatically chose different backends for different")
    print("circuit types, optimizing performance without any user configuration!")

    print("\nNext Steps:")
    print("• Check out docs/README.md for advanced features")
    print("• Try your own circuits with simulate(your_circuit)")
    print("• Explore different backends with backend='stim' parameter")


if __name__ == "__main__":
    main()
