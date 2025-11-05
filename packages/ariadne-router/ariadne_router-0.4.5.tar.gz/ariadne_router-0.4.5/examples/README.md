# Ariadne Examples

Welcome to the Ariadne examples! This directory contains a comprehensive collection of examples demonstrating Ariadne's capabilities, from basic usage to advanced features.

## Table of Contents

- [Quick Start](#quick-start)
- [Example Categories](#example-categories)
- [Running Examples](#running-examples)
- [Example Index](#example-index)
- [Learning Path](#learning-path)

---

## Quick Start

The fastest way to get started is with the basic quickstart example:

```bash
python examples/basic/quickstart.py
```

Or try the interactive notebook:

```bash
jupyter lab notebooks/01_ariadne_advantage_fixed.ipynb
```

---

## Example Categories

### Basic Examples (`basic/`)
Perfect for first-time users learning Ariadne fundamentals.

- **quickstart.py** - Your first Ariadne simulation
- **bell_state_demo.py** - Simple Bell state with automatic routing
- **simple_demo.py** - Basic circuit simulation workflow
- **clifford_circuit.py** - Clifford circuit optimization demo

### Educational Examples (`education/`)
Learn quantum computing concepts with interactive tutorials.

- **learning_tutorial.py** - Step-by-step quantum computing basics
- **quantum_algorithms_tutorial.py** - Explore famous quantum algorithms
- **advanced_benchmarking_tutorial.py** - Performance analysis and optimization
- **cli_education_demo.py** - Command-line interface demonstrations

### Advanced Examples (`advanced/`)
Deep dives into Ariadne's powerful features.

- **large_circuit_demo.py** - Simulating large-scale quantum circuits
- **enhanced_routing_demo.py** - Custom routing strategies
- **performance_optimizations_demo.py** - Advanced performance tuning

### Benchmarking Examples (`benchmarking/`)
Compare backends and analyze performance.

- **performance_comparison.py** - Backend performance comparison
- **cross_platform.py** - Cross-platform performance analysis

### Production Examples (`production/`)
Production-ready patterns and best practices.

- **production_ready_demo.py** - Enterprise-grade simulation workflows
- **production_ready_example.py** - Production deployment patterns

---

## Running Examples

### Python Scripts

All Python examples can be run directly from the command line:

```bash
# Run from repository root
python examples/<category>/<example_name>.py

# Examples:
python examples/basic/quickstart.py
python examples/education/learning_tutorial.py
python examples/advanced/large_circuit_demo.py
```

### Jupyter Notebooks

For interactive exploration, use Jupyter notebooks:

1. **Install Jupyter:**
   ```bash
   pip install jupyterlab
   ```

2. **Start JupyterLab:**
   ```bash
   jupyter lab
   ```

3. **Navigate and Run:**
   Open any `.ipynb` file from the `notebooks/` directory

**Available Notebooks:**
- `01_ariadne_advantage_fixed.ipynb` - Ariadne's performance advantages
- `02_mps_performance_scaling.ipynb` - Matrix Product State scaling analysis

---

## Example Index

| Example | Category | Difficulty | Description | Key Concepts |
|---------|----------|------------|-------------|--------------|
| **quickstart.py** | Basic | Beginner | First steps with Ariadne | Basic simulation, automatic routing |
| **bell_state_demo.py** | Basic | Beginner | Create and simulate Bell states | Entanglement, measurement |
| **clifford_circuit.py** | Basic | Beginner | Clifford circuit optimization | Stim backend, 1000× speedup |
| **learning_tutorial.py** | Education | Beginner | Interactive quantum computing basics | Superposition, gates, algorithms |
| **quantum_algorithms_tutorial.py** | Education | Intermediate | Famous quantum algorithms | Deutsch-Jozsa, Grover, QFT |
| **advanced_benchmarking_tutorial.py** | Education | Intermediate | Performance benchmarking | Backend comparison, scalability |
| **large_circuit_demo.py** | Advanced | Advanced | Large-scale circuit simulation | Memory management, MPS backend |
| **enhanced_routing_demo.py** | Advanced | Advanced | Custom routing strategies | Routing tree, performance models |
| **performance_comparison.py** | Benchmarking | Intermediate | Compare backend performance | Benchmarking, profiling |
| **production_ready_demo.py** | Production | Advanced | Production deployment patterns | Error handling, logging, monitoring |
| **production_ready_example.py** | Production | Advanced | Example of production deployment | Production patterns, best practices |

---

## Learning Path

### For Beginners
Start here if you're new to quantum computing or Ariadne:

1. **Read the basics** → [Quantum Computing Primer](../docs/quantum_computing_primer.md)
2. **Run quickstart** → `python examples/basic/quickstart.py`
3. **Try Bell states** → `python examples/bell_state_demo.py`
4. **Interactive tutorial** → `python examples/education/learning_tutorial.py`

### For Students
Already know quantum basics? Dive into algorithms:

1. **Quantum algorithms** → `python examples/education/quantum_algorithms_tutorial.py`
2. **Explore Clifford circuits** → `python examples/clifford_circuit.py`
3. **Performance analysis** → `python examples/education/advanced_benchmarking_tutorial.py`
4. **Interactive notebook** → `jupyter lab notebooks/01_ariadne_advantage_fixed.ipynb`

### For Researchers
Need production-grade performance and customization:

1. **Large circuits** → `python examples/advanced/large_circuit_demo.py`
2. **Custom routing** → `python examples/advanced/enhanced_routing_demo.py`
3. **Backend comparison** → `python examples/benchmarking/performance_comparison.py`
4. **Production patterns** → `python examples/production/production_ready_demo.py`

### For Developers
Building applications with Ariadne:

1. **Production examples** → `examples/production/`
2. **Error handling** → See production_ready_demo.py
3. **CLI integration** → `python examples/education/cli_education_demo.py`
4. **API reference** → [Documentation](../docs/README.md)

---

## Prerequisites

Most examples require only the basic Ariadne installation:

```bash
pip install ariadne-router
```

For hardware-accelerated examples:

```bash
# Apple Silicon (M1/M2/M3/M4)
pip install ariadne-router[apple]

# NVIDIA GPUs
pip install ariadne-router[cuda]
```

For educational notebooks:

```bash
pip install ariadne-router[dev]
```

---

## Expected Outputs

Most examples will output:

- **Backend used** - Which backend Ariadne selected
- **Execution time** - How long the simulation took
- **Results** - Measurement counts or circuit analysis
- **Routing explanation** - Why that backend was chosen

Example output:

```
Backend: stim
Time: 0.012s
Why: Clifford circuit detected → routed to Stim for 1000× speedup
Results: {'00': 502, '11': 498}
```

---

## Troubleshooting

**Import errors:**
```bash
pip install -e .[dev]
```

**Backend not found:**
Check the [Troubleshooting Guide](../docs/troubleshooting.md)

**Performance issues:**
See the [Performance Guide](../docs/PERFORMANCE_GUIDE.md)

**Questions:**
Open a [GitHub Discussion](https://github.com/Hmbown/ariadne/discussions)

---

## Contributing Examples

We welcome new examples! See our [Contributing Guide](../CONTRIBUTING.md) for:

- How to add new examples
- Example structure guidelines
- Documentation requirements
- Testing your examples

---

## Next Steps

After exploring the examples:

- **Deep dive** → [Documentation](../docs/README.md)
- **Contribute** → [Contributing Guide](../CONTRIBUTING.md)
- **Ask questions** → [GitHub Discussions](https://github.com/Hmbown/ariadne/discussions)
- **Report issues** → [GitHub Issues](https://github.com/Hmbown/ariadne/issues)

Happy quantum computing!
