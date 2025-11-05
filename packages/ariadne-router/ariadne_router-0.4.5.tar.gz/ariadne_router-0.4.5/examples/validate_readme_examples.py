#!/usr/bin/env python3
"""
README Example Validator

This script validates that all the code examples in the README actually work.
Run this to ensure the README examples are always accurate.
"""

import sys

from qiskit import QuantumCircuit


def test_30_second_demo():
    """Test the 30-second demo from the README."""
    print("Testing 30-second demo...")

    try:
        from ariadne import explain_routing, simulate

        # 40-qubit GHZ (stabilizer circuit)
        qc = QuantumCircuit(40, 40)
        qc.h(0)
        [qc.cx(i, i + 1) for i in range(39)]
        qc.measure_all()

        result = simulate(qc, shots=1000)
        print(f"Backend: {result.backend_used}")
        print(f"Time: {result.execution_time:.3f}s")

        explanation = explain_routing(qc)
        print(f"Explanation: {explanation[:100]}...")

        return True

    except Exception as e:
        print(f"30-second demo failed: {e}")
        return False


def test_first_simulation():
    """Test the first simulation example."""
    print("\nTesting first simulation example...")

    try:
        from ariadne import simulate

        # Create any circuit - Ariadne handles backend selection
        qc = QuantumCircuit(20, 20)
        qc.h(range(10))
        for i in range(9):
            qc.cx(i, i + 1)
        qc.measure_all()

        # Single call handles all backend complexity
        result = simulate(qc, shots=1000)
        print(f"Backend used: {result.backend_used}")
        print(f"Execution time: {result.execution_time:.4f}s")
        print(f"Unique outcomes: {len(result.counts)}")

        return True

    except Exception as e:
        print(f"First simulation failed: {e}")
        return False


def test_transparent_decisions():
    """Test the transparent decision making example."""
    print("\nTesting transparent decision making...")

    try:
        from ariadne import explain_routing, show_routing_tree

        # Create a circuit
        qc = QuantumCircuit(2, 2)
        qc.h(0)
        qc.cx(0, 1)
        qc.measure_all()

        # Get detailed routing explanation
        explanation = explain_routing(qc)
        print(f"Explanation available: {len(explanation) > 0}")

        # Visualize the routing tree
        tree = show_routing_tree()
        print(f"Routing tree available: {len(tree) > 0}")

        return True

    except Exception as e:
        print(f"Transparent decisions failed: {e}")
        return False


def test_core_api():
    """Test the core API examples."""
    print("\nTesting core API...")

    try:
        from qiskit import QuantumCircuit

        from ariadne import ComprehensiveRoutingTree, EnhancedQuantumRouter, simulate

        circuit = QuantumCircuit(2, 2)
        circuit.h(0)
        circuit.cx(0, 1)
        circuit.measure_all()

        # Test simulate function
        result = simulate(circuit, shots=1000)
        print(f"simulate() works: {result.backend_used}")

        # Test EnhancedQuantumRouter
        router = EnhancedQuantumRouter()
        decision = router.select_optimal_backend(circuit)
        print(f"EnhancedQuantumRouter works: {decision.recommended_backend}")

        # Test ComprehensiveRoutingTree
        tree = ComprehensiveRoutingTree()
        decision = tree.route_circuit(circuit)
        print(f"ComprehensiveRoutingTree works: {decision.recommended_backend}")

        return True

    except Exception as e:
        print(f"Core API failed: {e}")
        return False


def main():
    """Run all README example validations."""
    print("Validating README Examples")
    print("=" * 50)

    tests = [
        test_30_second_demo,
        test_first_simulation,
        test_transparent_decisions,
        test_core_api,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"Test {test.__name__} crashed: {e}")
            failed += 1

    print("\n" + "=" * 50)
    print(f"Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("All README examples work correctly.")
        return 0
    else:
        print("Some README examples need fixing")
        return 1


if __name__ == "__main__":
    sys.exit(main())
