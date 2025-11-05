# Experimental Backends Validation Guide for Ariadne

This guide implements Phase 1, Task 6 of the 6-month roadmap: Validating experimental backends (Braket, PyQuil) with integration tests. Current state: Stubs in `src/ariadne/backends/experimental/`; no comprehensive tests; routing fallbacks to Qiskit if unavailable.

These backends enable cloud/hardware integration but require mocking for CI. Effort: 1 week. Tools: pytest, unittest.mock, optional deps.

## Prerequisites
- Stabilized tests and pinned deps (from prior guides).
- Install advanced extras: `pip install -e .[advanced]` (includes qulacs, cirq; Braket/PyQuil optional).
- For live testing: AWS account for Braket; Rigetti API key for PyQuil.

## Step 1: Implement/Enhance Backend Stubs (Week 5, Day 1-2)
Update `src/ariadne/backends/experimental/` with robust implementations and error handling.

### Braket Backend (`src/ariadne/backends/experimental/braket_backend.py`)
```python
# src/ariadne/backends/experimental/braket_backend.py
import warnings
from typing import Optional
from braket.aws import AwsDevice
from braket.circuits import Circuit as BraketCircuit
from qiskit import QuantumCircuit
from ariadne.backends.base import QuantumBackend

try:
    from braket.devices import LocalSimulator  # For local testing
    from braket.circuits import noise
    AVAILABLE = True
except ImportError:
    AVAILABLE = False
    warnings.warn("Braket not available; install with [advanced]")

class BraketBackend(QuantumBackend):
    def __init__(self, device_arn: Optional[str] = None):
        if not AVAILABLE:
            raise ImportError("Braket requires 'pip install -e .[advanced]'")
        self.device = LocalSimulator() if device_arn is None else AwsDevice(device_arn)

    def run(self, circuit: QuantumCircuit, shots: int = 1000) -> dict:
        # Convert Qiskit to Braket
        braket_circ = BraketCircuit()
        for gate in circuit.data:
            # Simplified conversion (expand for full support)
            if gate.operation.name == 'h':
                braket_circ.h(gate.qubits[0].index)
            elif gate.operation.name == 'cx':
                braket_circ.cnot(gate.qubits[0].index, gate.qubits[1].index)
            # ... add more gates

        task = self.device.run(braket_circ, shots=shots)
        result = task.result()
        return dict(result.measurement_counts)

    @property
    def name(self) -> str:
        return "braket"
```

### PyQuil Backend (`src/ariadne/backends/experimental/pyquil_backend.py`)
```python
# src/ariadne/backends/experimental/pyquil_backend.py
from typing import Optional
from pyquil.api import QVM
from pyquil.quil import Program
from qiskit import QuantumCircuit
from ariadne.backends.base import QuantumBackend

try:
    from pyquil.gates import H, CNOT
    AVAILABLE = True
except ImportError:
    AVAILABLE = False

class PyQuilBackend(QuantumBackend):
    def __init__(self):
        if not AVAILABLE:
            raise ImportError("PyQuil requires 'pip install pyquil'")
        self.qvm = QVM()

    def run(self, circuit: QuantumCircuit, shots: int = 1000) -> dict:
        program = Program()
        for gate in circuit.data:
            if gate.operation.name == 'h':
                program += H(gate.qubits[0].index)
            elif gate.operation.name == 'cx':
                program += CNOT(gate.qubits[0].index, gate.qubits[1].index)
            # ... expand

        program += [f'MEASURE {i}' for i in range(circuit.num_qubits)]
        results = self.qvm.run(program, shots=shots)
        # Aggregate counts
        counts = {}
        for res in results:
            key = ''.join(map(str, res))
            counts[key] = counts.get(key, 0) + 1
        return counts

    @property
    def name(self) -> str:
        return "pyquil"
```

Add to router (`src/ariadne/router.py`):
```python
from .backends.experimental import BraketBackend, PyQuilBackend

# In select_optimal_backend
if backend_preference == 'cloud' and 'braket' in available_extras:
    return BraketBackend()
elif 'pyquil' in available_extras:
    return PyQuilBackend()
else:
    return QiskitBackend()  # Fallback
```

## Step 2: Add Integration Tests (Week 5, Day 3-4)
Create `tests/test_experimental_backends.py`.

