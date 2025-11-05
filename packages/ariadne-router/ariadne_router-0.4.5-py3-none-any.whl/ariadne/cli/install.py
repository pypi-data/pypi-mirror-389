"""
Unified installation system for Ariadne Quantum Simulator.

This module provides platform detection and automatic installation of optional components
based on system capabilities, with support for CUDA, Apple Silicon, and other hardware
accelerators.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..core.error_handling import AriadneError
from ..core.logging import get_logger


class ProgressIndicator:
    """Simple progress indicator for long-running operations."""

    def __init__(self, description: str = "Processing"):
        self.description = description
        self.start_time: float | None = None
        self.last_update: float = 0

    def start(self) -> None:
        self.start_time = time.time()
        print(f"{self.description}...", end="", flush=True)

    def update(self, message: str = "") -> None:
        current_time = time.time()
        if self.start_time is not None and current_time - self.last_update > 0.5:
            elapsed = current_time - self.start_time
            print(f"\r{self.description}... ({elapsed:.1f}s){message}", end="", flush=True)
            self.last_update = current_time

    def finish(self, message: str = "done") -> None:
        if self.start_time is not None:
            elapsed = time.time() - self.start_time
            print(f"\r{self.description}... {message} ({elapsed:.1f}s)")
        else:
            print(f"\r{self.description}... {message} (0.0s)")


class Platform(Enum):
    """Supported operating systems."""

    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"
    UNKNOWN = "unknown"


class Architecture(Enum):
    """Supported system architectures."""

    X86_64 = "x86_64"
    ARM64 = "arm64"
    UNKNOWN = "unknown"


@dataclass
class SystemInfo:
    """Information about the current system."""

    platform: Platform
    architecture: Architecture
    python_version: str
    has_cuda: bool = False
    cuda_version: str | None = None
    has_apple_silicon: bool = False
    has_rocm: bool = False
    rocm_version: str | None = None
    has_intel_oneapi: bool = False
    oneapi_version: str | None = None


@dataclass
class PackageInfo:
    """Information about an installable package."""

    name: str
    pip_spec: str
    purpose: str
    platforms: list[Platform]
    architectures: list[Architecture] | None = None
    requires_hardware: str | None = None
    verification_command: str | None = None
    size_mb: int | None = None


class InstallationError(AriadneError):
    """Raised when installation fails."""

    def __init__(self, package: str, reason: str, details: dict[str, Any] | None = None):
        self.package = package
        self.reason = reason
        message = f"Failed to install '{package}': {reason}"
        super().__init__(message, details)


class RollbackManager:
    """Manages rollback of failed installations."""

    def __init__(self, logger: Any) -> None:
        """Initialize rollback manager."""
        self.logger = logger
        self.installed_packages: list[str] = []
        self.backup_files: dict[str, str] = {}

    def record_installation(self, package: str) -> None:
        """Record a successful installation for potential rollback."""
        self.installed_packages.append(package)
        self.logger.debug(f"Recorded installation of {package} for rollback")

    def record_file_backup(self, original: str, backup: str) -> None:
        """Record a file backup for potential rollback."""
        self.backup_files[original] = backup
        self.logger.debug(f"Recorded file backup: {original} -> {backup}")

    def rollback(self) -> None:
        """Rollback all recorded installations."""
        self.logger.info("Rolling back failed installation...")

        # Uninstall packages in reverse order
        for package in reversed(self.installed_packages):
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "uninstall", "-y", package],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                self.logger.info(f"Uninstalled {package}")
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Failed to uninstall {package}: {e}")

        # Restore backup files
        for original, backup in self.backup_files.items():
            try:
                shutil.copy2(backup, original)
                self.logger.info(f"Restored {original} from backup")
            except Exception as e:
                self.logger.error(f"Failed to restore {original}: {e}")

        # Clean up backup files
        for backup in self.backup_files.values():
            try:
                os.remove(backup)
            except Exception as e:
                self.logger.debug(f"Failed to remove backup file {backup}: {e}")

        self.logger.info("Rollback completed")


class PlatformDetector:
    """Detects platform and hardware capabilities."""

    def __init__(self) -> None:
        """Initialize platform detector."""
        self.logger = get_logger("install")
        self._system_info: SystemInfo | None = None

    def detect_system(self) -> SystemInfo:
        """Detect system information."""
        if self._system_info:
            return self._system_info

        # Detect platform
        system = platform.system().lower()
        if system == "windows":
            detected_platform = Platform.WINDOWS
        elif system == "linux":
            detected_platform = Platform.LINUX
        elif system == "darwin":
            detected_platform = Platform.MACOS
        else:
            detected_platform = Platform.UNKNOWN

        # Detect architecture
        machine = platform.machine().lower()
        if machine in ("x86_64", "amd64"):
            detected_arch = Architecture.X86_64
        elif machine in ("arm64", "aarch64"):
            detected_arch = Architecture.ARM64
        else:
            detected_arch = Architecture.UNKNOWN

        # Create system info
        self._system_info = SystemInfo(
            platform=detected_platform,
            architecture=detected_arch,
            python_version=f"{sys.version_info.major}.{sys.version_info.minor}",
        )

        # Detect hardware capabilities
        self._detect_hardware_capabilities()

        self.logger.info(f"Detected system: {detected_platform.value} {detected_arch.value}")
        return self._system_info

    def _detect_hardware_capabilities(self) -> None:
        """Detect hardware capabilities like CUDA, Apple Silicon, etc."""
        if not self._system_info:
            return

        # Check for CUDA
        try:
            result = subprocess.run(
                ["/usr/bin/nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                self._system_info.has_cuda = True
                self._system_info.cuda_version = result.stdout.strip()
                self.logger.info(f"Detected CUDA {self._system_info.cuda_version}")
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            self.logger.debug("CUDA not available")

        # Check for Apple Silicon
        if self._system_info.platform == Platform.MACOS and self._system_info.architecture == Architecture.ARM64:
            self._system_info.has_apple_silicon = True
            self.logger.info("Detected Apple Silicon")

        # Check for ROCm
        if self._system_info.platform == Platform.LINUX:
            try:
                result = subprocess.run(
                    ["/usr/bin/rocm-smi", "--showproductname"], capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    self._system_info.has_rocm = True
                    # Extract version from output
                    for line in result.stdout.split("\n"):
                        if "ROCm" in line:
                            self._system_info.rocm_version = line.strip()
                            break
                    self.logger.info(f"Detected ROCm: {self._system_info.rocm_version}")
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                self.logger.debug("ROCm not available")

        # Check for Intel oneAPI
        try:
            result = subprocess.run(["/usr/bin/sycl-ls", "--version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self._system_info.has_intel_oneapi = True
                self._system_info.oneapi_version = result.stdout.strip()
                self.logger.info(f"Detected Intel oneAPI: {self._system_info.oneapi_version}")
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            self.logger.debug("Intel oneAPI not available")


class PackageManager:
    """Manages installation of packages."""

    def __init__(self, dry_run: bool = False) -> None:
        """Initialize package manager."""
        self.logger = get_logger("install")
        self.dry_run = dry_run
        self.rollback_manager = RollbackManager(self.logger)
        self._available_packages = self._initialize_packages()

    def _initialize_packages(self) -> dict[str, PackageInfo]:
        """Initialize available packages."""
        return {
            "cuda": PackageInfo(
                name="CUDA Backend",
                pip_spec="cupy-cuda12x>=12.0.0",
                purpose="NVIDIA GPU acceleration",
                platforms=[Platform.WINDOWS, Platform.LINUX],
                architectures=[Architecture.X86_64],
                requires_hardware="CUDA",
                verification_command="import cupy; print(cupy.cuda.get_device_name())",
                size_mb=500,
            ),
            "apple": PackageInfo(
                name="Apple Silicon Backend",
                pip_spec="jax[cpu]>=0.4; jaxlib>=0.4; jax-metal>=0.1",
                purpose="Apple Silicon GPU acceleration",
                platforms=[Platform.MACOS],
                architectures=[Architecture.ARM64],
                requires_hardware="Apple Silicon",
                verification_command="import jax; print(jax.devices())",
                size_mb=200,
            ),
            "rocm": PackageInfo(
                name="ROCm Backend",
                pip_spec="cupy-rocm-5-6>=12.0.0",
                purpose="AMD GPU acceleration",
                platforms=[Platform.LINUX],
                architectures=[Architecture.X86_64],
                requires_hardware="ROCm",
                verification_command="import cupy; print(cupy.cuda.get_device_name())",
                size_mb=500,
            ),
            "oneapi": PackageInfo(
                name="Intel oneAPI Backend",
                pip_spec="dpctl>=0.18; intel-extension-for-pytorch>=2.1",
                purpose="Intel GPU acceleration",
                platforms=[Platform.LINUX, Platform.WINDOWS],
                architectures=[Architecture.X86_64],
                requires_hardware="Intel oneAPI",
                verification_command="import dpctl; print(dpctl.get_devices())",
                size_mb=400,
            ),
            "tensor_network": PackageInfo(
                name="Tensor Network Backend",
                pip_spec="quimb>=1.11.0; cotengra>=0.7.0; opt_einsum>=3.4.0",
                purpose="Efficient tensor network simulations",
                platforms=[Platform.WINDOWS, Platform.LINUX, Platform.MACOS],
                verification_command="import quimb; print('Tensor network backend available')",
                size_mb=100,
            ),
            "advanced": PackageInfo(
                name="Advanced Backends",
                pip_spec="mqt.ddsim>=2.0.0; qulacs>=0.6.4; cirq>=1.0.0",
                purpose="Additional quantum simulation backends",
                platforms=[Platform.WINDOWS, Platform.LINUX, Platform.MACOS],
                verification_command="import mqt.ddsim, qulacs, cirq; print('Advanced backends available')",
                size_mb=150,
            ),
            "quantum_platforms": PackageInfo(
                name="Quantum Platform SDKs",
                pip_spec="pennylane>=0.30.0; pyquil>=3.0.0; amazon-braket-sdk>=1.40.0; qsharp>=1.0.0; pyopencl>=2023.1.0",
                purpose="Cloud quantum computing platforms",
                platforms=[Platform.WINDOWS, Platform.LINUX, Platform.MACOS],
                verification_command="import pennylane; print('Quantum platforms available')",
                size_mb=300,
            ),
            "cloud": PackageInfo(
                name="Cloud SDKs",
                pip_spec="boto3>=1.26.0; azure-quantum>=0.28.0; google-cloud-quantum>=0.4.0",
                purpose="Cloud quantum computing services",
                platforms=[Platform.WINDOWS, Platform.LINUX, Platform.MACOS],
                verification_command="import boto3; print('Cloud SDKs available')",
                size_mb=200,
            ),
        }

    def get_available_packages(self, system_info: SystemInfo) -> list[PackageInfo]:
        """Get packages available for the current system."""
        available = []

        for package_info in self._available_packages.values():
            # Check platform compatibility
            if system_info.platform not in package_info.platforms:
                continue

            # Check architecture compatibility
            if package_info.architectures and system_info.architecture not in package_info.architectures:
                continue

            # Check hardware requirements
            if package_info.requires_hardware:
                if package_info.requires_hardware == "CUDA" and not system_info.has_cuda:
                    continue
                elif package_info.requires_hardware == "Apple Silicon" and not system_info.has_apple_silicon:
                    continue
                elif package_info.requires_hardware == "ROCm" and not system_info.has_rocm:
                    continue
                elif package_info.requires_hardware == "Intel oneAPI" and not system_info.has_intel_oneapi:
                    continue

            available.append(package_info)

        return available

    def install_package(self, package_info: PackageInfo, force: bool = False) -> bool:
        """Install a package."""
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would install: {package_info.name}")
            return True

        progress = ProgressIndicator(f"Installing {package_info.name}")
        progress.start()

        try:
            # Check if already installed
            if self._is_package_installed(package_info) and not force:
                progress.finish("already installed")
                self.logger.info(f"{package_info.name} is already installed")
                return True

            # Install package
            progress.update(" (downloading...)")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", package_info.pip_spec],
                check=True,
                capture_output=True,
                text=True,
            )

            progress.update(" (verifying...)")

            # Verify installation
            if package_info.verification_command:
                try:
                    verify_result = subprocess.run(
                        [sys.executable, "-c", package_info.verification_command],
                        check=True,
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    self.logger.debug(f"Verification output: {verify_result.stdout.strip()}")
                except subprocess.CalledProcessError as e:
                    raise InstallationError(package_info.name, f"Verification failed: {e.stderr}") from e
                except subprocess.TimeoutExpired as e:
                    raise InstallationError(package_info.name, "Verification timed out") from e

            # Record for rollback
            self.rollback_manager.record_installation(package_info.pip_spec.split(">=")[0].split("[")[0])

            progress.finish("installed")
            self.logger.info(f"Successfully installed {package_info.name}")
            return True

        except subprocess.CalledProcessError as e:
            progress.finish("failed")
            error_msg = e.stderr if e.stderr else e.stdout
            raise InstallationError(package_info.name, f"Installation failed: {error_msg}") from e
        except Exception as e:
            progress.finish("failed")
            raise InstallationError(package_info.name, f"Unexpected error: {str(e)}") from e

    def _is_package_installed(self, package_info: PackageInfo) -> bool:
        """Check if a package is already installed."""
        try:
            # Extract package name from pip spec
            package_name = package_info.pip_spec.split(">=")[0].split("[")[0]

            # Check if package is installed
            result = subprocess.run([sys.executable, "-m", "pip", "show", package_name], capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False

    def check_dependencies(self) -> list[str]:
        """Check for missing dependencies."""
        missing = []

        # Check for pip
        try:
            subprocess.run([sys.executable, "-m", "pip", "--version"], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            missing.append("pip")

        # Check for internet connectivity
        try:
            import urllib.request

            urllib.request.urlopen("https://pypi.org", timeout=5)  # nosec B310: HTTPS is safe
        except Exception:
            missing.append("internet connection")

        return missing


class Installer:
    """Main installer class."""

    def __init__(self, dry_run: bool = False, force: bool = False) -> None:
        """Initialize installer."""
        self.logger = get_logger("install")
        self.dry_run = dry_run
        self.force = force
        self.detector = PlatformDetector()
        self.package_manager = PackageManager(dry_run)

    def install_accelerate(self) -> int:
        """Install acceleration packages based on system capabilities."""
        self.logger.info("Starting accelerated installation...")

        # Detect system
        system_info = self.detector.detect_system()

        # Check dependencies
        missing_deps = self.package_manager.check_dependencies()
        if missing_deps:
            self.logger.error(f"Missing dependencies: {', '.join(missing_deps)}")
            return 1

        # Get available packages
        available_packages = self.package_manager.get_available_packages(system_info)

        if not available_packages:
            self.logger.info("No additional packages available for this system")
            return 0

        # Select packages to install
        packages_to_install = self._select_packages(system_info, available_packages)

        if not packages_to_install:
            self.logger.info("No packages selected for installation")
            return 0

        # Show installation plan
        self._show_installation_plan(packages_to_install)

        if self.dry_run:
            self.logger.info("Dry run completed - no packages were installed")
            return 0

        # Install packages
        failed_packages = []
        for package_info in packages_to_install:
            try:
                success = self.package_manager.install_package(package_info, self.force)
                if not success:
                    failed_packages.append(package_info.name)
            except InstallationError as e:
                self.logger.error(f"Failed to install {package_info.name}: {e}")
                failed_packages.append(package_info.name)

                # Rollback on failure
                if not self.dry_run:
                    self.package_manager.rollback_manager.rollback()
                    self.logger.error("Installation failed, rolled back changes")
                    return 1

        # Report results
        if failed_packages:
            self.logger.error(f"Failed to install: {', '.join(failed_packages)}")
            return 1
        else:
            self.logger.info("All packages installed successfully")
            return 0

    def install_specific(self, package_names: list[str]) -> int:
        """Install specific packages."""
        self.logger.info(f"Installing specific packages: {', '.join(package_names)}")

        # Detect system
        system_info = self.detector.detect_system()

        # Check dependencies
        missing_deps = self.package_manager.check_dependencies()
        if missing_deps:
            self.logger.error(f"Missing dependencies: {', '.join(missing_deps)}")
            return 1

        # Get available packages
        available_packages = self.package_manager.get_available_packages(system_info)
        available_map = {p.name.lower(): p for p in available_packages}

        # Find requested packages
        packages_to_install = []
        not_found = []

        for name in package_names:
            if name.lower() in available_map:
                packages_to_install.append(available_map[name.lower()])
            else:
                not_found.append(name)

        if not_found:
            self.logger.error(f"Packages not found: {', '.join(not_found)}")
            return 1

        if not packages_to_install:
            self.logger.info("No valid packages to install")
            return 0

        # Show installation plan
        self._show_installation_plan(packages_to_install)

        if self.dry_run:
            self.logger.info("Dry run completed - no packages were installed")
            return 0

        # Install packages
        failed_packages = []
        for package_info in packages_to_install:
            try:
                success = self.package_manager.install_package(package_info, self.force)
                if not success:
                    failed_packages.append(package_info.name)
            except InstallationError as e:
                self.logger.error(f"Failed to install {package_info.name}: {e}")
                failed_packages.append(package_info.name)

                # Rollback on failure
                if not self.dry_run:
                    self.package_manager.rollback_manager.rollback()
                    self.logger.error("Installation failed, rolled back changes")
                    return 1

        # Report results
        if failed_packages:
            self.logger.error(f"Failed to install: {', '.join(failed_packages)}")
            return 1
        else:
            self.logger.info("All packages installed successfully")
            return 0

    def list_available(self) -> int:
        """List available packages for the current system."""
        system_info = self.detector.detect_system()
        available_packages = self.package_manager.get_available_packages(system_info)

        print(f"\nAvailable packages for {system_info.platform.value} {system_info.architecture.value}:")
        print("=" * 60)

        if not available_packages:
            print("No additional packages available for this system")
            return 0

        for package in available_packages:
            status = "✓ Available"
            if self.package_manager._is_package_installed(package):
                status = "✓ Installed"

            print(f"\n{package.name}:")
            print(f"  Purpose: {package.purpose}")
            print(f"  Status: {status}")
            if package.size_mb:
                print(f"  Size: ~{package.size_mb} MB")
            if package.requires_hardware:
                print(f"  Requires: {package.requires_hardware}")

        return 0

    def _select_packages(self, system_info: SystemInfo, available_packages: list[PackageInfo]) -> list[PackageInfo]:
        """Select packages to install based on system capabilities."""
        selected = []

        # Always include tensor network backend
        for package in available_packages:
            if "tensor_network" in package.pip_spec:
                selected.append(package)
                break

        # Add hardware-specific packages
        if system_info.has_cuda:
            for package in available_packages:
                if "cuda" in package.pip_spec:
                    selected.append(package)
                    break

        if system_info.has_apple_silicon:
            for package in available_packages:
                if "jax-metal" in package.pip_spec:
                    selected.append(package)
                    break

        if system_info.has_rocm:
            for package in available_packages:
                if "rocm" in package.pip_spec:
                    selected.append(package)
                    break

        if system_info.has_intel_oneapi:
            for package in available_packages:
                if "intel-extension-for-pytorch" in package.pip_spec:
                    selected.append(package)
                    break

        return selected

    def _show_installation_plan(self, packages: list[PackageInfo]) -> None:
        """Show the installation plan."""
        total_size = sum(p.size_mb or 0 for p in packages)

        print("\nInstallation Plan:")
        print("=" * 40)

        for package in packages:
            status = "Update" if self.package_manager._is_package_installed(package) else "Install"
            print(f"  {status}: {package.name}")
            print(f"    Purpose: {package.purpose}")
            if package.size_mb:
                print(f"    Size: ~{package.size_mb} MB")

        if total_size > 0:
            print(f"\nTotal download size: ~{total_size} MB")

        if self.dry_run:
            print("\n[DRY RUN] No packages will be installed")
        else:
            print("\nProceeding with installation...")
