from __future__ import annotations

from _util import write_report


def main() -> None:
    from qiskit import QuantumCircuit

    from ariadne.ft.resource_estimator import estimate_circuit_resources

    # Create a simple example circuit
    qc = QuantumCircuit(3)
    qc.h(0)
    qc.cx(0, 1)
    qc.cx(1, 2)
    qc.measure_all()

    # Estimate resources
    estimate = estimate_circuit_resources(qc)

    lines = [
        "# Resource Estimates\n",
        f"Physical qubits: {estimate.physical_qubits}\n",
        f"Logical qubits: {estimate.logical_qubits}\n",
        f"T-gates: {estimate.t_gates}\n",
        f"T-gate depth: {estimate.t_gate_depth}\n",
        f"Code distance: {estimate.code_distance}\n",
        f"Runtime hours: {estimate.runtime_hours:.2f}\n",
        f"Error rate: {estimate.error_rate:.2e}\n",
    ]
    path = write_report("05_qualtran_resources", "\n".join(lines))
    print(f"Wrote report to {path}")


if __name__ == "__main__":
    main()
