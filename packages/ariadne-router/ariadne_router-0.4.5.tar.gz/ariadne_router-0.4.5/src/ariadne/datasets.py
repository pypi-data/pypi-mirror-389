"""Dataset generation utilities for benchmark circuits.

This module centralizes generation of standard circuits (GHZ, QFT,
hardware-efficient ansatz) and writes OpenQASM 2.0 files to a datasets
directory. It is used by the CLI `ariadne datasets generate`.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from pathlib import Path

from qiskit import QuantumCircuit
from qiskit.circuit.library import QFTGate

DEFAULT_SIZES: tuple[int, ...] = (10, 20, 30, 40, 50)


def resolve_datasets_dir(output_dir: str | Path | None = None) -> Path:
    """Resolve the directory for dataset files.

    Preference order:
    1) Explicit `output_dir` if provided
    2) `benchmarks/datasets` under current working directory
    3) `~/.ariadne/datasets`
    """
    if output_dir is not None:
        out = Path(output_dir).expanduser().resolve()
        out.mkdir(parents=True, exist_ok=True)
        return out

    cwd = Path.cwd()
    repo_dir = cwd / "benchmarks" / "datasets"
    try:
        repo_dir.mkdir(parents=True, exist_ok=True)
        return repo_dir
    except Exception:
        pass

    home_dir = Path.home() / ".ariadne" / "datasets"
    home_dir.mkdir(parents=True, exist_ok=True)
    return home_dir


def ghz_circuit(n: int) -> QuantumCircuit:
    qc = QuantumCircuit(n, n)
    qc.h(0)
    for i in range(1, n):
        qc.cx(0, i)
    qc.measure_all()
    return qc


def qft_circuit(n: int) -> QuantumCircuit:
    qc = QuantumCircuit(n, n)
    qc.append(QFTGate(num_qubits=n), range(n))
    qc.measure_all()
    return qc


def vqe_hea_circuit(n: int, depth: int = 2) -> QuantumCircuit:
    qc = QuantumCircuit(n, n)
    for d in range(depth):
        for i in range(n):
            qc.ry(0.1 * (i + 1) * (d + 1), i)
            qc.rz(0.2 * (i + 1) * (d + 1), i)
        for i in range(n - 1):
            qc.cx(i, i + 1)
    qc.measure_all()
    return qc


def write_qasm(qc: QuantumCircuit, name: str, directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{name}.qasm2"
    path.write_text(qc.qasm())
    return path


def generate_datasets(
    families: Iterable[str],
    sizes: Sequence[int] = DEFAULT_SIZES,
    *,
    depth: int = 2,
    output_dir: str | Path | None = None,
) -> list[Path]:
    """Generate datasets and return written file paths.

    families: subset of {"ghz", "qft", "vqe_hea", "all"}
    sizes: qubit counts to generate
    depth: VQE HEA depth (ignored for GHZ/QFT)
    output_dir: directory to write files (resolved by `resolve_datasets_dir`)
    """
    fams = {f.lower() for f in families}
    if "all" in fams:
        fams = {"ghz", "qft", "vqe_hea"}

    out_dir = resolve_datasets_dir(output_dir)
    written: list[Path] = []

    if "ghz" in fams:
        for n in sizes:
            qc = ghz_circuit(n)
            written.append(write_qasm(qc, f"ghz_{n}", out_dir))

    if "qft" in fams:
        for n in sizes:
            qc = qft_circuit(n)
            written.append(write_qasm(qc, f"qft_{n}", out_dir))

    if "vqe_hea" in fams:
        for n in sizes:
            qc = vqe_hea_circuit(n, depth=depth)
            written.append(write_qasm(qc, f"vqe_hea_d{depth}_{n}", out_dir))

    return written


__all__ = [
    "DEFAULT_SIZES",
    "generate_datasets",
    "resolve_datasets_dir",
    "ghz_circuit",
    "qft_circuit",
    "vqe_hea_circuit",
]
