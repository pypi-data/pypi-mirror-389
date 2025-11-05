# CI Expansion Guide for Ariadne: Windows & Cross-Platform Support

This guide implements Phase 1, Task 9 of the 6-month roadmap: Expanding CI to full Windows and cross-platform support in `.github/workflows/ci.yml`. Current state: Basic matrix (Ubuntu/macOS/Windows, Python 3.11/3.12), but lacks Windows-specific fixes (e.g., path handling, CUDA), full coverage enforcement, and artifact uploads for all platforms.

This ensures parity across OSes, critical for production reliability. Effort: 1.5 weeks. Tools: GitHub Actions, Act (local testing), pwsh for Windows.

## Prerequisites
- Stabilized tests and pinned deps (from prior guides).
- Local testing: Install [Act](https://github.com/nektos/act) for simulating workflows.
- Access: GitHub repo with write perms for workflows.

## Step 1: Audit Current CI (Week 3, Day 1)
Review `.github/workflows/ci.yml`:
- **Strengths**: Matrix covers 3 OS x 2 Python = 6 combos; caching; security scans.
- **Gaps**: No Windows-specific commands (e.g., `pip` vs. `py -m pip`); no coverage aggregation across platforms; conditional jobs (e.g., Apple deps only on macOS); no failure artifacts.

Run locally: `act -j test -P ubuntu-latest=ubuntu-latest` (test Ubuntu first).

## Step 2: Add Windows-Specific Fixes (Week 3, Day 2-3)
Update the `test` job in ci.yml for platform-aware steps.

### Path & Command Handling
Use cross-platform syntax:
```yaml
- name: Install dependencies
  shell: pwsh  # Use PowerShell on Windows
  run: |
    python -m pip install --upgrade pip
    if ($env:PLATFORM -eq "windows") {
      pip install -e ".[dev,viz]"
    } else {
      pip install -e ".[dev,viz]"
    }
    # Windows CUDA check
    if ($env:PLATFORM -eq "windows" -and (Test-Path "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA")) {
      pip install -e ".[cuda]"
    }
```

### Environment Variables
Add matrix env vars:
```yaml
strategy:
  matrix:
    os: [ubuntu-latest, windows-latest, macos-latest]
    python-version: ["3.11", "3.12"]
  fail-fast: false
env:
  PLATFORM: ${{ runner.os }}
```

For Windows paths in pytest:
```yaml
- name: Run tests
  shell: pwsh
  run: |
    if ($env:PLATFORM -eq "windows") {
      # Fix path separators
      $env:PYTHONPATH = ($env:PYTHONPATH -replace '\\', '/')
      pytest tests/ -v --tb=short -n auto --cov=src/ariadne --cov-report=xml --cov-fail-under=60
    } else {
      pytest tests/ -v --tb=short -n auto --cov=src/ariadne --cov-report=xml --cov-fail-under=60
    }
```

## Step 3: Enhance Coverage & Artifacts (Week 3, Day 4)
- **Aggregate Coverage**: Add job to combine reports (use `codecov-action` multi-upload).
  ```yaml
  - name: Upload coverage to Codecov
    uses: codecov/codecov-action@v4
    with:
      file: ./coverage.xml
      flags: ${{ runner.os }}-${{ matrix.python-version }}
      name: codecov-${{ runner.os }}-${{ matrix.python-version }}
  ```
- **Artifacts for All Platforms**: Update upload:
  ```yaml
  - name: Upload test artifacts
    if: always()
    uses: actions/upload-artifact@v4
    with:
      name: test-results-${{ runner.os }}-${{ matrix.python-version }}
      path: |
        .coverage
        tests/results/
        pytest.xml
  ```
- **Enforce Coverage**: Already in pytest; add global threshold in code-quality job:
  ```yaml
  - name: Global Coverage Check
    run: coverage report --fail-under=60
  ```

## Step 4: Add Platform-Specific Jobs (Week 4, Day 1-2)
### Windows CUDA Job (Conditional)
```yaml
windows-cuda:
  name: Windows CUDA Tests
  runs-on: windows-latest
  if: contains(runner.labels, 'gpu')  # Use GPU runner if available
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: 3.11
    - name: Install CUDA deps
      run: |
        choco install cuda  # Chocolatey for CUDA
        pip install -e ".[cuda,dev]"
    - name: Run CUDA tests
      run: pytest tests/test_cuda_backend.py -v
```

### macOS Apple Silicon
Already partial; enhance:
```yaml
- name: Install Apple Silicon dependencies
  if: runner.os == 'macOS'
  run: |
    pip install -e ".[apple]"
    # Verify Metal
    python -c "import jax; print(jax.devices())"
```

## Step 5: Full Matrix Validation (Week 4, Day 3)
- **Test All Combos**: Run `act` locally for each:
  ```bash
  act -j test -P ubuntu-latest=ubuntu-latest -P python-version=3.11
  act -j test -P windows-latest=windows-latest -P python-version=3.11  # Requires WSL/VM
  ```
- **Benchmark Parity**: Add cross-platform perf check:
  ```yaml
  - name: Cross-Platform Perf Check
    run: |
      python benchmarks/quick_check.py --platform ${{ runner.os }}
    if: matrix.python-version == '3.11' && runner.os == 'ubuntu-latest'
  ```

## Step 6: Documentation & Metrics (Week 4, Day 4-5)
- Update README.md: Add "CI: Full cross-platform support" badge (e.g., GitHub workflow status).
- Docs: Create `docs/guides/windows.md` snippet:
  ```
  ## Windows Setup
  - Use WSL2 for Linux-like env.
  - CUDA: Install via Chocolatey (`choco install cuda`).
  - Paths: Use `/` separators in Python code.
  ```
- **Success Metrics**: 100% pass on 6 combos; <10min total runtime; artifacts for debugging.
- CI: Aim for green matrix; monitor with GitHub insights.

Pitfalls:
- **Windows Paths**: Always use `os.path.join`; avoid hardcoded `/`.
- **Caching**: Keys include `${{ runner.os }}` for per-platform cache.
- **Resources**: Windows runners slower; use `timeout-minutes: 15` if needed.

Commit: Updated ci.yml. This completes Phase 1 CI expansion, enabling reliable cross-platform development.

Last updated: 2025-10-21
