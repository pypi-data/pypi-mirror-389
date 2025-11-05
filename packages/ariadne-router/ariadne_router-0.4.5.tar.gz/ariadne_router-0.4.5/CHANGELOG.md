# Changelog

All notable changes to this project will be documented in this file.

## [0.4.5] - 2025-11-04

### Added
- `ariadne doctor` diagnostic command for comprehensive system health checks
- `ariadne version` subcommand with detailed version and dependency information
- `ariadne quickstart` interactive command for new users with algorithm demonstrations
- Configuration file support (~/.ariadnerc and ./.ariadnerc) with YAML and JSON formats
- Common pitfalls section to README addressing import confusion and platform-specific issues
- Enhanced backend error messages with installation guidance and alternative suggestions
- Hello Quantum minimal examples for quick getting started
- Comprehensive test suite for v0.4.5 features

### Changed
- Enhanced BackendUnavailableError with actionable installation instructions using ariadne-router[extras] format
- Improved CLI user experience with more discoverable commands
- Better error messages throughout CLI and simulation interfaces
- Updated examples with clearer usage patterns
- Configuration file loading now provides helpful error messages for malformed files
- Quickstart demonstrations now show correct measurement results (|00⟩, |11⟩ instead of |0000⟩, |1100⟩)
- Eliminated duplicate log entries in CLI output

### Fixed
- **Critical:** Updated license field to PEP 621 compliant format for successful pip installation
- QFTGate import issue for Qiskit 1.1.2+ compatibility (changed to QFT)
- Import confusion between ariadne-router package and ariadne import namespace
- Enhanced user onboarding with step-by-step guidance
- Doctor command now recommends ariadne-router[extras] packages instead of raw dependencies
- All installation commands consistently use ariadne-router[extras] format
- Fixed type annotations and enum comparisons for mypy compatibility

## [0.4.4] - 2025-11-01

### Security
- Updated PyYAML from 6.0.1 to 6.0.3 to address security vulnerabilities
- Updated numpy from 1.26.4 to 2.3.4 with expanded version range (<3.0.0)
- Updated qiskit from 2.2.1 to 2.2.3 with expanded version range (<2.0.0)
- Updated scipy from 1.13.1 to 1.16.3 with expanded version range (<2.0.0)
- Fixed bandit security issues: replaced silent exception handling with proper logging
- Enhanced subprocess security by using full paths for system commands
- Added security scanning with bandit to CI pipeline

### Changed
- Improved error handling in backend modules with proper logging instead of silent exception handling
- Enhanced security posture for production deployment readiness

## [0.4.3] - 2025-10-30

### Changed
- Professionalized messaging and documentation: removed brand analogies, neutralized tone across README/examples
- Added trademark/affiliation disclaimer section to README
- Cleaned example output and container default command for non-emoji, log-friendly output

### Added
- Standard OSS polish: CODEOWNERS, SUPPORT.md, CITATION.cff, .editorconfig, Dependabot configuration

### Docs
- Reduced Sphinx build warnings by correcting RST heading underlines and excluding unstable modules from API docs

## [0.4.2] - 2025-10-29

### Added
- Verified packaging builds cleanly (`sdist` and `wheel`) and metadata passes `twine check`
- Improved CLI integration tests and help/version coverage
- Expanded README with accurate test counts and clarified performance statements
- Added canonical project URLs to `pyproject.toml` for PyPI metadata completeness

### Changed
- Optimized Stim converter by emitting program text directly, reducing Clifford circuit conversion overhead from ~100 ms to microseconds
- Raised minimum supported Python version to 3.11 to align with modern dependency support and strict zip iteration
- Updated Bell state demo to correctly interpret measurement bitstrings when `measure_all()` adds an extra classical register; verification now extracts the 2-qubit outcomes reliably
- Aligned README "Comprehensive Benchmark Results" and "Project Status" with current test results (319 passed, 32 skipped)
- Removed unused legacy benchmark parser helpers from CLI to avoid duplication
- Refreshed benchmark artifacts with latest reproducible performance measurements on Apple Silicon (M4 Max)

