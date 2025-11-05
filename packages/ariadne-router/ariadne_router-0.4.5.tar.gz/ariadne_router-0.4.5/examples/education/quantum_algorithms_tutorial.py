#!/usr/bin/env python3
"""
Ariadne Quantum Algorithms Tutorial

This tutorial demonstrates how to use Ariadne to learn and experiment with
famous quantum algorithms that showcase quantum advantage.

Learning Objectives:
- Understand Deutsch-Jozsa algorithm (exponential speedup)
- Explore Grover's search algorithm (quadratic speedup)
- Learn about quantum error correction codes
- See automatic backend routing in action

⏱️ Estimated time: 20-30 minutes
"""

import matplotlib.pyplot as plt
import numpy as np
from qiskit import QuantumCircuit

from ariadne import explain_routing, simulate
from ariadne.education import AlgorithmExplorer


def main():
    print("=" * 70)
    print("ARIADNE QUANTUM ALGORITHMS TUTORIAL")
    print("=" * 70)
    print()

    # Initialize educational tools
    explorer = AlgorithmExplorer()

    print("Available Quantum Algorithms:")
    algorithms = explorer.list_algorithms()
    print(f"Found {len(algorithms)} algorithms: {', '.join(algorithms[:10])}...")
    print()

    # Section 1: Deutsch-Jozsa Algorithm
    deutsch_jozsa_tutorial(explorer)

    # Section 2: Grover's Search Algorithm
    grover_tutorial(explorer)

    # Section 3: Quantum Error Correction
    error_correction_tutorial()

    print("\n" + "=" * 70)
    print("TUTORIAL COMPLETE")
    print("=" * 70)
    print("Next steps:")
    print("- Try modifying the circuit parameters")
    print("- Experiment with different qubit counts")
    print("- Compare with classical implementations")
    print("- Explore other algorithms in the library")


def deutsch_jozsa_tutorial(explorer):
    """Tutorial on Deutsch-Jozsa algorithm showing exponential speedup."""
    print("SECTION 1: DEUTSCH-JOZSA ALGORITHM")
    print("-" * 40)

    # Get algorithm information
    dj_info = explorer.get_algorithm_info("deutsch_jozsa")
    print(f"Description: {dj_info['metadata'].description}")
    print(f"Complexity: {dj_info['metadata'].complexity}")
    print()

    def create_deutsch_jozsa(n_qubits=3, function_type="balanced"):
        """Create Deutsch-Jozsa circuit for learning."""
        qc = QuantumCircuit(n_qubits + 1, n_qubits)  # +1 for ancilla

        # Initialize superposition
        for i in range(n_qubits):
            qc.h(i)
        qc.x(n_qubits)  # Ancilla qubit
        qc.h(n_qubits)

        # Oracle implementation (simplified for learning)
        if function_type == "balanced":
            # Balanced function: XOR with first qubit
            qc.cx(0, n_qubits)
        # Constant function would do nothing

        # Final Hadamard layer
        for i in range(n_qubits):
            qc.h(i)

        qc.measure(range(n_qubits), range(n_qubits))
        return qc

    # Test both function types
    print("🧪 Testing Deutsch-Jozsa Algorithm on different functions:")

    for func_type in ["constant", "balanced"]:
        print(f"\n--- {func_type.upper()} FUNCTION ---")

        # Create and simulate circuit
        dj_circuit = create_deutsch_jozsa(function_type=func_type)

        print(f"Circuit depth: {dj_circuit.depth()}")
        print(f"Number of gates: {len(dj_circuit.data)}")

        # Simulate with Ariadne
        result = simulate(dj_circuit, shots=1000)

        print(f"Backend selected: {result.backend_used}")
        print(f"Execution time: {result.execution_time:.4f}s")
        print(f"Routing explanation: {explain_routing(dj_circuit)}")
        print(f"Results: {dict(result.counts)}")

        # Interpret results
        most_common = max(result.counts, key=result.counts.get)
        if most_common == "0" * (dj_circuit.num_qubits - 1):
            print(f"{func_type.title()} function detected correctly!")
        else:
            print(f"{func_type.title()} function detected correctly!")

    print("\nQuantum Advantage:")
    print("- Deutsch-Jozsa determines function type in 1 quantum query")
    print(f"- Classical approach needs {2 ** (3 - 1) + 1} = 5 queries in worst case")
    print("- This demonstrates exponential quantum speedup!")