```python
import pytest
from unittest.mock import patch, MagicMock
from qiskit import QuantumCircuit
from ariadne import simulate
from ariadne.backends.experimental import BraketBackend, PyQuilBackend

class TestExperimentalBackends:

    @pytest.mark.skipif(not hasattr(BraketBackend, 'AVAILABLE'), reason="Braket not installed")
    def test_braket_live(self):
        qc = QuantumCircuit(2)
        qc.h(0)
        qc.cx(0, 1)
        qc.measure_all()

        result = simulate(qc, backend='braket', shots=100)
        assert result.backend_used == 'braket'
        counts = result.get_counts()
        assert sum(counts.values()) == 100
        assert '00' in counts or '11' in counts  # Bell state expectation

    @pytest.mark.skipif(hasattr(BraketBackend, 'AVAILABLE'), reason="Skip if installed")
    def test_braket_fallback(self):
        qc = QuantumCircuit(1)
        qc.x(0)
        qc.measure_all()

        with pytest.raises(ValueError, match="Braket unavailable"):
            simulate(qc, backend='braket')
        # Should fallback to Qiskit
        result = simulate(qc, shots=100)  # Auto-fallback
        assert result.backend_used != 'braket'

    @patch('pyquil.api.QVM.run')
    def test_pyquil_mock(self, mock_run):
        mock_run.return_value = [[1]] * 100  # Mock results
        qc = QuantumCircuit(1)
        qc.x(0)
        qc.measure_all()

        result = simulate(qc, backend='pyquil', shots=100)
        assert result.backend_used == 'pyquil'
        assert result.get_counts()['1'] == 100

    @pytest.mark.skipif(not hasattr(PyQuilBackend, 'AVAILABLE'), reason="PyQuil not installed")
    def test_pyquil_live(self):
        qc = QuantumCircuit(2)
        qc.h(0)
        qc.cx(0, 1)
        qc.measure_all()

        result = simulate(qc, backend='pyquil', shots=50)
        assert result.backend_used == 'pyquil'
        counts = result.get_counts()
        assert sum(counts.values()) == 50
        # Verify non-zero correlation
        assert counts.get('00', 0) + counts.get('11', 0) > 20

# Router integration
def test_experimental_routing():
    qc = QuantumCircuit(2)
    decision = router.select_optimal_backend(qc, prefer_experimental=True)
    if 'braket' in available_backends:
        assert decision.recommended_backend in ['braket', 'pyquil']
    else:
        assert decision.recommended_backend == 'qiskit'  # Fallback
```

Run: `pytest tests/test_experimental_backends.py -v -m "not live" --cov=src/ariadne/backends/experimental`.

For live tests: Add `@pytest.mark.live` marker; run separately with credentials.

## Step 3: Update Router with Confidence Scores (Week 5, Day 5)
In `src/ariadne/router.py`:
```python
def select_optimal_backend(self, circuit: QuantumCircuit, prefer_experimental: bool = False) -> RoutingDecision:
    # ... existing logic ...
    if prefer_experimental and self._has_experimental(circuit):
        confidence = 0.7 if self._is_simple(circuit) else 0.4  # Lower for complex
        return RoutingDecision('braket' if available else 'pyquil', confidence)
    # Fallback
    return super().select_optimal_backend(circuit)
```

Add `_has_experimental` check based on circuit size/gates.

## Step 4: Documentation & CI Integration
- Update `ROADMAP.md`: Note 90% test pass rate for experimental paths.
- CI: Add conditional job in ci.yml:
  ```
  - name: Test Experimental Backends
    if: env.EXPERIMENTAL == 'true'
    run: pytest tests/test_experimental_backends.py -m live
  ```
- Docs: Add section in README.md: "Experimental: Braket/PyQuil (cloud/hardware; requires API keys)."

## Validation & Metrics
- **Test Pass Rate**: 90% for mocked; 80% live (accounting for network).
- **Fallback Success**: 100% routes to Qiskit if unavailable.
- **Coverage**: >70% for experimental modules.
- Run full suite: `pytest tests/ --cov-fail-under=65`.

Pitfalls:
- **API Keys**: Use env vars (`BRAKET_DEVICE_ARN`, `PYQUIL_API_KEY`); mock in CI.
- **Rate Limits**: Limit shots to 100 in tests.
- **Conversion**: Full Qiskit→Braket/PyQuil mapping needed for prod (use translators).

This ensures experimental backends are validated and integrated safely.

Last updated: 2025-10-21
