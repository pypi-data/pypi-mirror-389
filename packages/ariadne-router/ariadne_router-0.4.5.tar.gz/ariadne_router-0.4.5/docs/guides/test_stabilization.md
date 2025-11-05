# Test Suite Stabilization Guide for Ariadne

This guide implements Phase 1, Task 2 of the 6-month roadmap: Stabilizing the test suite to achieve >60% coverage, fix flakiness, and add quantum-specific tests. Current state: 23 test files (~38% coverage), flakiness in performance tests, missing GHZ/error correction coverage.

Follow these steps to update `tests/` and integrate with CI. Effort: 2 weeks. Tools: pytest-cov, pytest-xdist, tox.

## Prerequisites
- Pinned dependencies (from `docs/guides/pin_dependencies.md`).
- Install dev extras: `pip install -e .[dev]`.

## Step 1: Audit Existing Tests (Week 1, Day 1-2)
Run coverage baseline:
```bash
pytest tests/ --cov=src/ariadne --cov-report=html --cov-report=term-missing
```
- Review `htmlcov/index.html` for gaps (e.g., low coverage in `src/ariadne/backends/experimental/`).
- Identify flakiness: Run `pytest tests/ --runslow --lf` (last-fail mode) 10x; note failures in `test_performance_validation.py` (timing variance).

Common issues:
- Non-deterministic backends (e.g., Qiskit noise) → Add `seed=42` to simulators.
- Platform diffs (Windows paths) → Use `os.path.join` in test fixtures.

## Step 2: Fix Flakiness (Week 1, Day 3-4)
Update flaky tests:

### Performance Tests (`test_performance_validation.py`)
Add seeds/timeouts:
```python
import pytest
import numpy as np

@pytest.mark.parametrize("circuit", [ghz_20, random_10], indirect=True)
@pytest.mark.timeout(30)  # 30s timeout
def test_simulation_speed(circuit, benchmark):
    np.random.seed(42)  # Fix randomness
    result = benchmark(simulate, circuit, shots=1000)
    assert result.execution_time < 5.0  # Threshold
```

### Async Tests (`test_async_simulation.py` - if exists, else create)
```python
import asyncio
import pytest
from ariadne.async_ import async_simulate

@pytest.mark.asyncio
async def test_concurrent_routing():
    circuits = [QuantumCircuit(2) for _ in range(5)]
    results = await asyncio.gather(*(async_simulate(c, shots=100) for c in circuits))
    assert all(r.success for r in results)
    assert len(set(r.backend_used for r in results)) <= 3  # Limited variance
```

Commit fixes; re-run: `pytest tests/ -v --lf`.

## Step 3: Add Quantum-Specific Tests (Week 1, Day 5 - Week 2, Day 2)
Create/enhance files in `tests/` and `src/ariadne/algorithms/`.

### GHZ State Test (`tests/test_algorithm_validation.py`)
Add to existing or create:
```python
from qiskit import QuantumCircuit
from ariadne import simulate
from ariadne.algorithms import ghz_state

def test_ghz_routing():
    n_qubits = 20
    qc = ghz_state(n_qubits)
    result = simulate(qc, shots=1000)
    counts = result.get_counts()
    # Stim should route for large GHZ
    assert result.backend_used == 'stim', "Should route to Stim for Clifford"
    assert abs(counts['0' * n_qubits] + counts['1' * n_qubits] - 1000) < 50  # Near-perfect correlation

@pytest.mark.parametrize("n_qubits", [10, 20, 40])
def test_ghz_scalability(n_qubits):
    qc = ghz_state(n_qubits)
    result = simulate(qc, shots=100)
    assert result.success
    assert result.execution_time < 2.0 if n_qubits <= 20 else 10.0  # Scale threshold
```

### Error Correction Test (`tests/test_error_correction.py` - new file)
```python
import pytest
from qiskit.providers.aer.noise import NoiseModel
from ariadne import simulate
from ariadne.algorithms import steane_code

def test_steane_code_routing():
    qc = steane_code(7, error_rate=0.01)
    result = simulate(qc, shots=500, noise_model=NoiseModel())  # Mock noise
    # Should prefer Qiskit for error correction
    assert result.backend_used in ['qiskit', 'stim']
    # Verify logical qubit fidelity >90%
    logical_counts = extract_logical_counts(result)  # Implement helper
    fidelity = max(logical_counts.values()) / 500
    assert fidelity > 0.90, f"Low fidelity: {fidelity}"
```

Implement `steane_code` in `src/ariadne/algorithms/error_correction.py`:
```python
from qiskit import QuantumCircuit

def steane_code(n_physical=7, logical_qubit=0):
    """7-qubit Steane code circuit."""
    qc = QuantumCircuit(n_physical)
    # Encoding gates (simplified)
    qc.h(range(7))
    qc.cx(0, [1,2,4])  # Simplified parity
    # ... full implementation
    qc.measure_all()
    return qc
```

### Experimental Backend Tests (`tests/test_backends.py`)
Add integration (mock external):
```python
import pytest
from unittest.mock import patch
from ariadne.backends.experimental import braket_backend

@patch('braket.aws.amazon_braket.BraketSession')
def test_braket_fallback(mock_session):
    mock_session.return_value.run.return_value.result.return_value = {'0': 1000}
    qc = QuantumCircuit(1)
    qc.x(0)
    qc.measure_all()

    with pytest.raises(ImportError):  # If not installed
        simulate(qc, backend='braket')
    else:
        result = simulate(qc, backend='braket')
        assert result.backend_used == 'braket'
        assert result.get_counts()['1'] == 1000
```

For PyQuil: Similar mock for `pyquil.api.QVM`.

Run: `pytest tests/ --cov --cov-fail-under=60`.

## Step 4: Integrate Coverage into CI (Week 2, Day 3-4)
Update `.github/workflows/ci.yml` (manual edit, as Architect mode limits):
- In `test` job, replace `pytest tests/ -v --tb=short -n auto` with:
  ```
  pytest tests/ -v --tb=short -n auto --cov=src/ariadne --cov-report=xml --cov-fail-under=60
  ```
- Add to `code-quality` job:
  ```
  - name: Coverage Report
    run: coverage report --fail-under=60
  ```
- Ensure Codecov upload: Already present, but add `fail_ci_if_error: true`.

Test locally: `act -j test` (install Act for GitHub Actions simulation).

## Step 5: Validation & Iteration (Week 2, Day 5)
- Run full suite: `tox -e py311-py312` (setup tox.ini if needed).
- Metrics: Aim for >60% (current ~38% → add 20+ tests).
- Commit: New files to `tests/`; updates to `src/ariadne/algorithms/`.
- Docs: Update README.md with "Tests: 60%+ coverage" badge.

## Common Pitfalls & Tips
- **Flakiness**: Always seed RNG (`np.random.seed(42)`); use `@pytest.mark.flaky(reruns=3)`.
- **Coverage Gaps**: Focus on untested paths (e.g., error handling in router).
- **Platform**: Test on Windows via WSL or GitHub Actions.
- **Quantum-Specific**: Use Qiskit TestOps for circuit equivalence; mock noise for determinism.

Track in GitHub Issues. After completion, coverage should hit >60%, enabling Phase 1 milestones.

Last updated: 2025-10-21
