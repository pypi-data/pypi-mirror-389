# Ariadne Quantum Simulator Documentation

## Welcome to Ariadne

Ariadne is a zero-configuration quantum simulator bundle that automatically routes your circuits to the optimal backend. Whether you're teaching quantum computing, running benchmarks across platforms, or setting up CI pipelines, Ariadne ensures reproducible results without the complexity of manual backend selection.

### Choose Your Path

Select the documentation path that best matches your role:

- [For Classroom Instructors](./getting-started/for-instructors.md) — turnkey classroom setups, lesson plans, and grading workflows.
- [For Research Scientists](./getting-started/for-researchers.md) — performance analysis, reproducible benchmarking, and publication tooling.
- [For DevOps Engineers](./getting-started/for-devops.md) — deployment, observability, and CI/CD integration guidance.

---

## Quick Navigation

- **Install & Launch**
  - [Quick Start](./quickstart.md) — run your first routed simulation in minutes.
  - [Installation Summary](./installation_summary.md) — copy-paste commands for every platform.
  - [Comprehensive Installation](./comprehensive_installation.md) — full dependency matrix and advanced setups.
  - [Troubleshooting](./troubleshooting.md) — unblock common installation and runtime issues fast.
- **Understand the Router**
  - [Routing Decisions Explained](./router_decisions.md) — walkthrough of the prioritized filter chain and scoring engine.
  - [Capability Matrix](./capability_matrix.md) — backend feature comparison at a glance.
  - [Performance Guide](./PERFORMANCE_GUIDE.md) — tuning tips for speed, memory, and accuracy.
- **Learn & Teach**
  - [Quantum Computing Primer](./quantum_computing_primer.md) — crash course for new learners.
  - [Algorithms Catalog](./algorithms.md) — curated list of 15+ built-in quantum algorithms.
  - [Examples Repository](../examples/README.md) — notebooks and scripts for education, benchmarking, and production use.
- **Develop & Contribute**
  - [Developer Guide](./guides/developer_guide.md) — architecture overview and development workflow.
  - [Release Notes](./project/RELEASE_NOTES_v0.4.1.md) — latest changes and migration tips.
  - [CONTRIBUTING](./project/CONTRIBUTING.md) — how to file issues, propose features, and open pull requests.
- **API Reference**
  - [Sphinx API Docs](./source/index.rst) — auto-generated reference for the entire public API.
  - [Routing Rules](./source/routing_rules.md) — deep dive into router heuristics and configuration options.

---

## Available Quantum Algorithms

Ariadne ships with 15+ ready-to-run algorithms across multiple categories:

**Foundational**
- Bell States (entanglement)
- GHZ States (multipartite entanglement)
- Quantum Fourier Transform (QFT)
- Quantum Phase Estimation (QPE)

**Search Algorithms**
- Grover's Search (quadratic speedup)
- Bernstein-Vazirani (linear speedup)

**Optimization**
- QAOA (Quantum Approximate Optimization Algorithm)
- VQE (Variational Quantum Eigensolver)

**Error Correction**
- Steane Code [[7,1,3]] CSS code
- Surface Code (simplified)

**Machine Learning**
- Quantum Support Vector Machine (QSVM)
- Variational Quantum Classifier (VQC)
- Quantum Neural Network

**Specialized**
- Deutsch-Jozsa (constant vs balanced functions)
- Simon's Algorithm (period finding)
- Quantum Walk (search enhancement)
- Amplitude Amplification (Grover generalization)
