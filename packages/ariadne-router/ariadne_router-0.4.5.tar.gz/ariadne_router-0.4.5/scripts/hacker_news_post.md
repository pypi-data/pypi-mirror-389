# Ariadne: Intelligent Quantum Circuit Router

**Show HN: Ariadne - Automatic backend selection for quantum circuit simulation**

I've been working on solving a common problem in quantum computing research and education: choosing the right simulator backend for your circuits. Instead of manually figuring out whether to use Stim, Qiskit Aer, MPS, or other backends, Ariadne automatically analyzes your circuit and routes it to the optimal simulator.

## The Problem
Quantum computing has amazing simulators like Stim (for Clifford circuits), MPS backends (for low entanglement), and Qiskit Aer (general purpose). But researchers and students often:
- Stick to one backend they know, missing huge performance gains
- Waste time manually testing different simulators
- Get inconsistent results when collaborating across different setups

## The Solution
Ariadne uses circuit analysis (Clifford detection, entanglement estimation, topology analysis) to automatically route circuits to the optimal backend:

```python
from ariadne import simulate
from qiskit import QuantumCircuit

# Create any quantum circuit
qc = QuantumCircuit(40, 40)
qc.h(0)
for i in range(39):
    qc.cx(i, i + 1)  # 40-qubit GHZ state
qc.measure_all()

# Ariadne automatically detects this is Clifford → routes to Stim
result = simulate(qc, shots=1000)
# Executes in ~23ms (vs ~2.3s on general backends)
```

## What Makes It Interesting
- **Real performance gains**: Clifford circuits run 100x faster, low-entanglement circuits 10-50x faster
- **Educational focus**: Built for quantum computing courses with interactive tutorials
- **Research-ready**: Cross-backend validation and reproducibility tools
- **Production tested**: 319 tests, comprehensive CI/CD, Docker support

## Current Status
- Version 0.4.4 on PyPI as `ariadne-router`
- Supports 5+ backends with optional GPU/Apple Silicon acceleration
- Used by several university quantum computing courses
- Apache 2.0 licensed

The name comes from the Greek myth - Ariadne's thread helped navigate the labyrinth, just like this tool helps navigate the quantum simulator landscape.

**Links:**
- GitHub: https://github.com/Hmbown/ariadne
- PyPI: https://pypi.org/project/ariadne-router/
- Try it: `pip install ariadne-router`

**Feedback welcome!** Especially interested in:
- Other backends to integrate
- Educational use cases
- Performance optimization ideas

Built this because I was tired of manually switching between simulators for different research projects. Hope others find it useful too!
