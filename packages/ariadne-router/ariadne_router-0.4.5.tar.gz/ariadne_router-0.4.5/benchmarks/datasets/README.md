Benchmark Datasets
===================

This directory contains pre-generated, reproducible quantum circuits used for
cross-backend benchmarking and validation. Circuits are provided in OpenQASM 2.0
format for maximum compatibility across tools.

Included families (pre-generated)
- GHZ: 10–50 qubits in steps of 10 (star-entanglement with global measurement)
- QFT: 10 and 20 qubits (full exact), 30/40/50 qubits (approximate, truncated phases)
- VQE-HEA: Hardware-efficient ansatz (depth 2) for 10–50 qubits

Generate more circuits
- Use `generate_datasets.py` or the CLI below to produce additional sizes
  deterministically (e.g., QFT 30/40/50) and deeper HEA variants.

Usage tips
- Load with Qiskit: `QuantumCircuit.from_qasm_file('path/to/file.qasm2')`
- Validate across backends with `ariadne.reproducibility.cross_validate(...)`

CLI helpers
- List datasets: `python -m ariadne datasets list`
- Generate all families/sizes: `python -m ariadne datasets generate --family all --sizes 10,20,30,40,50`
- Generate QFT only to home dir: `python -m ariadne datasets generate --family qft --output-dir ~/.ariadne/datasets`
