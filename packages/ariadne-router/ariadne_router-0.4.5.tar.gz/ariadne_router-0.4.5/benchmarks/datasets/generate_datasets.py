"""Generate benchmark dataset circuits (OpenQASM 2.0).

Requires Qiskit (already a core dependency of Ariadne).
"""

from __future__ import annotations

import math
from pathlib import Path

from qiskit import QuantumCircuit
from qiskit.circuit.library import QFT


ROOT = Path(__file__).resolve().parent


def ghz_qasm(n: int) -> str:
    qc = QuantumCircuit(n, n)
    qc.h(0)
    for i in range(1, n):
        qc.cx(0, i)
    qc.measure_all()
    return qc.qasm()


def qft_qasm(n: int) -> str:
    qc = QuantumCircuit(n, n)
    qc.append(QFT(n), range(n))
    qc.measure_all()
    return qc.qasm()


def hea_vqe_qasm(n: int, depth: int = 2) -> str:
    qc = QuantumCircuit(n, n)
    # Deterministic rotations + linear entanglement
    for d in range(depth):
        for i in range(n):
            qc.ry(0.1 * (i + 1) * (d + 1), i)
            qc.rz(0.2 * (i + 1) * (d + 1), i)
        for i in range(n - 1):
            qc.cx(i, i + 1)
    qc.measure_all()
    return qc.qasm()


def write_qasm(name: str, qasm: str) -> None:
    path = ROOT / f"{name}.qasm2"
    path.write_text(qasm)
    print(f"Wrote {path}")


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)

    # GHZ 10..50
    for n in (10, 20, 30, 40, 50):
        write_qasm(f"ghz_{n}", ghz_qasm(n))

    # QFT 10..50 (may be large for 40/50)
    for n in (10, 20, 30, 40, 50):
        write_qasm(f"qft_{n}", qft_qasm(n))

    # HEA-VQE 10..50 (depth 2)
    for n in (10, 20, 30, 40, 50):
        write_qasm(f"vqe_hea_d2_{n}", hea_vqe_qasm(n, depth=2))


if __name__ == "__main__":
    main()