### Fixed
- Removed unused imports in config coverage tests to satisfy linting (ruff) and keep `make lint` green
- Addressed timing jitter in CPU backend and in a stability test (trimmed outliers)
- Normalized performance stability calculations to plain Python floats to avoid NumPy scalar warnings

## [0.3.4] - 2025-10-22

### Added
- New `get_available_backends()` function to public API for checking available backends
- Added offline release readiness checklist script and Makefile target for packaging validation
- Added optional dependencies for additional quantum platforms: PennyLane, PyQuil, Braket, Q#, and OpenCL
- Added quantum-full Docker environment with all quantum libraries pre-installed
- Added quantum-full service to docker-compose configuration

### Changed
- Updated license classifier format for compatibility with newer setuptools versions
- Reorganized optional dependencies with new quantum_platforms group
- Enhanced Dockerfile with multi-stage build including quantum-full environment
- Updated documentation to include quantum-full Docker usage

## [0.3.2] - 2025-10-20

### Added

- **Positioning Language**: Refined README language to clearly describe automatic routing and clarify differentiation from Qiskit Aer, avoiding brand analogies
- **PyPI Name Clarity**: Changed package name back to `ariadne-router` to avoid conflict with GraphQL Ariadne library
- **Enhanced CLI Error Handling**: Added friendly error messages for missing optional backends with install instructions (CUDA, JAX-Metal, MPS/TN, Stim)
- **New CLI Commands**: Added `ariadne run` and `ariadne explain` commands for better user experience
- **Routing Transparency**: Enhanced `explain_routing()` visibility throughout documentation and examples
- **Repeatable Benchmark Demo**: Added `examples/routing_demo_notebook.py` to validate README claims with real benchmarks
- **README Example Validator**: Added `examples/validate_readme_examples.py` to ensure all documentation examples work
- **Enhanced Quickstart**: Updated `examples/quickstart.py` to showcase key routing decisions from README

### Changed

- **Package Name**: From `ariadne-quantum-router` to `ariadne-router` in pyproject.toml
- **README Structure**: Improved positioning with clear value proposition, use cases, and external references
- **CLI User Experience**: Better error messages guide users to install missing optional dependencies
- **Documentation Links**: Added references to Stim and quimb documentation, QMAP paper for hardware routing distinction

### Fixed

- **CLI Duplicate Commands**: Resolved conflicting benchmark subparser issue
- **Linting Issues**: Fixed f-string formatting in CLI module
- **Import Validation**: Ensured all README code examples work correctly

## [0.2.0] - 2025-10-17

### Added

-   **Comprehensive Routing Tree**: Introduced `ariadne.ComprehensiveRoutingTree`, a new, powerful way to control and inspect routing decisions.
-   **Advanced Routing Strategies**: Added new routing strategies like `SPEED_FIRST`, `MEMORY_EFFICIENT`, `CLIFFORD_OPTIMIZED`, `APPLE_SILICON_OPTIMIZED`, and `CUDA_OPTIMIZED`.
-   **Routing Explanations**: Added `ariadne.explain_routing` to provide detailed, human-readable explanations for routing decisions.
-   **Routing Visualization**: Added `ariadne.show_routing_tree` to visualize the entire routing decision tree.

### Changed

-   **Public API**: `ariadne.ComprehensiveRoutingTree` is now the recommended entry point for advanced routing control. `QuantumRouter` is maintained as an alias for backward compatibility.
-   **Documentation**: Updated `README.md` and other documentation to reflect the new routing system.

## [0.1.0] - 2025-10-15

- macOS-first launch; Apple Silicon supported via Metal (falls back to CPU gracefully).
- Automatic backend routing:
  - Clifford → Stim
  - Low entanglement → MPS
  - Apple Silicon → Metal (when available)
  - General → Qiskit (CPU)
- CLI wired to `ariadne.cli.main:main`; `ariadne --help` now exposes subcommands.
- Fixed Metal backend sampling without JAX by converting statevector to NumPy.
- Docs: added Use Cases and Routing Matrix to README; added routing rules page and examples gallery.
- Packaging verified: `python -m build` and `twine check` pass.
- Docker: development and production stages updated for editable and standard installs.
