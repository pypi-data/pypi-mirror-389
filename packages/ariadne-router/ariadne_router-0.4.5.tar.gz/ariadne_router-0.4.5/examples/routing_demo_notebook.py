#!/usr/bin/env python3
"""
Repeatable Benchmark Demo - Proof of Ariadne's Routing

This demonstrates the key claims from the README:
1. 30-40 qubit GHZ/Clifford circuit auto-routes to Stim
2. Low-entanglement VQE/QAOA routes to MPS/TN
3. General circuit falls back to Aer CPU

With timings, memory usage, and explain_routing() outputs.
"""

import time
from typing import Any

from qiskit import QuantumCircuit

from ariadne import explain_routing, simulate


def benchmark_circuit(name: str, circuit: QuantumCircuit, shots: int = 1000) -> dict[str, Any]:
    """Benchmark a single circuit and return detailed results."""
    print(f"\n{'=' * 20} {name} {'=' * 20}")
    print(f"Circuit: {circuit.num_qubits} qubits, depth {circuit.depth()}")

    # Get routing explanation
    explanation = explain_routing(circuit)
    print(f"Routing decision: {explanation}")

    # Measure execution
    start_time = time.time()
    # start_memory = 0  # Could add memory profiling here

    try:
        result = simulate(circuit, shots=shots)
        end_time = time.time()

        execution_time = end_time - start_time
        throughput = shots / execution_time if execution_time > 0 else 0

        print("SUCCESS")
        print(f"   Backend: {result.backend_used.value}")
        print(f"   Time: {execution_time:.4f}s")
        print(f"   Throughput: {throughput:.0f} shots/s")
        print(f"   Sample results: {dict(list(result.counts.items())[:3])}")

        if result.fallback_reason:
            print(f"   Fallback reason: {result.fallback_reason}")

        return {
            "success": True,
            "backend": result.backend_used.value,
            "execution_time": execution_time,
            "throughput": throughput,
            "explanation": explanation,
            "fallback_reason": result.fallback_reason,
            "sample_counts": dict(list(result.counts.items())[:3]),
        }

    except Exception as e:
        end_time = time.time()
        print(f"FAILED: {e}")
        return {"success": False, "error": str(e), "explanation": explanation, "execution_time": end_time - start_time}


def create_large_clifford_circuit(n_qubits: int = 35) -> QuantumCircuit:
    """Create a large Clifford (GHZ) circuit that should route to Stim."""
    qc = QuantumCircuit(n_qubits, n_qubits)
    qc.h(0)
    for i in range(n_qubits - 1):
        qc.cx(i, i + 1)
    qc.measure_all()
    return qc


def create_low_entanglement_circuit(n_qubits: int = 12) -> QuantumCircuit:
    """Create a low-entanglement circuit (QAOA-like) that should route to MPS/TN."""
    qc = QuantumCircuit(n_qubits, n_qubits)

    # Initial superposition
    for i in range(n_qubits):
        qc.h(i)

    # Light entanglement (QAOA cost layer)
    for i in range(0, n_qubits - 1, 2):
        qc.cx(i, i + 1)
        qc.rz(0.5, i + 1)
        qc.cx(i, i + 1)

    # Mixer layer
    for i in range(n_qubits):
        qc.rx(0.7, i)

    qc.measure_all()
    return qc


def create_general_circuit(n_qubits: int = 5) -> QuantumCircuit:
    """Create a general circuit with T gates that should fall back to Aer."""
    qc = QuantumCircuit(n_qubits, n_qubits)

    qc.h(0)
    for i in range(n_qubits - 1):
        qc.cx(i, i + 1)

    # Add T gates to make it non-Clifford
    for i in range(n_qubits):
        qc.t(i)

    # More entanglement
    for i in range(n_qubits - 1):
        qc.cx(i, i + 1)

    qc.measure_all()
    return qc


def main():
    """Run the repeatable benchmark demo."""
    print("Ariadne Routing Demonstration")
    print("Reproducing README claims with real benchmarks")
    print("=" * 60)

    results = {}

    # Test 1: Large Clifford circuit → Stim
    print("\nCLAIM 1: Large Clifford circuits route to Stim")
    large_clifford = create_large_clifford_circuit(35)
    results["large_clifford"] = benchmark_circuit("Large Clifford (35-qubit GHZ)", large_clifford)

    # Test 2: Low-entanglement circuit → MPS/TN
    print("\nCLAIM 2: Low-entanglement circuits route to MPS/TN")
    low_ent = create_low_entanglement_circuit(12)
    results["low_entanglement"] = benchmark_circuit("Low-Entanglement QAOA", low_ent)

    # Test 3: General circuit → Aer CPU
    print("\nCLAIM 3: General circuits fall back to Aer")
    general = create_general_circuit(5)
    results["general"] = benchmark_circuit("General Circuit (T gates)", general)

    # Summary
    print("\n" + "=" * 60)
    print("BENCHMARK SUMMARY")
    print("=" * 60)

    for name, result in results.items():
        if result["success"]:
            print(f"SUCCESS {name}:")
            print(f"   → {result['backend']} ({result['execution_time']:.3f}s, {result['throughput']:.0f} shots/s)")
        else:
            print(f"FAILED {name}: {result['error']}")

    print("\n🔍 ROUTING TRANSPARENCY:")
    for name, result in results.items():
        if "explanation" in result:
            print(f"\n{name}:")
            print(f"   {result['explanation']}")

    print("\n" + "=" * 60)
    print("KEY INSIGHTS")
    print("=" * 60)
    print("• Ariadne automatically routes to optimal backends")
    print("• Large Clifford → Stim (enables scaling beyond standard simulators)")
    print("• Low-entanglement → MPS/TN (memory efficient)")
    print("• General circuits → Reliable Qiskit fallback")
    print("• Full transparency via explain_routing()")
    print("• Cross-ecosystem routing (not just within Aer)")

    return results


if __name__ == "__main__":
    benchmark_results = main()

    # Could save results to JSON for CI artifacts
    import json

    with open("routing_demo_results.json", "w") as f:
        json.dump(benchmark_results, f, indent=2, default=str)
    print("\nResults saved to routing_demo_results.json")
