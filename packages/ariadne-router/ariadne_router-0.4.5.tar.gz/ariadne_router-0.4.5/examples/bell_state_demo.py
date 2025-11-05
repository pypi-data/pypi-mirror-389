#!/usr/bin/env python3
"""Example: Bell state creation and measurement with Ariadne."""

from qiskit import QuantumCircuit

from ariadne import simulate


def main():
    """Demonstrate Bell state creation and measurement."""
    print("Ariadne Bell State Demo")
    print("=" * 30)

    # Create Bell state |Φ+⟩ = (|00⟩ + |11⟩)/√2
    qc = QuantumCircuit(2, 2)
    qc.h(0)  # Create superposition
    qc.cx(0, 1)  # Entangle qubits
    qc.measure_all()

    print("Bell state circuit:")
    print(qc.draw(output="text"))

    # Simulate with Ariadne
    result = simulate(qc, shots=1000)

    print(f"\nBackend used: {result.backend_used}")
    print(f"Execution time: {result.execution_time:.4f}s")
    print(f"Circuit entropy: {result.routing_decision.circuit_entropy:.3f}")

    print("\nMeasurement results:")
    for state, count in sorted(result.counts.items()):
        print(f"  {state}: {count}")

    # Verify Bell state properties
    total = sum(result.counts.values())

    # The measurement results are in 4-bit format (e.g., "0000", "1100")
    # For a 2-qubit Bell state measured with measure_all(),
    # the format is: q0, q1, c0, c1 (or with padding)
    # We need to extract the first 2 bits for the 2-qubit measurement
    prob_00 = 0
    prob_11 = 0
    for state, count in result.counts.items():
        # Extract the first 2 bits for 2-qubit measurement
        if len(state) >= 2:
            first_two_bits = state[:2]
            if first_two_bits == "00":
                prob_00 += count / total
            elif first_two_bits == "11":
                prob_11 += count / total

    print("\nBell state verification:")
    print(f"  P(00): {prob_00:.3f} (expected: ~0.5)")
    print(f"  P(11): {prob_11:.3f} (expected: ~0.5)")
    print(f"  P(01) + P(10): {1 - prob_00 - prob_11:.3f} (expected: ~0.0)")


if __name__ == "__main__":
    main()
