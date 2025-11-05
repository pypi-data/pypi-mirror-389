# Documentation Enhancements Guide for Ariadne

This guide implements Phase 1, Task 10 of the 6-month roadmap: Enhancing documentation with a Windows guide, alt-text for images, and CI validation for examples. Current state: Strong README.md with badges; Sphinx setup in pyproject.toml/docs extras; examples/*.ipynb and *.py exist but unvalidated in CI; no dedicated Windows guide; images (e.g., routing matrix) lack alt-text.

These changes improve accessibility, usability, and reliability. Effort: 1 week. Tools: Sphinx, nbconvert for validation, accessibility checkers.

## Prerequisites
- Completed CI expansion (from `docs/guides/ci_expansion.md`).
- Docs deps: `pip install -e .[docs]`.
- Tools: `sphinx-build`, `jupyter nbconvert`.

## Step 1: Add Windows Guide (Week 4, Day 1-2)
Create `docs/guides/windows.md`:

```markdown
# Windows Setup Guide for Ariadne

Ariadne works on Windows via native Python or WSL2. This guide covers installation, common issues, and best practices.

## Installation

### Native Windows
1. Install Python 3.11+ from [python.org](https://www.python.org/downloads/windows/).
2. Use Command Prompt or PowerShell:
   ```cmd
   pip install ariadne-router[dev]
   ```
3. For CUDA (NVIDIA GPU):
   - Download CUDA Toolkit from [NVIDIA](https://developer.nvidia.com/cuda-downloads).
   - Install: `choco install cuda` (if Chocolatey) or manual.
   - Verify: `nvidia-smi` in cmd.
   - Install: `pip install ariadne-router[cuda]`.

### WSL2 (Recommended for Linux Parity)
1. Enable WSL2: Settings > Apps > Optional Features > Windows Subsystem for Linux.
2. Install Ubuntu from Microsoft Store.
3. In WSL:
   ```bash
   sudo apt update
   sudo apt install python3-pip
   pip install ariadne-router[dev]
   ```

## Common Issues & Fixes
- **Path Separators**: Use `os.path.join` in code; avoid hardcoded `/`.
- **CUDA Detection**: Set `CUDA_PATH` env var if not auto-detected.
- **Asyncio on Windows**: Uses ProactorEventLoop; add `asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())` if issues.
- **Dependencies**: Use `py -m pip` instead of `pip` in cmd.
- **Tests**: Run `pytest tests/ -v` in WSL for Linux-like behavior.

## Verification
```cmd
python -c "from ariadne import simulate; print('✓ Ariadne ready on Windows!')"
python examples/quickstart.py
```

For troubleshooting, check CI logs from GitHub Actions (Windows runner).

Last updated: 2025-10-21
```

Link in README.md: Add under "Quick Links": "- **Windows Users** → [Windows Guide](guides/windows.md)".

## Step 2: Add Alt-Text to Images (Week 4, Day 3)
Scan docs for images and add descriptive alt-text for accessibility.

### README.md Updates
For routing matrix:
```markdown
![Routing matrix](docs/source/_static/routing_matrix.png)

*Alt-text: A heatmap showing Ariadne's backend routing decisions for different circuit types (Clifford, low-entanglement, high-entanglement) across backends (Stim, MPS, TN, Qiskit). Darker colors indicate higher confidence/suitability.*
```

For quickstart GIF:
```markdown
![Quickstart Routing Demo](docs/source/_static/quickstart.gif)

*Alt-text: Animated GIF demonstrating Ariadne's automatic backend selection for a Bell state circuit, showing routing to Qiskit with execution time and results.*
```

### Other Files
- In `ROADMAP.md`: Add alt-text to any tables/figures if added.
- Use tools: Run `alt-text-checker` or manual review with screen readers.

Update Sphinx conf.py (if using reST): Ensure `img` directives have `:alt:`.

## Step 3: CI Validation for Examples (Week 4, Day 4-5)
Enhance ci.yml's `test-notebooks` job to validate all examples.

### Update ci.yml
Expand the notebook job:
```yaml
test-examples:
  name: Validate Examples & Notebooks
  runs-on: ubuntu-latest
  strategy:
    matrix:
      python-version: ["3.11"]
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        pip install -e ".[dev,viz]"
        pip install nbconvert ipykernel jupyter pytest
    - name: Validate Python Examples
      run: |
        set -e
        for script in examples/*.py; do
          echo "Running $script"
          timeout 60 python "$script" || { echo "Failed: $script"; exit 1; }
        done
    - name: Execute Notebooks
      run: |
        set -e
        for notebook in examples/*.ipynb; do
          echo "Executing $notebook"
          jupyter nbconvert --to notebook --execute "$notebook" --ExecutePreprocessor.timeout=300 --allow-errors=false
        done
    - name: Upload Example Artifacts
      if: always()
      uses: actions/upload-artifact@v4
      with:
        name: example-outputs
        path: |
          examples/*.ipynb  # Executed versions
          examples/*.png    # Generated plots
```

### Local Validation Script
Create `scripts/validate_examples.py`:
```python
#!/usr/bin/env python3
import subprocess
import sys
import glob
from pathlib import Path

def run_example(example_path: Path):
    if example_path.suffix == '.py':
        result = subprocess.run([sys.executable, str(example_path)], capture_output=True, timeout=60)
        if result.returncode != 0:
            print(f"Failed: {example_path}")
            print(result.stderr.decode())
            return False
        print(f"Passed: {example_path}")
    elif example_path.suffix == '.ipynb':
        result = subprocess.run(['jupyter', 'nbconvert', '--to', 'notebook', '--execute', str(example_path), '--allow-errors=false'], timeout=300, capture_output=True)
        if result.returncode != 0:
            print(f"Failed: {example_path}")
            return False
        print(f"Passed: {example_path}")
    return True

if __name__ == "__main__":
    examples = glob.glob("examples/*")
    all_pass = True
    for ex in examples:
        if not run_example(Path(ex)):
            all_pass = False
    sys.exit(0 if all_pass else 1)
```

Run locally: `python scripts/validate_examples.py`.

## Step 4: Sphinx & Overall Polish
- Build docs: `cd docs; sphinx-build -b html source build/html`.
- Add badges to README.md:
  ```
  [![Tests](https://github.com/Hmbown/ariadne/actions/workflows/ci.yml/badge.svg)](https://github.com/Hmbown/ariadne/actions/workflows/ci.yml)
  [![Coverage](https://codecov.io/gh/Hmbown/ariadne/branch/main/graph/badge.svg)](https://codecov.io/gh/Hmbown/ariadne)
  ```
- Accessibility: Run `axe` or Lighthouse on built HTML; ensure ARIA labels.

## Validation & Metrics
- **Build Success**: Sphinx builds without warnings; 100% alt-text.
- **CI Pass**: Examples execute in <10min; artifacts include outputs.
- **Usability**: Windows guide tested on Win10/11; feedback loop via Issues.

Pitfalls:
- **Notebook Errors**: Use `--allow-errors=false` to catch issues; debug with `--to python`.
- **Image Paths**: Use relative paths (e.g., `docs/source/_static/`).
- **Length**: Keep guides concise; link to upstream docs (e.g., Qiskit Windows).

Commit: New `windows.md`; updated README.md/ci.yml. This completes Phase 1 documentation enhancements.

Last updated: 2025-10-21
