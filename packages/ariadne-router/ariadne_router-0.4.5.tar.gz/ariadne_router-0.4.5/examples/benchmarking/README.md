Benchmark Suite

Generate reproducible, cross‑simulator benchmark reports. The CLI wrapper uses `export_benchmark_report` under the hood and writes JSON suitable for citation and trend analysis.

Example:

```bash
ariadne benchmark-suite \
  --algorithms bell,ghz,qaoa,vqe \
  --backends auto,stim,qiskit,mps \
  --shots 1000 \
  --output benchmark_results.json
```

Programmatic use:

```python
from ariadne.benchmarking import export_benchmark_report

report = export_benchmark_report(
    algorithms=["bell", "ghz", "qaoa", "vqe"],
    backends=["auto", "stim", "qiskit", "mps"],
    shots=1000,
)
```
