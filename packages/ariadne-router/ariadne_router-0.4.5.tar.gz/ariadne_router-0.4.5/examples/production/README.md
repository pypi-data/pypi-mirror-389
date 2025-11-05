Production CI Templates

This directory contains minimal, production‑ready examples for integrating Ariadne into CI/CD pipelines.

- GitHub Actions matrix testing across macOS, Linux, and Windows
- Quantum regression tests via the composite action `.github/actions/ariadne-ci`
- Local install in CI to validate the code in the repository

Key files:
- `ci_example.yml` — basic workflow that installs the package and runs a small benchmark/regression test

Recommended install for CI:

```yaml
- name: Install package (local)
  run: |
    python -m pip install --upgrade pip
    pip install -e ".[advanced,viz]"
```

Using the composite action in a workflow:

```yaml
- name: Run Ariadne CI
  uses: ./.github/actions/ariadne-ci
  with:
    circuits-folder: test_circuits
    backends-list: auto,stim,qiskit,mps
    tolerance: '0.05'
    shots: '1000'
    algorithms: 'bell,ghz,qaoa,vqe'
```

For a full pipeline, see `.github/workflows/quantum-regression.yml`.