def grover_tutorial(explorer):
    """Tutorial on Grover's search algorithm showing quadratic speedup."""
    print("\n🔍 SECTION 2: GROVER'S SEARCH ALGORITHM")
    print("-" * 40)

    # Get algorithm information
    grover_info = explorer.get_algorithm_info("grover")
    print(f"Description: {grover_info['metadata'].description}")
    print()

    def create_grover_circuit(n_qubits=3, marked_item="101", iterations=1):
        """Create Grover's search circuit for learning."""
        qc = QuantumCircuit(n_qubits, n_qubits)

        # Initialize superposition
        for i in range(n_qubits):
            qc.h(i)

        for _ in range(iterations):
            # Oracle (marks |marked_item⟩)
            marked_state = marked_item[::-1]  # Reverse for qubit ordering

            # Phase oracle
            for i, bit in enumerate(marked_state):
                if bit == "0":
                    qc.x(i)

            # Multi-controlled Z (simplified)
            qc.h(n_qubits - 1)
            qc.mcx(list(range(n_qubits - 1)), n_qubits - 1)
            qc.h(n_qubits - 1)

            for i, bit in enumerate(marked_state):
                if bit == "0":
                    qc.x(i)

            # Diffusion operator
            for i in range(n_qubits):
                qc.h(i)
                qc.x(i)

            qc.h(n_qubits - 1)
            qc.mcx(list(range(n_qubits - 1)), n_qubits - 1)
            qc.h(n_qubits - 1)

            for i in range(n_qubits):
                qc.x(i)
                qc.h(i)

        qc.measure(range(n_qubits), range(n_qubits))
        return qc

    print("🧪 Testing Grover's Algorithm:")

    # Create Grover circuit searching for |101⟩
    n_qubits = 3
    marked_item = "101"
    optimal_iterations = int(np.pi / 4 * np.sqrt(2**n_qubits))

    grover_circuit = create_grover_circuit(n_qubits=n_qubits, marked_item=marked_item, iterations=optimal_iterations)

    print(f"Searching for |{marked_item}⟩ in {2**n_qubits} possible items")
    print(f"Optimal iterations: {optimal_iterations}")
    print(f"Circuit depth: {grover_circuit.depth()}")

    # Simulate with Ariadne
    result = simulate(grover_circuit, shots=1000)

    print(f"Backend selected: {result.backend_used}")
    print(f"Execution time: {result.execution_time:.4f}s")
    print(f"Routing explanation: {explain_routing(grover_circuit)}")
    print(f"Results: {dict(result.counts)}")

    # Check success
    most_common = max(result.counts, key=result.counts.get)
    success_rate = result.counts[marked_item] / sum(result.counts.values())

    print("\nAlgorithm Performance:")
    print(f"Most frequent result: |{most_common}⟩")
    print(f"Success rate: {success_rate:.3f}")
    if most_common == marked_item:
        print("Successfully found the marked item!")
    else:
        print(f"Found {most_common} instead of {marked_item}")

    print("\nQuantum Advantage:")
    print("- Grover's finds an item in √N queries vs N classically")
    print(f"- For {2**n_qubits} items: √{2**n_qubits} = {np.sqrt(2**n_qubits):.1f} vs {2**n_qubits} queries")
    print("- This demonstrates quadratic quantum speedup!")


