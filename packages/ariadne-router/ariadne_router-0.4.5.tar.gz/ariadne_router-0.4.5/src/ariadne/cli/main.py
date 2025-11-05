"""
Command-line interface for Ariadne.

This module provides a comprehensive CLI for all Ariadne functionality,
including simulation, configuration management, and system monitoring.
"""

import argparse
import logging
import os
import platform
import sys
import time
from argparse import ArgumentParser, _SubParsersAction
from pathlib import Path
from typing import TYPE_CHECKING, Any

import psutil
from qiskit import QuantumCircuit

from .._version import __version__
from ..backends import (
    get_health_checker,
    get_pool_manager,
)
from ..config import (
    ConfigFormat,
    create_default_template,
    create_development_template,
    create_production_template,
    load_config,
)
from ..core import configure_logging, get_logger
from ..router import simulate

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    from ariadne.types import BackendType
except ImportError:  # pragma: no cover - fallback for script execution
    if PROJECT_ROOT not in sys.path:
        sys.path.append(PROJECT_ROOT)
    from ariadne.types import BackendType

if TYPE_CHECKING:
    from ariadne.backends.health_check import HealthMetrics
    from ariadne.core.logging import AriadneLogger
    from ariadne.results import SimulationResult


BACKEND_ALIASES: dict[str, str] = {"metal": BackendType.JAX_METAL.value}

CLI_BACKEND_CHOICES = sorted(
    {
        BackendType.QISKIT.value,
        BackendType.STIM.value,
        BackendType.CUDA.value,
        BackendType.JAX_METAL.value,
        BackendType.TENSOR_NETWORK.value,
        BackendType.MPS.value,
        BackendType.DDSIM.value,
    }
    | set(BACKEND_ALIASES.keys())
    | set(BACKEND_ALIASES.values())
)

# Check if YAML is available
yaml: Any | None
try:
    import yaml as _yaml_module
except ImportError:
    YAML_AVAILABLE = False
    yaml = None
else:
    YAML_AVAILABLE = True
    yaml = _yaml_module


def _describe_config_keys(config: object) -> str:
    """Return a readable list of configuration keys for logging/display."""

    if isinstance(config, dict):
        return ", ".join(sorted(str(key) for key in config.keys()))

    if hasattr(config, "model_dump"):
        try:
            data = config.model_dump()
        except Exception:  # pragma: no cover - defensive fallback
            data = getattr(config, "__dict__", {})
        if isinstance(data, dict):
            return ", ".join(sorted(str(key) for key in data.keys()))

    if hasattr(config, "__dict__"):
        return ", ".join(sorted(str(key) for key in vars(config)))

    return ""


class ProgressIndicator:
    """Simple progress indicator for long-running operations."""

    def __init__(self, description: str = "Processing"):
        """Initialize progress indicator."""
        self.description = description
        self.start_time: float | None = None
        self.last_update: float = 0

    def start(self) -> None:
        """Start the progress indicator."""
        self.start_time = time.time()
        print(f"{self.description}...", end="", flush=True)

    def update(self, message: str = "") -> None:
        """Update the progress indicator."""
        current_time = time.time()
        if self.start_time is not None and current_time - self.last_update > 0.5:  # Update every 0.5 seconds
            elapsed = current_time - self.start_time
            print(f"\r{self.description}... ({elapsed:.1f}s){message}", end="", flush=True)
            self.last_update = current_time

    def finish(self, message: str = "done") -> None:
        """Finish the progress indicator."""
        if self.start_time is not None:
            elapsed = time.time() - self.start_time
            print(f"\r{self.description}... {message} ({elapsed:.1f}s)")
        else:
            print(f"\r{self.description}... {message} (0.0s)")


