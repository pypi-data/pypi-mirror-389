# Notebook Expansion Plan

This document captures the Phase 3 notebook roadmap and the automation guardrails that will keep the examples reproducible.

## Planned Notebooks

| Notebook | Working Title | Objective | Key Assets | Status |
| --- | --- | --- | --- | --- |
| `03_vqe_ground_state.ipynb` | Variational Ground State Estimation | Demonstrate how Ariadne routes VQE subroutines across tensor networks, MPS, and CUDA backends. | `ariadne.algorithms.vqe`, small molecular Hamiltonians from `pyscf` (optional). | Outline complete — implementation pending. |
| `04_qaoa_maxcut.ipynb` | QAOA on Graph Instances | Show routing choices and hybrid execution for QAOA layers on random and structured graphs. | `networkx` graph generators, `ariadne.algorithms.qaoa`. | Needs circuit templates and benchmarking harness. |
| `05_error_correction_surface_code.ipynb` | Stabilizer Error Correction | Highlight Stim integration and error decoding workflows for surface codes. | `ariadne.algorithms.error_correction`, Stim noise channels. | Research spikes captured, notebook not started. |
| `06_backend_performance_comparison.ipynb` | Backend Performance Playbook | Compare execution time and accuracy across Qiskit, Stim, Tensor Network, CUDA, and Metal backends for representative workloads. | Benchmark datasets in `benchmarks/`, builtin performance monitors. | Wireframe authored; awaiting measurement cells. |

## Automated Execution Checks

To prevent notebook drift we will add the following automation:

1. **Local make target**: `make notebooks-test` will invoke `pytest --nbmake notebooks/*.ipynb` with `--nbmake-timeout=900` (15 minutes) and `--nbmake-kernel=python3`.
2. **CI integration**: a new GitHub Actions job (scheduled weekly to avoid PR slowdowns) will run the make target on Ubuntu using a minimal dependency set (`pip install -e .[dev,viz] nbmake`). Artifacts will include the executed notebooks to aid debugging.
3. **Result caching**: performance-heavy notebooks will persist intermediate CSV/JSON outputs under `reports/notebooks/` with timestamps so that re-runs can compare against previous benchmarks.
4. **Slow notebook opt-out**: each notebook will expose a top-level metadata flag (`{"ariadne": {"allow_ci": true}}`). The nbmake hook will respect this and skip notebooks flagged as `false` unless the CI job is manually triggered.

### Triage Workflow

When the nbmake step fails:

1. Download the executed notebook artifact and search for the first error cell.
2. Re-run locally with `pytest --nbmake notebooks/<name>.ipynb -k "<cell-id>"` to iterate quickly.
3. If failures are performance-related, compare the cached reports to confirm the regression and adjust baseline cells in `06_backend_performance_comparison.ipynb`.
4. Document fixes (or justified skips) in the notebook header so future runs remain self-explanatory.

This plan gives us an actionable backlog for the notebook suite while ensuring CI automation will catch regressions once the notebooks land.