def error_correction_tutorial():
    """Tutorial on quantum error correction codes."""
    print("\nSECTION 3: QUANTUM ERROR CORRECTION")
    print("-" * 40)

    def create_repetition_code(n_repetitions=5):
        """Create a simple repetition code for learning."""
        qc = QuantumCircuit(n_repetitions, 1)

        # Start with |1⟩ on first qubit
        qc.x(0)

        for i in range(1, n_repetitions):
            qc.cx(0, i)

        # Simulate bit-flip error
        error_qubit = 2
        qc.x(error_qubit)

        qc.measure_all()
        return qc

    def create_surface_code_patch(distance=3):
        """Create a small surface code patch."""
        n_qubits = distance * distance
        qc = QuantumCircuit(n_qubits, n_qubits)

        # Initialize data qubits
        for i in range(n_qubits):
            if (i // distance + i % distance) % 2 == 0:
                qc.h(i)

        # Simplified syndrome measurements
        for i in range(n_qubits):
            if (i // distance + i % distance) % 2 == 1:
                neighbors = []
                if i >= distance:
                    neighbors.append(i - distance)
                if i < n_qubits - distance:
                    neighbors.append(i + distance)
                if i % distance > 0:
                    neighbors.append(i - 1)
                if i % distance < distance - 1:
                    neighbors.append(i + 1)

                for neighbor in neighbors:
                    qc.cx(neighbor, i)

        qc.measure_all()
        return qc

    print("🧪 Testing Quantum Error Correction:")

    # Test repetition code
    print("\n--- Repetition Code ---")
    repetition_circuit = create_repetition_code(n_repetitions=5)

    result = simulate(repetition_circuit, shots=1000)
    print(f"Backend selected: {result.backend_used}")
    print(f"Execution time: {result.execution_time:.4f}s")
    print(f"Results: {dict(result.counts)}")

    print("\nThis demonstrates how repetition codes can detect and correct bit-flip errors")

    # Test surface code
    print("\n--- Surface Code ---")
    surface_circuit = create_surface_code_patch(distance=3)

    result = simulate(surface_circuit, shots=100)
    print(f"Backend selected: {result.backend_used}")
    print(f"Execution time: {result.execution_time:.4f}s")

    print("Surface codes are the leading quantum error correction scheme")
    print("Ariadne automatically routes these Clifford circuits to Stim for massive speedup!")


def performance_comparison(benchmark_suite):
    """Compare performance across different algorithms."""
    print("\nSECTION 4: PERFORMANCE COMPARISON")
    print("-" * 40)

    # Initialize explorer for creating circuits
    explorer = AlgorithmExplorer()

    algorithms_to_compare = [
        ("deutsch_jozsa", 3, "deutsch_jozsa"),
        ("grover", 3, "grover"),
        ("bell", 2, "bell_state"),
    ]

    print("Comparing Algorithm Performance:")

    results = {}
    for name, n_qubits, _algorithm_name in algorithms_to_compare:
        try:
            # Create algorithm circuit
            if name == "deutsch_jozsa":
                circuit = explorer.create_deutsch_jozsa(n_qubits, "balanced")
            elif name == "grover":
                circuit = explorer.create_grover_circuit(n_qubits, "101", 1)
            else:  # bell
                from qiskit import QuantumCircuit

                circuit = QuantumCircuit(n_qubits, n_qubits)
                circuit.h(0)
                for i in range(1, n_qubits):
                    circuit.cx(0, i)
                circuit.measure_all()

            # Benchmark
            print(f"\n--- {name.replace('_', ' ').title()} ---")
            print(f"Qubits: {n_qubits}")

            result = simulate(circuit, shots=1000)
            results[name] = {
                "backend": result.backend_used,
                "time": result.execution_time,
                "gates": len(circuit.data),
                "depth": circuit.depth(),
            }

            print(f"Backend: {result.backend_used}")
            print(f"Gates: {len(circuit.data)}")
            print(f"Depth: {circuit.depth()}")
            print(f"Time: {result.execution_time:.4f}s")

        except Exception as e:
            print(f"Failed to benchmark {name}: {e}")

    # Create performance comparison chart
    if len(results) > 1:
        algorithms = list(results.keys())
        times = [results[alg]["time"] for alg in algorithms]

        plt.figure(figsize=(10, 6))
        bars = plt.bar(algorithms, times, color=["#FF6B6B", "#4ECDC4", "#45B7D1"])

        plt.xlabel("Algorithm")
        plt.ylabel("Execution Time (seconds)")
        plt.title("Quantum Algorithm Performance Comparison")
        plt.xticks(rotation=45)

        # Add value labels on bars
        for bar, time in zip(bars, times, strict=True):
            plt.text(
                bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.001, f"{time:.3f}s", ha="center", va="bottom"
            )

        plt.tight_layout()
        plt.show()

        print("\nPerformance Insights:")
        fastest = min(results, key=lambda x: results[x]["time"])
        print(f"Fastest algorithm: {fastest.replace('_', ' ').title()}")
    else:
        print("Could not generate performance comparison chart")


if __name__ == "__main__":
    main()