class AriadneCLI:
    """Main CLI class for Ariadne."""

    def __init__(self) -> None:
        """Initialize the CLI."""
        self.logger: AriadneLogger | None = None

    def run(self, args: list[str] | None = None) -> int:
        """
        Run the CLI with the given arguments.

        Args:
            args: Command-line arguments (uses sys.argv if None)

        Returns:
            Exit code
        """
        parser = self._create_parser()
        parsed_args = parser.parse_args(args)

        # Configure logging
        log_level_name = getattr(parsed_args, "log_level", "INFO")
        log_level = getattr(logging, log_level_name.upper(), logging.INFO)
        configure_logging(level=log_level)
        self.logger = get_logger("cli")

        # Execute command
        try:
            cmd_method = getattr(self, f"_cmd_{parsed_args.command.replace('-', '_')}")
            result: int = cmd_method(parsed_args)
            return result
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            return 130
        except Exception as e:
            if self.logger:
                self.logger.error(f"Command failed: {e}")
            return 1

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser."""
        parser = argparse.ArgumentParser(
            prog="ariadne",
            description="Ariadne quantum circuit simulation framework",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  ariadne simulate circuit.qc --shots 1000 --backend qiskit
  ariadne config create --template production --output config.yaml
  ariadne status --backend metal
  ariadne benchmark --circuit circuit.qc --shots 1000
  ariadne install --accelerate
  ariadne install cuda apple
  ariadne install --list
            """,
        )

        # Add global arguments
        parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

        parser.add_argument(
            "--log-level",
            choices=["DEBUG", "INFO", "WARNING", "ERROR"],
            default="INFO",
            help="Set logging level",
        )

        # Add subcommands
        subparsers = parser.add_subparsers(dest="command", help="Available commands", metavar="COMMAND")

        # Run command (unified simulation)
        self._add_run_command(subparsers)

        # Explain command (routing transparency)
        self._add_explain_command(subparsers)

        # Predict command (performance estimates)
        self._add_predict_command(subparsers)

        # Benchmark command (performance analysis)
        self._add_benchmark_new_command(subparsers)

        # Learn command (educational tools)
        self._add_learn_command(subparsers)

        # Install command
        self._add_install_command(subparsers)

        # Doctor command (system diagnostics)
        self._add_doctor_command(subparsers)

        # Version command (detailed version info)
        self._add_version_command(subparsers)

        # Quickstart command (interactive demo)
        self._add_quickstart_command(subparsers)

        # Datasets command (list/generate)
        self._add_datasets_command(subparsers)

        # Reproducibility command (cross-backend validation)
        self._add_repro_command(subparsers)

        # Backward compatibility - keep original commands with deprecation warnings
        self._add_simulate_command(subparsers)
        self._add_config_command(subparsers)
        self._add_status_command(subparsers)
        self._add_benchmark_suite_command(subparsers)
        self._add_education_command(subparsers)
        self._add_learning_command(subparsers)

        return parser

    def _add_run_command(self, subparsers: "_SubParsersAction[ArgumentParser]") -> None:
        """Add the run command (unified simulation)."""
        parser = subparsers.add_parser(
            "run",
            help="Run a quantum circuit simulation",
            description="Simulate a quantum circuit with automatic backend selection",
            epilog="Examples:\n  ariadne run circuit.qasm\n  ariadne run circuit.qasm --shots 10000\n  ariadne run circuit.qasm --backend qiskit",
        )

        parser.add_argument("circuit", help="Path to quantum circuit file (QASM or QPY format)")

        parser.add_argument("--shots", type=int, default=1024, help="Number of measurement shots (default: 1024)")

        parser.add_argument(
            "--backend",
            choices=CLI_BACKEND_CHOICES,
            help="Backend to use for simulation (default: auto-select)",
        )

        parser.add_argument("--output", help="Output file for results (JSON format)")

        parser.add_argument("--config", help="Configuration file path")

        parser.add_argument("--explain", action="store_true", help="Show routing explanation")
        parser.add_argument("--predict-route", action="store_true", help="Use predictor to choose backend")
        parser.add_argument("--hybrid", action="store_true", help="Prefer hybrid planner (advisory)")

    def _add_explain_command(self, subparsers: "_SubParsersAction[ArgumentParser]") -> None:
        """Add the explain command (routing transparency)."""
        parser = subparsers.add_parser(
            "explain",
            help="Explain quantum circuit routing decision",
            description="Get detailed explanation of why a circuit would be routed to a specific backend",
        )

        parser.add_argument("circuit", help="Path to quantum circuit file (QASM or QPY format)")

        parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed technical explanation")

    def _add_benchmark_new_command(self, subparsers: "_SubParsersAction[ArgumentParser]") -> None:
        """Add the new simplified benchmark command (performance analysis)."""
        parser = subparsers.add_parser(
            "benchmark",
            help="Run performance benchmarks",
            description="Run performance benchmarks for backends",
        )

        parser.add_argument("--circuit", help="Path to quantum circuit file for benchmarking")

        parser.add_argument("--shots", type=int, default=1000, help="Number of measurement shots (default: 1000)")

        parser.add_argument(
            "--backend",
            choices=CLI_BACKEND_CHOICES,
            help="Backend to benchmark (default: all available)",
        )

        parser.add_argument("--iterations", type=int, default=5, help="Number of benchmark iterations (default: 5)")

        parser.add_argument("--output", help="Output file for benchmark results (JSON format)")

    # Removed legacy duplicate benchmark parser to avoid confusion

    def _add_learn_command(self, subparsers: "_SubParsersAction[ArgumentParser]") -> None:
        """Add the learn command (educational tools)."""
        try:
            from ..algorithms import list_algorithms

            available_algorithms = list_algorithms()
        except Exception:
            available_algorithms = ["bell", "ghz", "qft", "grover", "qpe", "steane"]

        parser = subparsers.add_parser(
            "learn",
            help="Interactive learning tools",
            description="Educational tools for learning quantum algorithms and concepts",
        )

        learn_subparsers = parser.add_subparsers(dest="learn_action", help="Learning actions")

        # Algorithm demo command
        demo_parser = learn_subparsers.add_parser("demo", help="Run algorithm demos")
        demo_parser.add_argument(
            "algorithm",
            choices=available_algorithms,
            help=f"Algorithm to demonstrate: {', '.join(available_algorithms)}",
            nargs="?",  # Make it optional so we can show help
        )
        demo_parser.add_argument("--qubits", type=int, default=3, help="Number of qubits for the demonstration")
        demo_parser.add_argument("--verbose", action="store_true", help="Show detailed execution information")

        # Learning quizzes
        quiz_parser = learn_subparsers.add_parser("quiz", help="Take quantum computing quizzes")
        quiz_parser.add_argument(
            "topic", choices=["gates", "algorithms", "applications", "hardware"], help="Topic for the quiz", nargs="?"
        )

    def _add_install_command(self, subparsers: "_SubParsersAction[ArgumentParser]") -> None:
        """Add install command."""
        parser = subparsers.add_parser(
            "install",
            help="Install optional components for acceleration",
            description="Install optional components based on system capabilities",
            epilog="Examples:\n  ariadne install --accelerate\n  ariadne install cuda apple\n  ariadne install --list\n  ariadne install --dry-run --accelerate",
        )

        parser.add_argument(
            "--accelerate", action="store_true", help="Install all available acceleration packages for current system"
        )

        parser.add_argument(
            "packages",
            nargs="*",
            help="Specific packages to install (e.g., cuda apple tensor_network)",
        )

        parser.add_argument("--list", action="store_true", help="List available packages for current system")

        parser.add_argument(
            "--dry-run", action="store_true", help="Show what would be installed without actually installing"
        )

        parser.add_argument("--force", action="store_true", help="Reinstall packages even if already installed")

    def _add_doctor_command(self, subparsers: "_SubParsersAction[ArgumentParser]") -> None:
        """Add doctor command for system diagnostics."""
        parser = subparsers.add_parser(
            "doctor",
            help="Run system diagnostics and health checks",
            description="Check system configuration, backend availability, and provide troubleshooting guidance",
            epilog="Examples:\n  ariadne doctor\n  ariadne doctor --verbose",
        )

        parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed diagnostic information")

    def _add_version_command(self, subparsers: "_SubParsersAction[ArgumentParser]") -> None:
        """Add version command for detailed version information."""
        parser = subparsers.add_parser(
            "version",
            help="Show detailed version and system information",
            description="Display Ariadne version, dependencies, and platform information",
            epilog="Examples:\n  ariadne version\n  ariadne version --verbose",
        )

        parser.add_argument(
            "--verbose", "-v", action="store_true", help="Show dependency versions and detailed system information"
        )

    def _add_quickstart_command(self, subparsers: "_SubParsersAction[ArgumentParser]") -> None:
        """Add quickstart command for interactive demonstrations."""
        parser = subparsers.add_parser(
            "quickstart",
            help="Interactive quickstart demonstrations",
            description="Run interactive demonstrations of quantum algorithms with automatic backend selection",
            epilog="Examples:\n  ariadne quickstart\n  ariadne quickstart --algorithm bell\n  ariadne quickstart --list",
        )

        parser.add_argument(
            "--algorithm",
            "-a",
            choices=["bell", "ghz", "grover", "qft", "vqe"],
            help="Run specific algorithm demonstration",
        )

        parser.add_argument("--list", action="store_true", help="List available quickstart algorithms")

        parser.add_argument("--shots", "-s", type=int, default=1024, help="Number of measurement shots (default: 1024)")

    def _add_simulate_command(self, subparsers: "_SubParsersAction[ArgumentParser]") -> None:
        """Add the simulate command."""
        parser = subparsers.add_parser(
            "simulate",
            help="Simulate a quantum circuit",
            description="Simulate a quantum circuit using the specified backend",
        )

        parser.add_argument("circuit", help="Path to quantum circuit file (QASM or QPY format)")

        parser.add_argument("--shots", type=int, default=1024, help="Number of measurement shots (default: 1024)")

        parser.add_argument(
            "--backend",
            choices=CLI_BACKEND_CHOICES,
            help="Backend to use for simulation",
        )

        parser.add_argument("--output", help="Output file for results (JSON format)")

        parser.add_argument("--config", help="Configuration file path")
        parser.add_argument("--predict-route", action="store_true", help="Use predictor to choose backend")
        parser.add_argument("--hybrid", action="store_true", help="Prefer hybrid planner (advisory)")

    def _add_predict_command(self, subparsers: "_SubParsersAction[ArgumentParser]") -> None:
        """Add the predict command (performance estimates)."""
        parser = subparsers.add_parser(
            "predict",
            help="Predict performance across backends",
            description="Estimate time/memory/success rate across available backends and suggest the best",
        )
        parser.add_argument("circuit", help="Path to quantum circuit file (QASM or QPY)")
        parser.add_argument("--backends", help="Comma-separated backends to consider (defaults to available)")
        parser.add_argument("--optimize-for", choices=["time", "memory", "success"], default="time")

    def _add_config_command(self, subparsers: "_SubParsersAction[ArgumentParser]") -> None:
        """Add the config command."""
        parser = subparsers.add_parser(
            "config",
            help="Manage configuration",
            description="Create, validate, or show configuration",
        )

        config_subparsers = parser.add_subparsers(dest="config_action", help="Configuration actions")

        # Create command
        create_parser = config_subparsers.add_parser("create", help="Create a configuration file")

        create_parser.add_argument(
            "--template",
            choices=["default", "development", "production"],
            default="default",
            help="Configuration template to use",
        )

        create_parser.add_argument(
            "--format",
            choices=["yaml", "json", "toml"],
            default="yaml",
            help="Configuration file format",
        )

        create_parser.add_argument("--output", required=True, help="Output file path")

        # Validate command
        validate_parser = config_subparsers.add_parser("validate", help="Validate a configuration file")

        validate_parser.add_argument("config_file", help="Configuration file to validate")

        # Show command
        show_parser = config_subparsers.add_parser("show", help="Show current configuration")

        show_parser.add_argument("--format", choices=["yaml", "json"], default="yaml", help="Output format")

    def _add_status_command(self, subparsers: "_SubParsersAction[ArgumentParser]") -> None:
        """Add the status command."""
        parser = subparsers.add_parser(
            "status",
            help="Show system status",
            description="Show status of backends, pools, and system resources",
        )

        parser.add_argument("--backend", help="Show status for specific backend only")

        parser.add_argument("--detailed", action="store_true", help="Show detailed status information")

    # Legacy duplicate benchmark parser removed

    def _add_benchmark_suite_command(self, subparsers: "_SubParsersAction[ArgumentParser]") -> None:
        """Add the benchmark-suite command."""
        # Get available algorithms for help text
        try:
            from ..algorithms import list_algorithms

            available_algorithms = list_algorithms()
        except Exception:
            available_algorithms = ["bell", "qaoa", "vqe", "stabilizer"]

        parser = subparsers.add_parser(
            "benchmark-suite",
            help="Run comprehensive benchmark suite",
            description="Run comprehensive benchmark suite across algorithms and backends",
        )

        parser.add_argument(
            "--algorithms",
            help=f"Comma-separated list of algorithms to test (e.g., bell,qaoa,vqe,qft,grover,qpe,steane). Available: {', '.join(available_algorithms)}",
        )

        parser.add_argument(
            "--backends",
            help="Comma-separated list of backends to test (e.g., auto,stim,qiskit,mps)",
        )

        parser.add_argument("--shots", type=int, default=1000, help="Number of measurement shots (default: 1000)")

        parser.add_argument("--output", help="Output file for benchmark results (JSON format)")

    def _add_education_command(self, subparsers: "_SubParsersAction[ArgumentParser]") -> None:
        """Add the education command for learning quantum algorithms."""
        try:
            from ..algorithms import list_algorithms

            available_algorithms = list_algorithms()
        except Exception:
            available_algorithms = ["bell", "ghz", "qft", "grover", "qpe", "vqe", "qaoa"]

        parser = subparsers.add_parser(
            "education",
            help="Educational tools for learning quantum algorithms",
            description="Interactive educational tools for learning quantum algorithms and concepts",
        )

        education_subparsers = parser.add_subparsers(dest="education_action", help="Education actions")

        # Algorithm demo command
        demo_parser = education_subparsers.add_parser("demo", help="Run algorithm demos")
        demo_parser.add_argument(
            "algorithm",
            choices=available_algorithms,
            help=f"Algorithm to demonstrate: {', '.join(available_algorithms)}",
        )
        demo_parser.add_argument("--qubits", type=int, default=3, help="Number of qubits for the demonstration")
        demo_parser.add_argument("--verbose", action="store_true", help="Show detailed execution information")

        # Learning quizzes
        quiz_parser = education_subparsers.add_parser("quiz", help="Take quantum computing quizzes")
        quiz_parser.add_argument(
            "topic", choices=["gates", "algorithms", "applications", "hardware"], help="Topic for the quiz"
        )

        # Circuit visualization
        viz_parser = education_subparsers.add_parser("visualize", help="Visualize quantum circuits")
        viz_parser.add_argument("circuit_file", help="Path to circuit file to visualize")
        viz_parser.add_argument(
            "--format", choices=["text", "image", "latex"], default="text", help="Visualization format"
        )

    def _add_learning_command(self, subparsers: "_SubParsersAction[ArgumentParser]") -> None:
        """Add the learning command for educational resources."""
        parser = subparsers.add_parser(
            "learning",
            help="Learning resources and tools",
            description="Access educational materials and learning resources",
        )

        learning_subparsers = parser.add_subparsers(dest="learning_action", help="Learning actions")

        # List available learning materials
        list_parser = learning_subparsers.add_parser("list", help="List available learning resources")
        list_parser.add_argument(
            "--category",
            choices=["tutorials", "algorithms", "papers", "videos", "all"],
            default="all",
            help="Category of resources to list",
        )

        # Get detailed information about a resource
        info_parser = learning_subparsers.add_parser("info", help="Get detailed information about a learning resource")
        info_parser.add_argument("resource_name", help="Name of the learning resource")

    def _cmd_install(self, args: argparse.Namespace) -> int:
        """Execute the install command."""
        try:
            from .install import Installer
        except ImportError:
            if self.logger:
                self.logger.error("Install module not available")
            print("Error: Install module not available")
            return 1

        installer = Installer(dry_run=args.dry_run, force=args.force)

        if args.list:
            return installer.list_available()
        elif args.accelerate:
            return installer.install_accelerate()
        elif args.packages:
            return installer.install_specific(args.packages)
        else:
            print("No action specified. Use --help for options.")
            return 1

    def _cmd_doctor(self, args: argparse.Namespace) -> int:
        """Execute the doctor command for system diagnostics."""
        print("Ariadne System Diagnostics")
        print("=" * 25)

        # System information
        print(f"✓ Python version: {sys.version.split()[0]}")
        print(f"✓ Ariadne: {__version__}")
        print(f"✓ Platform: {platform.system()} {platform.release()} ({platform.machine()})")

        # Memory information
        memory = psutil.virtual_memory()
        print(f"✓ Memory: {memory.total // (1024**3)} GB available")

        print("✓ Available backends:")

        # Check backend availability with simple import tests
        backend_tests = [
            ("qiskit", "import qiskit", "Core quantum simulation"),
            ("stim", "import stim", "Clifford circuit simulation"),
            ("cuda", "import cupy", "NVIDIA GPU acceleration - run: pip install ariadne-router[cuda]"),
            (
                "metal",
                "import jax; from jax.lib import xla_bridge",
                "Apple Silicon acceleration - run: pip install ariadne-router[apple]",
            ),
            (
                "tensor_network",
                "import tensornetwork",
                "Tensor network simulation - run: pip install ariadne-router[quantum_platforms]",
            ),
            ("mps", "import qtealeaves", "Matrix product state simulation - run: pip install ariadne-router[advanced]"),
        ]

        for name, test_code, description in backend_tests:
            try:
                exec(test_code)
                if name == "metal":
                    # Additional check for Apple Silicon
                    if platform.system() == "Darwin" and "arm64" in platform.machine().lower():
                        print(f"  ✓ {name} (ready - Apple Silicon detected)")
                    else:
                        print(f"  ⚠ {name} (not supported - requires Apple Silicon)")
                else:
                    print(f"  ✓ {name} (ready)")
            except ImportError:
                install_cmd = description.split(" - run: ")[-1] if " - run: " in description else f"pip install {name}"
                print(f"  ✗ {name} (not installed - run: {install_cmd})")
            except Exception as e:
                print(f"  ✗ {name} (error: {str(e)[:40]}...)")

        if args.verbose:
            print("\nDetailed Information:")
            print("--------------------")
            try:
                # CPU information
                print(f"CPU cores: {psutil.cpu_count(logical=False)} physical, {psutil.cpu_count()} logical")
                print(f"CPU usage: {psutil.cpu_percent(interval=1):.1f}%")

                # Memory details
                memory = psutil.virtual_memory()
                print(
                    f"Memory: {memory.used // (1024**3):.1f}GB used / {memory.total // (1024**3):.1f}GB total ({memory.percent:.1f}%)"
                )

                # Python packages
                print("\nKey dependencies:")
                packages = ["qiskit", "stim", "numpy", "jax", "cupy", "tensornetwork"]
                for package in packages:
                    try:
                        module = __import__(package)
                        version = getattr(module, "__version__", "unknown")
                        print(f"  {package}: {version}")
                    except ImportError:
                        print(f"  {package}: not installed")

            except Exception as e:
                print(f"Error getting detailed info: {e}")

        print("\nAll systems operational!")
        return 0

    def _cmd_version(self, args: argparse.Namespace) -> int:
        """Execute the version command for detailed version information."""
        print(f"Ariadne {__version__}")
        print(f"Python {sys.version.split()[0]} on {platform.system()} {platform.release()} ({platform.machine()})")

        # Count available backends
        available_backends = []
        backend_tests = [
            ("qiskit", "import qiskit"),
            ("stim", "import stim"),
            ("metal", "import jax"),
            ("cuda", "import cupy"),
            ("tensor_network", "import tensornetwork"),
            ("mps", "import qtealeaves"),
        ]

        for name, test_code in backend_tests:
            try:
                exec(test_code)
                if name == "metal":
                    # Only count Metal if on Apple Silicon
                    if platform.system() == "Darwin" and "arm64" in platform.machine().lower():
                        available_backends.append(name)
                else:
                    available_backends.append(name)
            except ImportError:
                pass

        print(f"\nAvailable backends: {', '.join(available_backends)}")

        # Platform-specific information
        if platform.system() == "Darwin" and "arm64" in platform.machine().lower():
            print("Platform: Apple Silicon")
        elif platform.system() == "Darwin":
            print("Platform: Intel Mac")
        elif platform.system() == "Linux":
            print("Platform: Linux")
        elif platform.system() == "Windows":
            print("Platform: Windows")
        else:
            print(f"Platform: {platform.system()}")

        if args.verbose:
            print("\nDependency versions:")
            packages = [
                "qiskit",
                "stim",
                "numpy",
                "scipy",
                "jax",
                "cupy",
                "tensornetwork",
                "qtealeaves",
                "matplotlib",
                "yaml",
            ]
            for package in packages:
                try:
                    if package == "yaml":
                        import yaml

                        module = yaml
                        package_name = "PyYAML"
                    else:
                        module = __import__(package)
                        package_name = package
                    version = getattr(module, "__version__", "unknown")
                    print(f"  {package_name}: {version}")
                except ImportError:
                    print(f"  {package}: not installed")

            # System information
            print("\nSystem information:")
            try:
                print(f"  CPU cores: {psutil.cpu_count(logical=False)} physical, {psutil.cpu_count()} logical")
                memory = psutil.virtual_memory()
                print(f"  Memory: {memory.total // (1024**3)} GB total")
                disk = psutil.disk_usage("/")
                print(f"  Disk: {disk.free // (1024**3)} GB free / {disk.total // (1024**3)} GB total")
            except Exception:
                print("  System details unavailable")
        else:
            print("\nUse --verbose for dependency versions")

        return 0

    def _cmd_quickstart(self, args: argparse.Namespace) -> int:
        """Execute the quickstart command for interactive demonstrations."""

        algorithms = {
            "bell": "Bell State - Quantum entanglement demonstration",
            "ghz": "GHZ State - Multi-qubit entanglement",
            "grover": "Grover's Algorithm - Quantum search",
            "qft": "Quantum Fourier Transform - Quantum signal processing",
            "vqe": "Variational Quantum Eigensolver - Quantum chemistry",
        }

        if args.list:
            print("Available Quickstart Algorithms:")
            print("=" * 33)
            for name, description in algorithms.items():
                print(f"  {name:<8} - {description}")
            return 0

        if args.algorithm:
            return self._run_quickstart_algorithm(args.algorithm, args.shots)

        # Interactive mode
        print("Welcome to Ariadne Quickstart!")
        print("=" * 30)
        print()
        print("Choose a quantum algorithm demonstration:")
        for i, (name, desc) in enumerate(algorithms.items(), 1):
            print(f"  {i}. {name.upper()}: {desc}")
        print("  0. Exit")
        print()

        try:
            choice = input("Enter your choice (0-5): ").strip()
            if choice == "0":
                print("Goodbye!")
                return 0

            if choice.isdigit():
                choice_num = int(choice)
                if 1 <= choice_num <= len(algorithms):
                    algorithm_name = list(algorithms.keys())[choice_num - 1]
                    return self._run_quickstart_algorithm(algorithm_name, args.shots)

            print("Invalid choice. Please enter a number between 0 and 5.")
            return 1

        except KeyboardInterrupt:
            print("\nGoodbye!")
            return 0
        except EOFError:
            print("\nGoodbye!")
            return 0

    def _run_quickstart_algorithm(self, algorithm: str, shots: int) -> int:
        """Run a specific quickstart algorithm demonstration."""
        try:
            from qiskit import QuantumCircuit

            print(f"\n🚀 Running {algorithm.upper()} Algorithm Demonstration")
            print("=" * 50)

            # Create the circuit based on algorithm
            if algorithm == "bell":
                qc = QuantumCircuit(2, 2)
                qc.h(0)
                qc.cx(0, 1)
                qc.measure(0, 0)
                qc.measure(1, 1)
                print("Creating Bell state (maximally entangled 2-qubit state)...")

            elif algorithm == "ghz":
                qc = QuantumCircuit(3, 3)
                qc.h(0)
                qc.cx(0, 1)
                qc.cx(1, 2)
                qc.measure(0, 0)
                qc.measure(1, 1)
                qc.measure(2, 2)
                print("Creating GHZ state (3-qubit entangled state)...")

            elif algorithm == "grover":
                qc = QuantumCircuit(2, 2)
                # Grover's algorithm for 2 qubits
                qc.h([0, 1])  # Superposition
                qc.cz(0, 1)  # Oracle (marks |11⟩)
                qc.h([0, 1])  # Hadamard
                qc.z([0, 1])  # Phase flip
                qc.cz(0, 1)  # Controlled-Z
                qc.h([0, 1])  # Hadamard
                qc.measure(0, 0)
                qc.measure(1, 1)
                print("Running Grover's search for marked state |11⟩...")

            elif algorithm == "qft":
                qc = QuantumCircuit(3, 3)
                # Simple QFT on 3 qubits
                qc.h(0)
                qc.cp(3.14159 / 2, 0, 1)
                qc.cp(3.14159 / 4, 0, 2)
                qc.h(1)
                qc.cp(3.14159 / 2, 1, 2)
                qc.h(2)
                qc.swap(0, 2)
                qc.measure(0, 0)
                qc.measure(1, 1)
                qc.measure(2, 2)
                print("Applying Quantum Fourier Transform...")

            elif algorithm == "vqe":
                qc = QuantumCircuit(2, 2)
                # Simple VQE ansatz
                import math

                qc.ry(math.pi / 4, 0)
                qc.ry(math.pi / 4, 1)
                qc.cx(0, 1)
                qc.ry(math.pi / 8, 0)
                qc.ry(math.pi / 8, 1)
                qc.measure(0, 0)
                qc.measure(1, 1)
                print("Running VQE circuit (hydrogen molecule simulation)...")

            else:
                print(f"Algorithm '{algorithm}' not implemented yet.")
                return 1

            # Simulate with Ariadne
            print(f"Simulating with {shots} shots...")

            start_time = time.time()
            result = simulate(qc, shots=shots)
            end_time = time.time()

            # Display results
            print("\n✅ Simulation Complete!")
            print(f"Backend used: {result.backend_used}")
            print(f"Execution time: {end_time - start_time:.3f}s")
            print(f"Circuit depth: {qc.depth()}")
            print(f"Number of qubits: {qc.num_qubits}")

            print(f"\nMeasurement Results ({shots} shots):")
            counts = dict(result.counts)
            for state, count in sorted(counts.items()):
                percentage = (count / shots) * 100
                print(f"  |{state}⟩: {count:4d} ({percentage:5.1f}%)")

            # Explain the routing
            print("\n🧭 Routing Explanation:")
            print(f"Ariadne selected the '{result.backend_used}' backend because:")

            from ..types import BackendType

            if result.backend_used == BackendType.STIM:
                print("  - This circuit is Clifford (contains only H, CNOT, CZ gates)")
                print("  - Stim is optimized for stabilizer circuit simulation")
            elif result.backend_used == BackendType.QISKIT:
                print("  - This circuit contains non-Clifford gates")
                print("  - Qiskit Aer provides full quantum simulation capabilities")
            elif result.backend_used == BackendType.JAX_METAL:
                print("  - Apple Silicon Metal acceleration was available")
                print("  - Hardware acceleration improves performance")

            print(f"\n💡 To run this again: ariadne quickstart --algorithm {algorithm}")
            print(f"💡 To try different shots: ariadne quickstart --algorithm {algorithm} --shots 2048")

            return 0

        except ImportError as e:
            print(f"Error: Missing dependency: {e}")
            print("Run 'ariadne doctor' to check your installation.")
            return 1
        except Exception as e:
            print(f"Error running demonstration: {e}")
            if self.logger:
                self.logger.error(f"Quickstart error: {e}")
            return 1

    def _add_datasets_command(self, subparsers: "_SubParsersAction[ArgumentParser]") -> None:
        """Add the datasets command (list/generate)."""
        parser = subparsers.add_parser(
            "datasets",
            help="Manage benchmark datasets",
            description="List or generate benchmark dataset circuits (OpenQASM 2.0)",
            epilog="Examples:\n  ariadne datasets list\n  ariadne datasets generate --family all --sizes 10,20,30,40,50\n  ariadne datasets generate --family vqe_hea --sizes 10,20 --depth 3\n  ariadne datasets generate --family qft --output-dir ~/.ariadne/datasets",
        )
        sub = parser.add_subparsers(dest="datasets_action", help="Dataset actions")

        p_list = sub.add_parser("list", help="List available dataset files")
        p_list.add_argument("--dir", dest="dir", help="Directory to list (defaults to repo or ~/.ariadne/datasets)")

        p_gen = sub.add_parser("generate", help="Generate dataset circuits")
        p_gen.add_argument(
            "--family",
            choices=["ghz", "qft", "vqe_hea", "all"],
            default="all",
            help="Circuit family to generate",
        )
        p_gen.add_argument(
            "--sizes",
            default="10,20,30,40,50",
            help="Comma-separated qubit sizes (e.g., 10,20,30)",
        )
        p_gen.add_argument(
            "--depth",
            type=int,
            default=2,
            help="Depth for VQE HEA (ignored for GHZ/QFT)",
        )
        p_gen.add_argument("--output-dir", help="Directory to write datasets (defaults to repo or ~/.ariadne/datasets)")

    def _cmd_datasets(self, args: argparse.Namespace) -> int:
        """Execute the datasets command."""
        from ..datasets import DEFAULT_SIZES, generate_datasets, resolve_datasets_dir

        if args.datasets_action == "list":
            target = resolve_datasets_dir(args.dir)
            files = sorted(target.glob("*.qasm*"))
            print(f"Dataset directory: {target}")
            if not files:
                print("No dataset files found. Use 'ariadne datasets generate' to create some.")
                return 0
            for p in files:
                print(f"- {p.name}")
            return 0

        if args.datasets_action == "generate":
            if args.sizes.strip().lower() == "all":
                sizes = list(DEFAULT_SIZES)
            else:
                try:
                    sizes = [int(s.strip()) for s in args.sizes.split(",") if s.strip()]
                except ValueError:
                    print("Invalid --sizes. Use comma-separated integers or 'all'.")
                    return 2

            written = generate_datasets(
                families=[args.family],
                sizes=sizes,
                depth=getattr(args, "depth", 2),
                output_dir=args.output_dir,
            )
            print(
                f"Wrote {len(written)} files to {written[0].parent if written else resolve_datasets_dir(args.output_dir)}"
            )
            for p in written:
                print(f"- {p.name}")
            return 0

        print("No action specified. Use --help for options.")
        return 1

    def _add_repro_command(self, subparsers: "_SubParsersAction[ArgumentParser]") -> None:
        """Add the reproducibility (cross-validation) command."""
        parser = subparsers.add_parser(
            "repro",
            help="Cross-validate results across backends",
            description="Run a circuit across multiple backends and compare distributions",
            epilog="Examples:\n  ariadne repro --circuit ghz_20\n  ariadne repro --circuit benchmarks/datasets/qft_10.qasm2 --backends qiskit,tensor_network --shots 2000\n  ariadne repro --circuit vqe_hea_d2_10 --tolerance 0.08 --output report.json",
        )
        parser.add_argument("--circuit", required=True, help="Dataset name or QASM file path")
        parser.add_argument("--backends", help="Comma-separated backends (defaults to a sensible set)")
        parser.add_argument("--shots", type=int, default=1000, help="Number of shots per backend")
        parser.add_argument("--tolerance", type=float, default=0.05, help="JSD tolerance for consistency")
        parser.add_argument("--metric", choices=["jsd"], default="jsd", help="Distance metric")
        parser.add_argument("--output", help="Write full JSON report to file")
        parser.add_argument("--export-csv", dest="export_csv", help="Export pairwise distances to CSV path")
        parser.add_argument("--export-md", dest="export_md", help="Export a Markdown summary to path")
        parser.add_argument("--export-html", dest="export_html", help="Export an HTML summary to path")
        parser.add_argument("--json", action="store_true", help="Print JSON report to stdout")
        parser.add_argument("--pretty", action="store_true", help="Pretty-print a summary")

    def _cmd_run(self, args: argparse.Namespace) -> int:
        """Execute the run command (unified simulation)."""
        # This is essentially the same as simulate but with better UX
        return self._cmd_simulate(args)

    def _cmd_explain(self, args: argparse.Namespace) -> int:
        """Execute the explain command (routing transparency)."""
        progress = ProgressIndicator("Loading circuit")
        progress.start()

        try:
            # Load circuit
            circuit = self._load_circuit(args.circuit)
            progress.update(f" ({circuit.num_qubits} qubits, {circuit.depth()} depth)")
            progress.finish("loaded")
        except Exception as e:
            progress.finish("failed")
            if self.logger:
                self.logger.error(f"Failed to load circuit: {e}")
            return 1

        try:
            from ..route.routing_tree import explain_routing

            print(f"\nRouting Analysis for {args.circuit}:")
            print("=" * 50)

            explanation = explain_routing(circuit)
            print(explanation)

            if getattr(args, "verbose", False):
                print("\nDetailed Technical Analysis:")
                print("-" * 30)
                print("Circuit properties:")
                print(f"  Qubits: {circuit.num_qubits}")
                print(f"  Depth: {circuit.depth()}")
                print(f"  Operations: {circuit.count_ops()}")

                # Check if it's Clifford
                try:
                    from qiskit.quantum_info import Clifford

                    Clifford.from_circuit(circuit)
                    print("  Type: Clifford (stabilizer)")
                except Exception:
                    print("  Type: Non-Clifford (general)")

            return 0

        except Exception as e:
            if self.logger:
                self.logger.error(f"Routing explanation failed: {e}")
            return 1

    def _cmd_repro(self, args: argparse.Namespace) -> int:
        """Execute the reproducibility command."""
        import json

        try:
            from ..reproducibility import cross_validate, default_backends
        except Exception:
            if self.logger:
                self.logger.error("Reproducibility module not available")
            print("Error: reproducibility module not available")
            return 1

        bk = None
        if args.backends:
            bk = [b.strip() for b in args.backends.split(",") if b.strip()]
        else:
            bk = default_backends()

        try:
            from typing import Any, cast

            report: dict[str, Any] = cross_validate(
                args.circuit,
                backends=bk,
                shots=args.shots,
                tolerance=args.tolerance,
                metric=args.metric,
            )
        except Exception as e:
            if self.logger:
                self.logger.error(f"Reproducibility failed: {e}")
            return 1

        if args.output:
            try:
                Path(args.output).write_text(json.dumps(report, indent=2))
                print(f"Wrote report to {args.output}")
            except Exception as e:
                print(f"Failed to write output: {e}")

        # Optional exports
        if args.export_csv:
            try:
                import csv

                with open(args.export_csv, "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["pair", "distance"])
                    distances = cast(dict[str, float], report.get("distances", {}))
                    for k, v in sorted(distances.items()):
                        writer.writerow([k, f"{v:.6f}"])
                print(f"Wrote CSV to {args.export_csv}")
            except Exception as e:
                print(f"Failed to write CSV: {e}")

        if args.export_md:
            try:
                lines = []
                lines.append("# Reproducibility Report")
                lines.append("")
                lines.append(f"- Circuit: `{args.circuit}`")
                lines.append(f"- Backends: {', '.join(bk)}")
                lines.append(f"- Metric: {report['metric']}")
                lines.append(f"- Tolerance: {report['tolerance']}")
                lines.append(f"- Consistent: {report['consistent']}")
                lines.append(f"- Max distance: {report['max_distance']:.6f}")
                distances = cast(dict[str, float], report.get("distances", {}))
                if distances:
                    lines.append("")
                    lines.append("## Pairwise distances")
                    for k, v in sorted(distances.items()):
                        lines.append(f"- {k}: {v:.6f}")
                Path(args.export_md).write_text("\n".join(lines))
                print(f"Wrote Markdown to {args.export_md}")
            except Exception as e:
                print(f"Failed to write Markdown: {e}")

        if args.export_html:
            try:
                html = []
                html.append("<!DOCTYPE html>")
                html.append('<html lang="en"><head><meta charset="utf-8"><title>Reproducibility Report</title>')
                html.append(
                    "<style>body{font-family:system-ui,Arial,sans-serif;margin:24px} table{border-collapse:collapse} td,th{border:1px solid #ddd;padding:6px 10px} th{background:#f6f8fa}</style>"
                )
                html.append("</head><body>")
                html.append("<h1>Reproducibility Report</h1>")
                html.append(
                    f"<p><b>Circuit:</b> <code>{args.circuit}</code><br>"
                    f"<b>Backends:</b> {', '.join(bk)}<br>"
                    f"<b>Metric:</b> {report['metric']} &nbsp; <b>Tolerance:</b> {report['tolerance']}<br>"
                    f"<b>Consistent:</b> {report['consistent']} &nbsp; <b>Max distance:</b> {report['max_distance']:.6f}</p>"
                )
                distances = cast(dict[str, float], report.get("distances", {}))
                if distances:
                    html.append("<h2>Pairwise distances</h2>")
                    html.append("<table><thead><tr><th>Pair</th><th>Distance</th></tr></thead><tbody>")
                    for k, v in sorted(distances.items()):
                        html.append(f"<tr><td>{k}</td><td>{v:.6f}</td></tr>")
                    html.append("</tbody></table>")
                html.append("</body></html>")
                Path(args.export_html).write_text("\n".join(html), encoding="utf-8")
                print(f"Wrote HTML to {args.export_html}")
            except Exception as e:
                print(f"Failed to write HTML: {e}")

        if args.json:
            print(json.dumps(report, indent=2))
        else:
            # concise summary
            print("Reproducibility Report")
            print("=" * 23)
            print(f"Circuit: {args.circuit}")
            print(f"Backends: {', '.join(bk)}")
            print(f"Metric: {report['metric']} | Tolerance: {report['tolerance']}")
            print(f"Consistent: {report['consistent']}")
            print(f"Max distance: {report['max_distance']:.4f}")
            distances = cast(dict[str, float], report.get("distances", {}))
            if args.pretty and distances:
                print("\nPairwise distances:")
                for k, v in sorted(distances.items()):
                    print(f"- {k}: {v:.4f}")

        return 0

    def _cmd_simulate(self, args: argparse.Namespace) -> int:
        """Execute the simulate command."""
        progress = ProgressIndicator("Loading circuit")
        progress.start()

        try:
            # Load circuit
            circuit = self._load_circuit(args.circuit)
            progress.update(f" ({circuit.num_qubits} qubits, {circuit.depth()} depth)")
            progress.finish("loaded")
        except Exception as e:
            progress.finish("failed")
            if self.logger:
                self.logger.error(f"Failed to load circuit: {e}")
            return 1

        # Load configuration if specified
        config = {}
        if args.config:
            try:
                config = load_config(config_paths=[args.config])
                if self.logger:
                    self.logger.info(f"Loaded configuration from {args.config}")
                config_keys = _describe_config_keys(config)
                if config_keys:
                    print(f"Using configuration keys: {config_keys}")
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Failed to load configuration: {e}")

        # Simulate circuit
        progress = ProgressIndicator("Simulating circuit")
        progress.start()

        try:
            # Enable optional predictor/hybrid modes via environment flags
            if getattr(args, "predict_route", False):
                os.environ["ARIADNE_ROUTING_PREDICT"] = "1"
            if getattr(args, "hybrid", False):
                os.environ["ARIADNE_ROUTING_HYBRID"] = "1"

            kwargs = {"shots": args.shots}
            if args.backend:
                kwargs["backend"] = self._resolve_backend_name(args.backend)

            result = simulate(circuit, **kwargs)
            progress.finish("complete")

            # Display results
            print("\nSimulation Results:")
            print(f"  Backend: {result.backend_used.value}")
            print(f"  Execution time: {result.execution_time:.4f}s")
            print(f"  Shots: {args.shots}")
            print(f"  Counts: {dict(list(result.counts.items())[:5])}")

            if len(result.counts) > 5:
                print(f"  ... and {len(result.counts) - 5} more")

            # Show fallback reason if present
            if result.fallback_reason:
                print(f"  Note: {result.fallback_reason}")

            # Save results if requested
            if args.output:
                self._save_results(result, args.output)
                print(f"  Results saved to: {args.output}")

            return 0

        except Exception as e:
            progress.finish("failed")

            # Provide friendly error messages for missing backends
            error_message = str(e).lower()
            if "cuda" in error_message and ("not available" in error_message or "not found" in error_message):
                print("\n❌ CUDA backend not available")
                print("💡 To enable CUDA support:")
                print("   pip install ariadne-router[cuda]")
                print("   (Requires NVIDIA GPU with CUDA drivers)")
            elif "metal" in error_message and ("not available" in error_message or "not found" in error_message):
                print("\n❌ JAX-Metal backend not available")
                print("💡 To enable JAX-Metal support:")
                print("   pip install ariadne-router[apple]")
                print("   (Requires Apple Silicon Mac: M1/M2/M3/M4)")
            elif "mps" in error_message or "tensor" in error_message:
                print("\n❌ Tensor network backend not available")
                print("💡 To enable tensor network support:")
                print("   pip install quimb cotengra")
            elif "stim" in error_message:
                print("\n❌ Stim backend not available")
                print("💡 To enable Stim support:")
                print("   pip install stim")
            else:
                if self.logger:
                    self.logger.error(f"Simulation failed: {e}")
                print(f"\n❌ Simulation failed: {e}")

            print("\n💡 Try using automatic backend selection (remove --backend flag)")
            return 1

    def _cmd_predict(self, args: argparse.Namespace) -> int:
        """Execute the predict command (performance estimates)."""
        try:
            circuit = self._load_circuit(args.circuit)
        except Exception as e:
            print(f"Failed to load circuit: {e}")
            return 1

        try:
            from ..route.performance_model import PerformancePredictor
            from ..route.routing_tree import get_available_backends
            from ..types import BackendType
        except Exception as e:
            print(f"Failed to import prediction modules: {e}")
            return 1

        predictor = PerformancePredictor()
        if args.backends:
            names = [b.strip() for b in args.backends.split(",") if b.strip()]
        else:
            names = get_available_backends()

        candidates: list[BackendType] = []
        for n in names:
            try:
                candidates.append(BackendType(n))
            except Exception:
                pass

        if not candidates:
            print("No valid backends to consider.")
            return 0

        results: list[tuple[BackendType, float, float, float]] = []
        for b in candidates:
            pred = predictor.predict_performance(circuit, b)
            results.append((b, pred.predicted_time, pred.predicted_memory_mb, pred.predicted_success_rate))

        # Choose based on optimize_for
        if args.optimize_for == "time":
            best = min(results, key=lambda r: r[1])
        elif args.optimize_for == "memory":
            best = min(results, key=lambda r: r[2])
        else:
            best = max(results, key=lambda r: r[3])

        print("Predicted Performance")
        print("=====================")
        print(f"Circuit: {args.circuit}")
        print(f"Backends considered: {', '.join(b.value for b, *_ in results)}")
        print("")
        print("Backend           Time (s)   Memory (MB)   Success")
        for b, t, m, s in results:
            print(f"{b.value:<16} {t:>8.3f}   {m:>11.1f}   {s:>6.2f}")
        print("")
        print(f"Recommended ({args.optimize_for}): {best[0].value}")
        return 0

    def _cmd_config(self, args: argparse.Namespace) -> int:
        """Execute the config command."""
        if args.config_action == "create":
            return self._cmd_config_create(args)
        elif args.config_action == "validate":
            return self._cmd_config_validate(args)
        elif args.config_action == "show":
            return self._cmd_config_show(args)
        else:
            if self.logger:
                self.logger.error(f"Unknown config action: {args.config_action}")
            return 1

    def _cmd_config_create(self, args: argparse.Namespace) -> int:
        """Execute the config create command."""
        progress = ProgressIndicator("Creating configuration")
        progress.start()

        try:
            # Get template
            if args.template == "default":
                template = create_default_template()
            elif args.template == "development":
                template = create_development_template()
            elif args.template == "production":
                template = create_production_template()
            else:
                progress.finish("failed")
                if self.logger:
                    self.logger.error(f"Unknown template: {args.template}")
                return 1

            # Get format
            if args.format == "yaml":
                format = ConfigFormat.YAML
            elif args.format == "json":
                format = ConfigFormat.JSON
            elif args.format == "toml":
                format = ConfigFormat.TOML
            else:
                progress.finish("failed")
                if self.logger:
                    self.logger.error(f"Unknown format: {args.format}")
                return 1

            # Save template
            template.save(args.output, format)
            progress.finish("created")

            print(f"Configuration template created: {args.output}")
            return 0

        except Exception as e:
            progress.finish("failed")
            if self.logger:
                self.logger.error(f"Failed to create configuration: {e}")
            return 1

    def _cmd_config_validate(self, args: argparse.Namespace) -> int:
        """Execute the config validate command."""
        progress = ProgressIndicator("Validating configuration")
        progress.start()

        try:
            # Load configuration
            config = load_config(config_paths=[args.config_file])
            progress.finish("valid")

            config_keys = _describe_config_keys(config)
            if config_keys:
                print(f"Configuration is valid: {args.config_file} (keys: {config_keys})")
            else:
                print(f"Configuration is valid: {args.config_file}")
            return 0

        except Exception as e:
            progress.finish("invalid")
            if self.logger:
                self.logger.error(f"Configuration validation failed: {e}")
            return 1

    def _cmd_config_show(self, args: argparse.Namespace) -> int:
        """Execute the config show command."""
        try:
            # Load current configuration
            config = load_config()

            # Display configuration
            if args.format == "json" or not YAML_AVAILABLE or yaml is None:
                import json

                print(json.dumps(config, indent=2))
            else:
                print(yaml.dump(config, default_flow_style=False, sort_keys=False))

            return 0

        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to show configuration: {e}")
            return 1

    def _cmd_status(self, args: argparse.Namespace) -> int:
        """Execute the status command."""
        print("Ariadne System Status")
        print("=" * 50)

        # Show backend status
        health_checker = get_health_checker()

        if args.backend:
            # Show specific backend status
            backend_type = self._parse_backend_type(args.backend)
            if backend_type:
                metrics = health_checker.get_backend_metrics(backend_type)
                if metrics:
                    self._print_backend_status(backend_type, metrics, args.detailed)
                else:
                    print(f"No status available for backend: {args.backend}")
            else:
                print(f"Unknown backend: {args.backend}")
                return 1
        else:
            # Show all backend status
            print("\nBackend Status:")
            print("-" * 30)

            for backend_type in self._get_available_backends():
                metrics = health_checker.get_backend_metrics(backend_type)
                if metrics:
                    self._print_backend_status(backend_type, metrics, args.detailed)

        # Show pool status
        print("\nBackend Pool Status:")
        print("-" * 30)

        pool_manager = get_pool_manager()
        pool_stats = pool_manager.get_all_statistics()

        if pool_stats:
            for backend_name, stats in pool_stats.items():
                print(f"{backend_name}:")
                print(f"  Total instances: {stats.total_instances}")
                print(f"  Active instances: {stats.active_instances}")
                print(f"  Available instances: {stats.available_instances}")
                print(f"  Success rate: {stats.success_rate:.2%}")
                print(f"  Average wait time: {stats.average_wait_time:.3f}s")
                print()
        else:
            print("No active pools")

        return 0

    def _cmd_benchmark(self, args: argparse.Namespace) -> int:
        """Execute the benchmark command."""
        # Load or create circuit
        if args.circuit:
            progress = ProgressIndicator("Loading circuit")
            progress.start()

            try:
                circuit = self._load_circuit(args.circuit)
                progress.update(f" ({circuit.num_qubits} qubits, {circuit.depth()} depth)")
                progress.finish("loaded")
            except Exception as e:
                progress.finish("failed")
                if self.logger:
                    self.logger.error(f"Failed to load circuit: {e}")
                return 1
        else:
            # Create benchmark circuit
            circuit = self._create_benchmark_circuit()
            print(f"Using benchmark circuit: {circuit.num_qubits} qubits, {circuit.depth()} depth")

        # Run benchmarks
        print(f"\nRunning benchmarks ({args.iterations} iterations, {args.shots} shots)...")
        print("=" * 60)

        backends = self._get_available_backends()
        if args.backend:
            backend_type = self._parse_backend_type(args.backend)
            if backend_type:
                backends = [backend_type]
            else:
                print(f"Unknown backend: {args.backend}")
                return 1

        results = {}

        for backend_type in backends:
            print(f"\nBenchmarking {backend_type.value}...")

            try:
                # Run benchmark iterations
                times = []
                success_count = 0

                for i in range(args.iterations):
                    try:
                        start_time = time.time()
                        result = simulate(circuit, shots=args.shots, backend=backend_type.value)
                        end_time = time.time()

                        times.append(end_time - start_time)
                        success_count += 1

                        print(f"  Iteration {i + 1}: {end_time - start_time:.4f}s")
                        if i == 0:
                            counts_preview = dict(list(result.counts.items())[:3])
                            print(f"    Sample counts: {counts_preview}")
                    except Exception as e:
                        print(f"  Iteration {i + 1}: Failed - {e}")

                # Calculate statistics
                if times:
                    avg_time = sum(times) / len(times)
                    min_time = min(times)
                    max_time = max(times)

                    results[backend_type.value] = {
                        "success_rate": success_count / args.iterations,
                        "avg_time": avg_time,
                        "min_time": min_time,
                        "max_time": max_time,
                        "iterations": args.iterations,
                        "shots": args.shots,
                    }

                    print(f"  Success rate: {success_count}/{args.iterations} ({success_count / args.iterations:.2%})")
                    print(f"  Average time: {avg_time:.4f}s")
                    print(f"  Min time: {min_time:.4f}s")
                    print(f"  Max time: {max_time:.4f}s")
                    print(f"  Throughput: {args.shots / avg_time:.0f} shots/s")
                else:
                    print("  All iterations failed")

            except Exception as e:
                print(f"  Benchmark failed: {e}")

        # Save results if requested
        if args.output and results:
            self._save_benchmark_results(results, args.output)
            print(f"\nBenchmark results saved to: {args.output}")

        # Print summary
        if len(results) > 1:
            print("\nBenchmark Summary:")
            print("-" * 30)

            # Sort by average time
            sorted_results = sorted(results.items(), key=lambda x: x[1]["avg_time"])

            for backend, stats in sorted_results:
                print(f"{backend}: {stats['avg_time']:.4f}s avg, {stats['throughput']:.0f} shots/s")

        return 0

    def _cmd_benchmark_suite(self, args: argparse.Namespace) -> int:
        """Execute the benchmark-suite command."""
        from ariadne.benchmarking import export_benchmark_report

        # Parse algorithms
        algorithms = ["bell", "qaoa", "vqe", "stabilizer"]  # default
        try:
            from ..algorithms import list_algorithms

            _available = list_algorithms()
        except Exception:
            # Fallback to original algorithms if module not available
            pass

        if args.algorithms:
            algorithms = [alg.strip() for alg in args.algorithms.split(",") if alg.strip()]

        # Parse backends
        backends = ["auto", "stim", "qiskit", "mps"]  # default
        if args.backends:
            backends = [backend.strip() for backend in args.backends.split(",") if backend.strip()]

        print("Running benchmark suite...")
        print(f"Algorithms: {', '.join(algorithms)}")
        print(f"Backends: {', '.join(backends)}")
        print(f"Shots: {args.shots}")
        print("=" * 50)

        progress = ProgressIndicator("Running benchmark suite")
        progress.start()

        try:
            # Generate benchmark report
            report = export_benchmark_report(algorithms, backends, args.shots, "json")
            progress.finish("complete")

            # Display summary
            print("\nBenchmark Results Summary:")
            print("-" * 40)

            for alg_name, alg_data in report["results"].items():
                circuit_info = alg_data["circuit_info"]
                print(f"\n{alg_name.upper()} ({circuit_info['qubits']} qubits, {circuit_info['depth']} depth):")

                successful_backends = []
                failed_backends = []

                for backend_name, backend_data in alg_data["backends"].items():
                    if backend_data["success"]:
                        execution_time = backend_data["execution_time"]
                        throughput = backend_data["throughput"]
                        successful_backends.append(f"{backend_name} ({execution_time:.3f}s, {throughput:.0f} shots/s)")
                    else:
                        failed_backends.append(f"{backend_name} ({backend_data.get('error', 'Unknown')})")

                if successful_backends:
                    print("  ✓ Working:", ", ".join(successful_backends))
                if failed_backends:
                    print("  ✗ Failed:", ", ".join(failed_backends))

            # Save results if requested
            if args.output:
                import json

                with open(args.output, "w") as f:
                    json.dump(report, f, indent=2, default=str)
                print(f"\nResults saved to: {args.output}")

            return 0

        except Exception as e:
            progress.finish("failed")
            if self.logger:
                self.logger.error(f"Benchmark suite failed: {e}")
            return 1

    def _cmd_education(self, args: argparse.Namespace) -> int:
        """Execute the education command."""
        if args.education_action == "demo":
            return self._cmd_education_demo(args)
        elif args.education_action == "quiz":
            return self._cmd_education_quiz(args)
        elif args.education_action == "visualize":
            return self._cmd_education_visualize(args)
        else:
            if self.logger:
                self.logger.error(f"Unknown education action: {args.education_action}")
            print(f"Unknown education action: {args.education_action}")
            return 1

    def _cmd_education_demo(self, args: argparse.Namespace) -> int:
        """Execute the education demo command."""
        try:
            # Import the algorithm module to get circuit
            from ..algorithms import get_algorithm
            from ..algorithms.base import AlgorithmParameters

            print(f"Running {args.algorithm} demo with {args.qubits} qubits...")

            # Create the algorithm circuit using proper instantiation
            algorithm_class = get_algorithm(args.algorithm)
            params = AlgorithmParameters(n_qubits=args.qubits)
            algorithm_instance = algorithm_class(params)
            circuit = algorithm_instance.create_circuit()

            if circuit is None:
                print(f"Algorithm {args.algorithm} not found or not implemented")
                return 1

            print(f"\nAlgorithm: {args.algorithm.upper()}")
            print(f"Circuit has {circuit.num_qubits} qubits and depth {circuit.depth()}")

            if args.verbose:
                print(f"Circuit:\n{circuit.draw()}")

            # Simulate the circuit
            from ..router import simulate

            result = simulate(circuit, shots=100)

            print("\nSimulation Results:")
            print(f"  Backend used: {result.backend_used.value}")
            print(f"  Execution time: {result.execution_time:.4f}s")
            print(f"  Sample counts: {dict(list(result.counts.items())[:5])}")

            if len(result.counts) > 5:
                print(f"  ... and {len(result.counts) - 5} more outcomes")

            return 0

        except ImportError:
            print(f"Algorithm {args.algorithm} is not available in this installation")
            return 1
        except Exception as e:
            if self.logger:
                self.logger.error(f"Education demo failed: {e}")
            print(f"Demo failed: {e}")
            return 1

    def _cmd_education_quiz(self, args: argparse.Namespace) -> int:
        """Execute the education quiz command."""
        print(f"Starting quiz on {args.topic}...")

        # For now, just show placeholder information
        quizzes = {
            "gates": [
                {"question": "Which gate creates superposition?", "options": ["X", "H", "Z", "S"], "answer": "H"},
                {
                    "question": "What does the CNOT gate do?",
                    "options": ["Creates entanglement", "Rotates phase", "Clones qubits", "Measures qubits"],
                    "answer": "Creates entanglement",
                },
            ],
            "algorithms": [
                {
                    "question": "Which algorithm provides quadratic speedup for unstructured search?",
                    "options": ["Shor's", "Grover's", "QFT", "VQE"],
                    "answer": "Grover's",
                }
            ],
            "applications": [
                {
                    "question": "Which application shows quantum advantage in optimization?",
                    "options": ["Cryptography", "Machine Learning", "QAOA", "All of the above"],
                    "answer": "QAOA",
                }
            ],
            "hardware": [
                {
                    "question": "Which quantum computing platform uses superconducting qubits?",
                    "options": ["IonQ", "IBM", "Rigetti", "All of the above"],
                    "answer": "All of the above",
                }
            ],
        }

        if args.topic not in quizzes:
            print(f"Unknown quiz topic: {args.topic}")
            return 1

        quiz = quizzes[args.topic]

        print(f"\nQuiz on {args.topic.upper()} - {len(quiz)} questions\n")

        for i, q in enumerate(quiz):
            print(f"Q{i + 1}: {q['question']}")
            for j, opt in enumerate(q["options"]):
                print(f"  {j + 1}. {opt}")

            # For simplicity, just show the answer (in a real implementation would ask user)
            correct_idx = q["options"].index(q["answer"]) + 1
            print(f"  Correct answer: {correct_idx}. {q['answer']}\n")

        print("Quiz completed! (This is a demo - in a real implementation, you would answer questions)")
        return 0

    def _cmd_education_visualize(self, args: argparse.Namespace) -> int:
        """Execute the education visualization command."""
        try:
            from qiskit import QuantumCircuit

            # Load circuit
            circuit_path = Path(args.circuit_file)
            if not circuit_path.exists():
                print(f"Circuit file not found: {args.circuit_file}")
                return 1

            if circuit_path.suffix == ".qasm":
                circuit = QuantumCircuit.from_qasm_file(str(circuit_path))
            else:
                print(f"Unsupported file format: {circuit_path.suffix}")
                return 1

            print(f"Visualizing circuit: {circuit_path.name}")
            print(f"Qubits: {circuit.num_qubits}, Depth: {circuit.depth()}")

            if args.format == "text":
                print(f"\nCircuit diagram:\n{circuit.draw()}")
            elif args.format == "latex":
                print("LaTeX output not implemented in this demo")
            elif args.format == "image":
                print("Image output not implemented in this demo")

            return 0

        except Exception as e:
            if self.logger:
                self.logger.error(f"Education visualization failed: {e}")
            print(f"Visualization failed: {e}")
            return 1

    def _cmd_learning(self, args: argparse.Namespace) -> int:
        """Execute the learning command."""
        if args.learning_action == "list":
            return self._cmd_learning_list(args)
        elif args.learning_action == "info":
            return self._cmd_learning_info(args)
        else:
            if self.logger:
                self.logger.error(f"Unknown learning action: {args.learning_action}")
            print(f"Unknown learning action: {args.learning_action}")
            return 1

    def _cmd_learning_list(self, args: argparse.Namespace) -> int:
        """Execute the learning list command."""
        resources = {
            "tutorials": [
                {"name": "quantum_basics", "title": "Quantum Computing Basics", "level": "Beginner"},
                {"name": "variational_algorithms", "title": "Variational Quantum Algorithms", "level": "Intermediate"},
                {"name": "error_correction", "title": "Quantum Error Correction", "level": "Advanced"},
            ],
            "algorithms": [
                {"name": "bell_state", "title": "Bell State Creation and Analysis", "type": "Algorithm"},
                {"name": "qft_detailed", "title": "Quantum Fourier Transform - Deep Dive", "type": "Algorithm"},
            ],
            "papers": [
                {
                    "name": "shor_quantum",
                    "title": "Polynomial-Time Algorithms for Prime Factorization",
                    "authors": "P. Shor",
                }
            ],
            "videos": [{"name": "intro_quantum", "title": "Introduction to Quantum Computing", "duration": "45 min"}],
        }

        categories = [args.category] if args.category != "all" else list(resources.keys())

        print("Ariadne Learning Resources:")
        print("=" * 50)

        for cat in categories:
            if cat in resources:
                print(f"\n{cat.upper()}:")
                for resource in resources[cat]:
                    name = resource.get("name", "Unknown")
                    title = resource.get("title", "Untitled")
                    print(f"  - {name}: {title}")

                    # Show additional details based on resource type
                    for key, value in resource.items():
                        if key not in ["name", "title"]:
                            print(f"      {key}: {value}")
                    print()

        return 0

    def _cmd_learning_info(self, args: argparse.Namespace) -> int:
        """Execute the learning info command."""
        # In a real implementation, this would fetch detailed info about a specific resource
        print(f"Detailed information for resource: {args.resource_name}")
        print("This would provide detailed information about the learning resource.")
        print("In a full implementation, this would retrieve content from documentation/resources.")
        return 0

    def _load_circuit(self, path: str) -> QuantumCircuit:
        """Load a quantum circuit from file."""
        circuit_path = Path(path)

        if not circuit_path.exists():
            raise FileNotFoundError(f"Circuit file not found: {path}")

        if circuit_path.suffix == ".qasm":
            # Load QASM file
            return QuantumCircuit.from_qasm_file(str(circuit_path))
        elif circuit_path.suffix == ".qpy":
            # Load QPY file
            from qiskit.qpy import load

            with open(circuit_path, "rb") as f:
                loaded_circuits = load(f)

            if isinstance(loaded_circuits, QuantumCircuit):
                return loaded_circuits

            try:
                iterator = iter(loaded_circuits)
            except TypeError as exc:
                raise ValueError(
                    "Loaded QPY data must be a QuantumCircuit or an iterable of QuantumCircuit objects."
                ) from exc

            for candidate in iterator:
                if isinstance(candidate, QuantumCircuit):
                    return candidate

            raise ValueError("QPY file does not contain any QuantumCircuit objects.")
        else:
            raise ValueError(f"Unsupported circuit file format: {circuit_path.suffix}")

    def _save_results(self, result: "SimulationResult", output_path: str) -> None:
        """Save simulation results to file."""
        import json

        # Convert result to dictionary
        result_dict = {
            "backend_used": result.backend_used.value,
            "execution_time": result.execution_time,
            "counts": result.counts,
            "metadata": result.metadata or {},
        }

        # Add fallback reason if present
        if result.fallback_reason:
            result_dict["fallback_reason"] = result.fallback_reason

        # Add warnings if present
        if result.warnings:
            result_dict["warnings"] = result.warnings

        # Save to file
        with open(output_path, "w") as f:
            json.dump(result_dict, f, indent=2)

    def _save_benchmark_results(self, results: dict[str, Any], output_path: str) -> None:
        """Save benchmark results to file."""
        import json
        from datetime import datetime

        # Create results dictionary
        benchmark_results = {"timestamp": datetime.now().isoformat(), "results": results}

        # Save to file
        with open(output_path, "w") as f:
            json.dump(benchmark_results, f, indent=2)

    def _resolve_backend_name(self, backend_name: str) -> str:
        """Resolve a backend name to its canonical value if an alias is provided."""

        return BACKEND_ALIASES.get(backend_name, backend_name)

    def _parse_backend_type(self, backend_name: str) -> "BackendType | None":
        """Parse backend name to BackendType enum."""

        resolved_name = self._resolve_backend_name(backend_name)

        try:
            return BackendType(resolved_name)
        except ValueError:
            return None

    def _get_available_backends(self) -> list["BackendType"]:
        """Get list of available backends."""
        from ariadne.types import BackendType

        return list(BackendType)

    def _print_backend_status(
        self, backend_type: "BackendType", metrics: "HealthMetrics", detailed: bool = False
    ) -> None:
        """Print status for a specific backend."""
        print(f"{backend_type.value}:")
        print(f"  Status: {metrics.status.value}")
        print(f"  Total checks: {metrics.total_checks}")
        print(f"  Success rate: {metrics.success_rate:.2%}")
        print(f"  Average response time: {metrics.average_response_time:.3f}s")
        print(f"  Uptime: {metrics.uptime_percentage:.1f}%")

        if detailed:
            print(f"  Last check: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(metrics.last_check))}")
            print(f"  Consecutive failures: {metrics.consecutive_failures}")

            if metrics.details:
                print("  Details:")
                for key, value in metrics.details.items():
                    print(f"    {key}: {value}")

        print()

    def _create_benchmark_circuit(self) -> QuantumCircuit:
        """Create a benchmark circuit."""
        # Create a moderately complex circuit for benchmarking
        circuit = QuantumCircuit(5)

        # Add some gates
        for i in range(5):
            circuit.h(i)

        # Add some entangling gates
        for i in range(4):
            circuit.cx(i, i + 1)

        # Add some single-qubit rotations
        for i in range(5):
            circuit.rz(0.5, i)
            circuit.sx(i)

        # Add measurement
        circuit.measure_all()

        return circuit


def main() -> int:
    """Main entry point for the CLI."""
    cli = AriadneCLI()
    return cli.run()


if __name__ == "__main__":
    sys.exit(main())
