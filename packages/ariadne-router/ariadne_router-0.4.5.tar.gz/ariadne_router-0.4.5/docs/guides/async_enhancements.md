# Async Features & Reproducibility Enhancements Guide for Ariadne

This guide implements Phase 1, Task 5 (and touches on Phase 2, Task 1) of the 6-month roadmap: Enhancing asynchronous simulation capabilities and reproducibility checks. Current state: Basic sync routing in `src/ariadne/router.py`; limited async support; no built-in seed enforcement or variance metrics in `src/ariadne/verify/`.

These enhancements enable concurrent simulations (e.g., batch processing) and ensure deterministic results across runs/platforms. Effort: 1.5 weeks. Tools: asyncio, pytest-asyncio, numpy for variance.

## Prerequisites
- Stabilized tests (from `docs/guides/test_stabilization.md`).
- Pinned deps (e.g., `pytest-asyncio>=0.21.0`).
- Install: `pip install -e .[dev]`.

## Step 1: Enhance Async Simulation (Week 9, Day 1-3)
Update `src/ariadne/async_/simulation.py` (create if missing) for concurrent routing.

### Core Async Implementation
```python
# src/ariadne/async_/simulation.py
import asyncio
from typing import List, Optional, Tuple
from qiskit import QuantumCircuit
from ariadne import simulate  # Sync version
from ariadne.types import SimulationResult

async def async_simulate(
    circuit: QuantumCircuit,
    shots: int = 1000,
    backend: Optional[str] = None,
    **kwargs
) -> SimulationResult:
    """Asynchronous wrapper for simulate()."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,  # Default executor
        simulate,
        circuit,
        shots=shots,
        backend=backend,
        **kwargs
    )

async def batch_simulate(
    circuits: List[QuantumCircuit],
    shots: int = 1000,
    max_concurrent: int = 10,
    **kwargs
) -> List[SimulationResult]:
    """Concurrent simulation of multiple circuits."""
    semaphore = asyncio.Semaphore(max_concurrent)

    async def _simulate_with_sem(circuit: QuantumCircuit) -> SimulationResult:
        async with semaphore:
            return await async_simulate(circuit, shots=shots, **kwargs)

    tasks = [_simulate_with_sem(c) for c in circuits]
    return await asyncio.gather(*tasks, return_exceptions=True)
```

### Integration with Router
Update `src/ariadne/router.py` to support async:
```python
# Add to EnhancedQuantumRouter class
async def async_route_and_simulate(
    self,
    circuit: QuantumCircuit,
    shots: int = 1000,
    **kwargs
) -> SimulationResult:
    """Async version of route_and_simulate."""
    decision = self.select_optimal_backend(circuit)
    return await async_simulate(circuit, backend=decision.recommended_backend, shots=shots, **kwargs)
```

## Step 2: Add Reproducibility Checks (Week 9, Day 4-5)
Enhance `src/ariadne/verify/` for seed enforcement and variance analysis.

### Seed Management (`src/ariadne/verify/seeding.py` - new)
```python
# src/ariadne/verify/seeding.py
import numpy as np
from typing import Optional, Tuple
from qiskit.providers import Backend

def set_global_seed(seed: Optional[int] = None) -> int:
    """Set global seed for reproducibility."""
    if seed is None:
        seed = np.random.randint(0, 2**32)
    np.random.seed(seed)
    # Set seeds for backends (Qiskit example)
    from qiskit_aer import AerSimulator
    AerSimulator().set_options(seed_simulator=seed)
    return seed

def verify_reproducibility(
    circuit: QuantumCircuit,
    shots: int,
    runs: int = 5,
    tolerance: float = 0.05  # 5% variance threshold
) -> Tuple[bool, dict]:
    """Run multiple simulations and check variance."""
    results = []
    seed = set_global_seed(42)  # Fixed for testing

    for i in range(runs):
        result = simulate(circuit, shots=shots, seed=seed + i)  # Vary slightly
        results.append(result.get_counts())

    # Compute variance (e.g., KL divergence or chi-squared)
    from scipy.stats import chisquare
    ref_counts = results[0]
    variances = []
    for counts in results[1:]:
        stat, pvalue = chisquare(list(counts.values()), list(ref_counts.values()))
        variances.append(pvalue)

    mean_variance = np.mean(variances)
    is_reproducible = mean_variance > (1 - tolerance)  # High p-value = low variance

    return is_reproducible, {
        'seed': seed,
        'mean_variance': mean_variance,
        'runs': runs,
        'tolerance': tolerance
    }
```

