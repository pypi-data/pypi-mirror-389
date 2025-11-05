# Contributing to Ariadne

Thank you for your interest in contributing to Ariadne! We welcome contributions from the community and are excited to work with you to make quantum computing more accessible.

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Submitting Issues](#submitting-issues)
- [Submitting Pull Requests](#submitting-pull-requests)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing Requirements](#testing-requirements)
- [Documentation](#documentation)
- [Community](#community)

---

## Getting Started

There are many ways to contribute to Ariadne:

- **Bug Reports**: Help us identify and fix bugs
- **Feature Requests**: Suggest new features or improvements
- **Code Contributions**: Submit bug fixes or new features
- **Documentation**: Improve or expand documentation
- **Examples**: Add educational examples or use cases
- **Testing**: Help expand test coverage
- **Community Support**: Answer questions and help other users

---

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Git
- pip or conda

### Setting Up Your Development Environment

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/ariadne.git
   cd ariadne
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies:**
   ```bash
   pip install -e .[dev]
   ```

4. **Install pre-commit hooks:**
   ```bash
   pre-commit install
   ```

5. **Verify your setup:**
   ```bash
   pytest tests/
   ```

---

## How to Contribute

### Submitting Issues

Before creating a new issue:

- **Search existing issues** to avoid duplicates
- **Check the documentation** to see if your question is already answered

When submitting an issue, please include:

- **Clear title and description**
- **Steps to reproduce** (for bugs)
- **Expected vs actual behavior**
- **Environment details** (OS, Python version, Ariadne version)
- **Code snippets** or error messages (use code blocks)
- **Screenshots** if applicable

**Issue Templates:**
- Bug Report: For reporting bugs or errors
- Feature Request: For suggesting new features
- Documentation: For documentation improvements
- Question: For general questions

---

## Submitting Pull Requests

### Before You Start

1. **Check existing PRs** to avoid duplicate work
2. **Open an issue first** for major changes to discuss the approach
3. **Review architectural decisions** in [`docs/router_decisions.md`](docs/router_decisions.md) for routing/core logic changes

### PR Workflow

1. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. **Make your changes:**
   - Write clean, readable code
   - Follow existing code patterns
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes:**
   ```bash
   # Run all tests
   pytest

   # Run specific tests
   pytest tests/test_specific.py

   # Check code coverage
   pytest --cov=ariadne tests/
   ```

4. **Lint your code:**
   ```bash
   # Ruff will run automatically via pre-commit
   # Or run manually:
   ruff check .
   ruff format .
   ```

5. **Commit your changes:**
   ```bash
   git add .
   git commit -m "feat: Add interactive circuit builder"
   ```

   **Commit Message Guidelines:**
   - Use present tense ("Add feature" not "Added feature")
   - Use imperative mood ("Move cursor to..." not "Moves cursor to...")
   - Limit first line to 72 characters
   - Reference issues and pull requests when applicable

6. **Push to your fork:**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request:**
   - Provide a clear title and description
   - Link related issues
   - Describe what changed and why
   - Include screenshots for UI changes
   - List any breaking changes

---

## Code Style Guidelines

Ariadne uses automated tools to enforce code style:

- **Formatter**: `ruff format` (runs via pre-commit)
- **Linter**: `ruff check` (runs via pre-commit)
- **Type Checker**: `mypy` (optional but recommended)

### Key Style Points

- **Line length**: 120 characters maximum
- **Imports**: Organized automatically by ruff
- **Naming conventions**:
  - Classes: `PascalCase`
  - Functions/variables: `snake_case`
  - Constants: `UPPER_CASE`
- **Docstrings**: Use Google-style docstrings
- **Type hints**: Add type hints to all public functions

### Example Docstring

```python
def simulate(circuit: QuantumCircuit, shots: int = 1024) -> SimulationResult:
    """Simulate a quantum circuit with automatic backend selection.

    Args:
        circuit: The quantum circuit to simulate.
        shots: Number of measurement shots to perform.

    Returns:
        SimulationResult containing counts, backend used, and execution time.

    Raises:
        CircuitTooLargeError: If the circuit exceeds available resources.
        SimulationError: If the simulation fails.
    """
```

---

## Testing Requirements

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=ariadne

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m "not slow"    # Skip slow tests
```

### Writing Tests

- **Location**: Place tests in `tests/` directory
- **Naming**: Test files must start with `test_`
- **Coverage**: Aim for >80% code coverage for new code
- **Markers**: Use pytest markers for test categorization

```python
import pytest
from ariadne import simulate

def test_basic_simulation():
    """Test basic circuit simulation."""
    # Arrange
    circuit = create_bell_circuit()

    # Act
    result = simulate(circuit, shots=1000)

    # Assert
    assert result.backend_used in ['qiskit', 'stim']
    assert len(result.counts) > 0
```

---

## Documentation

### Types of Documentation

1. **Code Documentation**: Docstrings in source code
2. **User Documentation**: Markdown files in `docs/`
3. **Examples**: Python scripts in `examples/`
4. **API Reference**: Auto-generated from docstrings

### Updating Documentation

When making changes, update:

- **Docstrings**: For API changes
- **README.md**: For major features
- **Documentation** (docs/): For user-facing functionality
- **Examples**: Add or update example scripts
- **CHANGELOG.md**: Document changes for next release

---

## Community

### Getting Help

- **GitHub Discussions**: For questions and discussions
- **GitHub Issues**: For bug reports and feature requests
- **Documentation**: Start with [README.md](README.md) and [Documentation](docs/README.md)

### Code Review Process

All PRs require:

1. **Passing CI/CD checks** (tests, linting, type checking)
2. **Code review** from at least one maintainer
3. **Documentation updates** if applicable
4. **CHANGELOG entry** for user-facing changes

### Recognition

Contributors are recognized in:

- **CHANGELOG.md**: For each release
- **GitHub Contributors**: Automatically tracked
- **Release Notes**: For significant contributions

---

## Questions?

If you have questions about contributing, feel free to:

- Open a GitHub Discussion
- Comment on an existing issue
- Reach out to the maintainers

Thank you for contributing to Ariadne and helping make quantum computing more accessible!
