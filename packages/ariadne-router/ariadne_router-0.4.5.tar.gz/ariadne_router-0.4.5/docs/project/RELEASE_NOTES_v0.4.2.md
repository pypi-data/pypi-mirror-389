## Ariadne v0.4.2 — CI/CD Enhancements and Release Polish

Highlights:
- **CI/CD Pipeline Fixed**: Corrected YAML syntax, updated Python to 3.11, and ensured cross-platform compatibility.
- **Stim Clifford Conversion**: Optimized to run in microseconds by emitting native program text.
- **Clean Packaging**: Verified metadata with canonical project URLs and validated build artifacts via `twine`.
- **Accurate Documentation**: Refreshed README, benchmark reports, and notebook guidance with the latest performance data.

Changes:
- **CI Workflow**:
    - Fixed YAML syntax errors in `.github/workflows/ci.yml`.
    - Updated Python version from 3.10 to 3.11 to match package requirements.
    - Removed invalid `env` block from matrix strategy.
    - Removed invalid `runner.labels` check.
    - Changed from PowerShell to bash for cross-platform compatibility.
- **Performance**:
    - Rewrote Qiskit→Stim converter to emit Stim program text directly, removing Python append overhead (~100 ms → μs).
- **Stability**:
    - Stabilized CPU statevector path by stripping measurements prior to simulation and adding a warm-up to reduce first-run jitter.
- **Dependencies**:
    - Raised minimum supported Python to 3.11.

Verification:
- **Build**: `sdist` and `wheel` produced; `twine check` passed.
- **Tests**: `pytest` reports 319 passed, 32 skipped on Apple Silicon (M4 Max).
- **CI**: Workflow running successfully on all platforms.

Upgrade Notes:
- Python 3.11+ is now required.
- No breaking changes to the public API.
