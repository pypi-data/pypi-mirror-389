# Show HN: Ariadne — Routes quantum circuits to the fastest simulator automatically

**URL:** https://github.com/Hmbown/ariadne

Ariadne analyzes quantum circuits and auto-selects an appropriate simulator (Clifford → Stim; low-entanglement → MPS; general circuits → Aer/GPU). The goal is to remove the "which backend should I use?" decision while keeping results reproducible.

**One call:**
```python
from ariadne import simulate
result = simulate(qc, shots=1000)  # reports backend + timing
```

**How routing works:** Circuit type detection (Clifford analysis), topology/entanglement heuristics, resource estimation, and hardware detection (Metal/CUDA when present).

**Reproducible benchmarks:**

| Circuit | Qubits | Depth | Backend Selected | Time (s) | Circuit Type |
|---------|--------|-------|------------------|----------|-------------|
| 20-qubit Clifford GHZ | 20 | 21 | stim | 0.0191 | Clifford |
| 15-qubit low-entanglement | 15 | 3 | stim | 0.0015 | Low entanglement |
| 12-qubit random circuit | 12 | 9 | mps | 2.1946 | General |

**Reproduce:** `make bench` or `python benchmarks/create_benchmark_table.py`

**What I'd love feedback on:**
1. Are the routing heuristics sensible for your workloads?
2. Missing backends you care about (DDSIM/Qulacs/Braket)?
3. Where should the "explain my routing" output be most useful?

**Scope/limitations:** Not a replacement if you need fine-grained simulator controls. Best for learning, teaching, and research where "fast enough" routing beats manual optimization.

**Install:** `pip install ariadne-router` (imports as `ariadne`; conflicts with GraphQL Ariadne—use separate venvs if needed)

The project includes cross-backend validation tools, algorithm library for teaching, and benchmarking for reproducible research.
