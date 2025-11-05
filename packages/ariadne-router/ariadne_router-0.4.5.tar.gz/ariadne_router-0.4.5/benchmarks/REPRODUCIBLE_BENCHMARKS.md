# Ariadne Reproducible Benchmarks

*Generated automatically for Hacker News post validation*

## Performance Results

| Circuit | Qubits | Depth | Backend Selected | Time (s) | Circuit Type |
|---------|--------|-------|------------------|----------|-------------|
| 20-qubit Clifford GHZ | 20 | 21 | BackendType.STIM | 0.0495 | Clifford |
| 15-qubit low-entanglement | 15 | 3 | BackendType.STIM | 0.0023 | Low entanglement |
| 12-qubit random circuit | 12 | 9 | BackendType.MPS | 1.4531 | General |


## Reproduction Commands

```bash
# Install dependencies
pip install ariadne-router qiskit

# Run benchmark script
python benchmarks/create_benchmark_table.py

# Or run individual circuits:
python -c "
from ariadne import simulate
from qiskit import QuantumCircuit

# 20-qubit Clifford GHZ
qc = QuantumCircuit(20, 20)
qc.h(0)
for i in range(19): qc.cx(i, i+1)
qc.measure_all()
result = simulate(qc, shots=1000)
print(f'GHZ: {result.backend_used}, {result.execution_time:.4f}s')
"
```

## Notes

- All benchmarks run with 1000 shots for consistency
- Times include routing decision overhead (~1ms)
- Results may vary by hardware and available backends
- Clifford circuits show largest performance differences
