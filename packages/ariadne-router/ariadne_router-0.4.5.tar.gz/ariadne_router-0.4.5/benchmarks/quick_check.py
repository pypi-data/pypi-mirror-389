#!/usr/bin/env python3
"""Quick performance check for CI/CD pipeline."""

import argparse
import sys
import time


def main():
    """Run quick performance check."""
    parser = argparse.ArgumentParser(description="Quick performance check")
    parser.add_argument("--platform", required=True, help="Platform name")
    args = parser.parse_args()

    try:
        # Import Ariadne
        from qiskit import QuantumCircuit

        from ariadne import get_available_backends, simulate

        print(f"🚀 Quick performance check on {args.platform}")
        print("=" * 50)

        # Check available backends
        backends = get_available_backends()
        print(f"✅ Available backends: {len(backends)}")
        for backend in backends:
            print(f"   - {backend}")

        # Quick simulation test
        qc = QuantumCircuit(5, 5)
        qc.h(0)
        for i in range(4):
            qc.cx(i, i + 1)
        qc.measure_all()

        start_time = time.time()
        result = simulate(qc, shots=100)
        end_time = time.time()

        print("✅ Test simulation completed:")
        print(f"   Backend: {result.backend_used}")
        print(f"   Time: {result.execution_time:.4f}s")
        print(f"   Total time: {end_time - start_time:.4f}s")

        # Performance threshold check
        if result.execution_time > 1.0:  # 1 second threshold
            print(f"⚠️  Performance warning: simulation took {result.execution_time:.4f}s")
        else:
            print("✅ Performance OK")

        print(f"🎉 Quick check passed on {args.platform}")
        return 0

    except Exception as e:
        print(f"❌ Quick check failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