### Update Verify Module (`src/ariadne/verify/__init__.py`)
```python
from .seeding import set_global_seed, verify_reproducibility

def check_simulation_reproducibility(
    circuit: QuantumCircuit,
    shots: int = 1000,
    runs: int = 3
) -> dict:
    """High-level reproducibility checker."""
    reproducible, metrics = verify_reproducibility(circuit, shots, runs)
    if not reproducible:
        raise ValueError(f"Non-reproducible: variance {metrics['mean_variance']:.3f}")
    return metrics
```

## Step 3: Add Tests for Async & Reproducibility (Week 10, Day 1-3)
Create/update tests in `tests/`.

### Async Tests (`tests/test_async_simulation.py` - new/enhance)
```python
import asyncio
import pytest
from qiskit import QuantumCircuit
from ariadne.async_ import async_simulate, batch_simulate
from ariadne import simulate

@pytest.mark.asyncio
async def test_async_single_simulation():
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure_all()

    sync_result = simulate(qc, shots=100)
    async_result = await async_simulate(qc, shots=100)

    assert async_result.backend_used == sync_result.backend_used
    assert abs(len(async_result.get_counts()) - len(sync_result.get_counts())) <= 1

@pytest.mark.asyncio
async def test_batch_simulation_concurrency():
    circuits = [QuantumCircuit(1) for _ in range(5)]
    results = await batch_simulate(circuits, shots=50, max_concurrent=3)

    assert len(results) == 5
    assert all(isinstance(r, SimulationResult) for r in results if not isinstance(r, Exception))
    assert len(set(r.backend_used for r in results if isinstance(r, SimulationResult))) <= 2  # Limited backends
```

### Reproducibility Tests (`tests/test_reproducibility.py` - new)
```python
import pytest
from qiskit import QuantumCircuit
from ariadne.verify import check_simulation_reproducibility, set_global_seed

def test_seed_enforcement():
    seed = set_global_seed(42)
    qc = QuantumCircuit(1)
    qc.x(0)
    qc.measure_all()

    result1 = simulate(qc, shots=100, seed=seed)
    result2 = simulate(qc, shots=100, seed=seed)

    assert result1.get_counts() == result2.get_counts(), "Seeds should produce identical results"

@pytest.mark.parametrize("shots", [100, 1000])
def test_reproducibility_check(shots):
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure_all()

    metrics = check_simulation_reproducibility(qc, shots=shots, runs=3)
    assert metrics['is_reproducible']  # Should pass for deterministic backends
    assert metrics['mean_variance'] > 0.95
```

Run: `pytest tests/ -v --cov --cov-fail-under=65` (aim for incremental gains).

## Step 4: Integrate into Main API (Week 10, Day 4)
Update `src/ariadne/__init__.py`:
```python
from .async_.simulation import async_simulate, batch_simulate
from .verify import check_simulation_reproducibility

__all__ = [
    # ... existing
    'async_simulate',
    'batch_simulate',
    'check_simulation_reproducibility'
]
```

Add to `simulate()` docstring: "For async, use `async_simulate()`."

## Step 5: Validation & Metrics (Week 10, Day 5)
- **Benchmark Speedup**: Compare sync vs. async batch (expect 1.5-2x for 10+ circuits).
  ```bash
  python -m timeit -s "import asyncio; from ariadne.async_ import batch_simulate; circuits = [QuantumCircuit(2) for _ in range(10)]" "asyncio.run(batch_simulate(circuits))"
  ```
- **Reproducibility**: Run `test_reproducibility_check` 100x; assert 100% pass.
- **CI Integration**: Add to `test` job in ci.yml: `pytest tests/ -m "not slow" --cov`.
- **Success Metrics**: 2x concurrent speedup; 100% reproducibility for seeded runs; >5% coverage increase.

## Common Pitfalls & Tips
- **Async Deadlocks**: Use `asyncio.run()` for top-level; avoid blocking calls in executors.
- **Seed Propagation**: Ensure backends honor seeds (Qiskit/Stim do; patch others if needed).
- **Variance Tolerance**: Adjust for noisy sims (e.g., 0.1 for Aer with noise).
- **Platform**: Test asyncio on Windows (uses ProactorEventLoop).

Commit: New files to `src/ariadne/async_/` and `verify/`; tests to `tests/`. This enables reliable async use cases, aligning with production goals.

Last updated: 2025-10-21
