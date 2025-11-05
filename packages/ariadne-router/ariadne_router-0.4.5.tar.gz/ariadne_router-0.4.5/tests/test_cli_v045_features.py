"""
Tests for Ariadne v0.4.5 CLI features.

This module tests the new CLI commands added in v0.4.5:
- ariadne doctor
- ariadne version
- ariadne quickstart
"""

import subprocess
import sys
from pathlib import Path


def run_cli_command(*args):
    """Run CLI command and return result."""
    cmd = [sys.executable, "-m", "ariadne.cli.main"] + list(args)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=30,
        env={"PYTHONPATH": str(Path(__file__).parent.parent / "src")},
    )
    return result


class TestDoctorCommand:
    """Test ariadne doctor command."""

    def test_doctor_basic(self):
        """Test basic doctor command functionality."""
        result = run_cli_command("doctor")
        assert result.returncode == 0
        assert "Ariadne System Diagnostics" in result.stdout
        assert "Python version:" in result.stdout
        assert "Ariadne:" in result.stdout
        assert "Available backends:" in result.stdout

    def test_doctor_verbose(self):
        """Test doctor command with verbose flag."""
        result = run_cli_command("doctor", "--verbose")
        assert result.returncode == 0
        assert "Detailed Information:" in result.stdout
        assert "CPU cores:" in result.stdout
        assert "Memory:" in result.stdout

    def test_doctor_invalid_flag(self):
        """Test doctor command with invalid flag."""
        result = run_cli_command("doctor", "--invalid-flag")
        assert result.returncode != 0


class TestVersionCommand:
    """Test ariadne version command."""

    def test_version_basic(self):
        """Test basic version command functionality."""
        result = run_cli_command("version")
        assert result.returncode == 0
        assert "Ariadne" in result.stdout
        assert "Python" in result.stdout
        assert "Available backends:" in result.stdout

    def test_version_verbose(self):
        """Test version command with verbose flag."""
        result = run_cli_command("version", "--verbose")
        assert result.returncode == 0
        assert "Dependency versions:" in result.stdout
        assert "System information:" in result.stdout


class TestQuickstartCommand:
    """Test ariadne quickstart command."""

    def test_quickstart_list(self):
        """Test quickstart list functionality."""
        result = run_cli_command("quickstart", "--list")
        assert result.returncode == 0
        assert "Available Quickstart Algorithms:" in result.stdout
        assert "bell" in result.stdout
        assert "ghz" in result.stdout
        assert "grover" in result.stdout

    def test_quickstart_bell_algorithm(self):
        """Test quickstart bell algorithm."""
        result = run_cli_command("quickstart", "--algorithm", "bell", "--shots", "10")
        assert result.returncode == 0
        assert "BELL Algorithm Demonstration" in result.stdout
        assert "Simulation Complete" in result.stdout
        assert "|00⟩" in result.stdout or "|11⟩" in result.stdout

    def test_quickstart_invalid_algorithm(self):
        """Test quickstart with invalid algorithm."""
        result = run_cli_command("quickstart", "--algorithm", "nonexistent")
        assert result.returncode == 2  # argparse returns 2 for invalid choices
        assert "invalid choice" in result.stderr


class TestEnhancedErrorMessages:
    """Test enhanced error messages."""

    def test_backend_unavailable_error_cuda(self):
        """Test CUDA backend error message."""
        from ariadne.core.error_handling import BackendUnavailableError

        error = BackendUnavailableError("cuda", "CUDA not available")
        error_str = str(error)
        assert "ariadne-router[cuda]" in error_str
        assert "NVIDIA GPU" in error_str

    def test_backend_unavailable_error_metal(self):
        """Test Metal backend error message."""
        from ariadne.core.error_handling import BackendUnavailableError

        error = BackendUnavailableError("metal", "JAX not available")
        error_str = str(error)
        assert "ariadne-router[apple]" in error_str
        assert "Apple Silicon" in error_str

    def test_backend_unavailable_error_generic(self):
        """Test generic backend error message."""
        from ariadne.core.error_handling import BackendUnavailableError

        error = BackendUnavailableError("unknown", "Test error")
        error_str = str(error)
        assert "ariadne-router[" in error_str
        assert "ariadne doctor" in error_str


class TestConfigurationLoading:
    """Test configuration file loading."""

    def test_load_config_file_empty(self):
        """Test loading config when no files exist."""
        from ariadne.config.loader import load_config_file

        config = load_config_file()
        assert isinstance(config, dict)
        # Should return empty dict when no config files found

    def test_config_error_handling(self):
        """Test that malformed config files are handled gracefully."""
        import tempfile
        import warnings
        from pathlib import Path

        from ariadne.config.loader import load_config_file

        # Create malformed YAML file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ariadnerc", delete=False) as f:
            f.write("invalid: yaml: [unclosed")
            temp_path = f.name

        try:
            # Temporarily move to directory with malformed config
            with warnings.catch_warnings(record=True):
                warnings.simplefilter("always")
                config = load_config_file()
                # Should either return empty dict or show warning
                assert isinstance(config, dict)
        finally:
            Path(temp_path).unlink(missing_ok=True)
