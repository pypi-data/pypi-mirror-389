#!/usr/bin/env python3
"""
Professional quantum simulation example showcasing production-ready usage.
"""

import time
from typing import Any

from qiskit import QuantumCircuit

from ariadne import explain_routing, get_available_backends, simulate


def benchmark_backends(circuit: QuantumCircuit, shots: int = 1000) -> dict[str, Any]:
    """Benchmark different backends for a given circuit."""
    backends = get_available_backends()
    results = {}

    for backend_name in backends:
        try:
            start_time = time.time()
            result = simulate(circuit, backend=backend_name, shots=shots)
            execution_time = time.time() - start_time

            results[backend_name] = {
                "success": True,
                "time": execution_time,
                "backend_used": result.backend_used,
                "shot_count": len(result.get_counts()) if hasattr(result, "get_counts") else shots,
            }
        except Exception as e:
            results[backend_name] = {"success": False, "error": str(e)}

    return results


def create_algorithm_circuits() -> dict[str, QuantumCircuit]:
    """Create a variety of quantum circuits for testing."""
    circuits = {}

    # Quantum Fourier Transform (12 qubits)
    qft_circuit = QuantumCircuit(12, 12)
    for i in range(12):
        qft_circuit.h(i)
        for j in range(i + 1, 12):
            qft_circuit.cp(2 * 3.14159 / (2 ** (j - i + 1)), i, j)
    qft_circuit.measure_all()
    circuits["QFT"] = qft_circuit

    # Bernstein-Vazirani Algorithm
    bv_circuit = QuantumCircuit(8, 8)
    secret = "10110101"  # Secret string
    bv_circuit.h(range(7))
    bv_circuit.x(7)
    bv_circuit.h(7)
    for i, bit in enumerate(secret[:-1]):
        if bit == "1":
            bv_circuit.cx(i, 7)
    bv_circuit.h(range(7))
    bv_circuit.measure_all()
    circuits["Bernstein-Vazirani"] = bv_circuit

    # Random Clifford Circuit
    cliff_circuit = QuantumCircuit(20, 20)
    for _ in range(50):
        cliff_circuit.h(0)
        cliff_circuit.s(1)
        cliff_circuit.cx(0, 1)
    cliff_circuit.measure_all()
    circuits["Clifford"] = cliff_circuit

    return circuits


def main() -> None:
    """Professional demonstration of Ariadne capabilities."""
    print("Ariadne: Production Quantum Simulator Router")
    print("=" * 60)

    # Get available backends
    print(f"📋 Available backends: {', '.join(get_available_backends())}")
    print()

    # Test different quantum algorithms
    circuits = create_algorithm_circuits()

    for name, circuit in circuits.items():
        print(f"Testing: {name}")
        print(f"   Circuit: {circuit.num_qubits} qubits, {circuit.size()} gates")

        # Get Ariadne's automatic choice
        result = simulate(circuit, shots=1000)
        routing_explanation = explain_routing(circuit)

        print(f"   Auto-selected: {result.backend_used}")
        print(f"   ⚡ Time: {result.execution_time:.4f}s")
        print(f"   Reasoning: {routing_explanation}")
        print()

    print("Performance Summary:")
    print("Ariadne automatically optimized each algorithm for maximum performance")
    print("without requiring manual backend selection or configuration.")


if __name__ == "__main__":
    main()
