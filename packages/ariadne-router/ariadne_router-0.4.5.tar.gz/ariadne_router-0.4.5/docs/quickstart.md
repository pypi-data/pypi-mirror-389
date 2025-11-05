# Ariadne Quick Start Guide

Get up and running with Ariadne in five minutes. This guide walks you through installation, your first routed simulation, and the core resources to explore next.

## 1. Install Ariadne

### Prerequisites
- Python 3.11 or higher
- `pip` package manager

### Install from PyPI (recommended)
```bash
pip install --upgrade ariadne-router
```

### Install from source (latest development build)
```bash
git clone https://github.com/Hmbown/ariadne.git
cd ariadne
pip install -e .
```

### Optional extras
```bash
# Apple Silicon acceleration (JAX + Metal)
pip install --upgrade ariadne-router[apple]

# NVIDIA GPU acceleration (CUDA)
pip install --upgrade ariadne-router[cuda]

# Visualization utilities (matplotlib, seaborn, plotly)
pip install --upgrade ariadne-router[viz]
```

> **Tip:** Contributors should install with `pip install -e .[dev]` to fetch the full tooling stack.

---

## 2. Run Your First Routed Simulation

Ariadne analyzes your circuit in milliseconds and selects the optimal backend automatically.

```python
from ariadne import explain_routing, simulate
from qiskit import QuantumCircuit

# 12-qubit chain with light entanglement
qc = QuantumCircuit(12, 12)
qc.h(range(12))
for i in range(0, 12, 2):
    qc.cx(i, (i + 1) % 12)
qc.measure_all()

result = simulate(qc, shots=1000)

print(f"Backend used: {result.backend_used.value}")
print(f"Execution time: {result.execution_time:.4f}s")
print("Routing explanation:", explain_routing(qc))
```

---

## 3. Understand Specialized Routing

### Clifford circuits → Stim

```python
from ariadne import simulate
from qiskit import QuantumCircuit

ghz = QuantumCircuit(40, 40)
ghz.h(0)
for i in range(39):
    ghz.cx(i, i + 1)
ghz.measure_all()

stim_result = simulate(ghz, shots=1000)
print(f"Clifford backend: {stim_result.backend_used.value}")  # -> stim
```

### Low-entanglement circuits → MPS

```python
from ariadne import simulate
from qiskit import QuantumCircuit
import numpy as np

low_ent = QuantumCircuit(25, 25)
low_ent.h(range(25))
for i in range(0, 25, 2):
    low_ent.ry(np.pi / 8, i)  # Break Clifford structure without raising depth
for i in range(0, 24, 2):
    low_ent.cx(i, i + 1)
low_ent.measure_all()

mps_result = simulate(low_ent, shots=100)
print(f"Low entanglement backend: {mps_result.backend_used.value}")  # -> mps
```

---

## 4. Explore More Circuit Inputs

Ariadne supports multiple circuit formats:

- **Qiskit `QuantumCircuit` instances** (most common)
- **OpenQASM 2/3 strings**
- **Python callables returning circuits**
- **JSON payloads via the CLI**

```python
from ariadne import simulate

OPENQASM_PROGRAM = \"\"\"\nOPENQASM 3.0;\nqubit[5] q;\nbit[5] c;\nh q[0];\ncx q[0], q[1];\nmeasure q -> c;\n\"\"\"\n\nqasm_result = simulate(OPENQASM_PROGRAM, shots=256)\nprint(qasm_result.backend_used.value)\n```

---

## 5. What to Read Next

- [Routing Decisions](router_decisions.md) — dissect the prioritized filter chain and confidence scoring.
- [Examples Gallery](../examples/README.md) — notebooks and scripts for education, benchmarking, and production use.
- [Performance Guide](PERFORMANCE_GUIDE.md) — squeeze more speed out of each backend.
- [Capability Matrix](capability_matrix.md) — compare bundled simulators at a glance.

---

## Need Help?

- Consult the [Troubleshooting Guide](troubleshooting.md) for quick fixes.
- File issues and feature requests on [GitHub](https://github.com/Hmbown/ariadne/issues).

---

*Welcome to Ariadne — the intelligent quantum router built for research, education, and production.*
