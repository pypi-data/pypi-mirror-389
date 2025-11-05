"""
AWS Braket Quantum Backend for Ariadne

This module integrates AWS Braket, Amazon's quantum computing service,
providing access to quantum hardware and simulators through the AWS cloud.

AWS Braket Features:
- Access to quantum hardware from multiple providers (IonQ, Rigetti, Oxford Quantum Circuits)
- Cloud-based quantum simulators (SV1, TN1, DM1)
- Hybrid quantum-classical algorithms
- Quantum job management and monitoring
- Error mitigation and noise characterization
"""

from __future__ import annotations

import importlib.util
import logging
import warnings
from typing import Any

from qiskit import QuantumCircuit
from qiskit.circuit import Parameter

logger = logging.getLogger(__name__)


class AWSBraketBackend:
    """AWS Braket-based quantum backend for Ariadne."""

    def __init__(
        self,
        device_arn: str | None = None,
        region: str = "us-east-1",
        shots: int = 1000,
        enable_fallback: bool = True,
        poll_timeout_seconds: int = 300,
        poll_interval_seconds: int = 5,
    ):
        """
        Initialize AWS Braket backend.

        Args:
            device_arn: ARN of the quantum device/simulator to use
            region: AWS region for Braket service
            shots: Number of shots for circuit execution
            enable_fallback: Enable fallback to local simulator on cloud failures
            poll_timeout_seconds: Timeout for job polling in seconds
            poll_interval_seconds: Interval between job status checks
        """
        self.device_arn = device_arn
        self.region = region
        self.shots = shots
        self.enable_fallback = enable_fallback
        self.poll_timeout_seconds = poll_timeout_seconds
        self.poll_interval_seconds = poll_interval_seconds

        # Check Braket availability
        self.braket_available = self._check_braket_availability()
        if not self.braket_available:
            raise RuntimeError("AWS Braket SDK not available")

        # Initialize AWS session and device
        self.aws_session = self._create_aws_session()
        self.device = self._get_or_create_device()

        # Track job statistics
        self.job_stats = {
            "total_jobs": 0,
            "successful_jobs": 0,
            "failed_jobs": 0,
            "fallbacks": 0,
        }

    def _check_braket_availability(self) -> bool:
        """Check if AWS Braket SDK is installed and available."""
        return importlib.util.find_spec("braket") is not None

    def _create_aws_session(self) -> Any:
        """Create AWS session for Braket."""
        try:
            import boto3
            from braket.aws.aws_session import AwsSession

            # Create AWS session with default credentials
            return AwsSession(boto3.Session(), default_region=self.region)
        except Exception as e:
            warnings.warn(f"Failed to create AWS session: {e}", stacklevel=2)
            raise RuntimeError(f"AWS session creation failed: {e}") from e

    def _get_or_create_device(self) -> Any:
        """Get or create quantum device."""
        try:
            from braket.aws.aws_device import AwsDevice

            if self.device_arn:
                # Use specified device
                return AwsDevice(self.device_arn, self.aws_session)
            else:
                # Use default simulator for reliability
                default_simulator_arn = "arn:aws:braket:::device/quantum-simulator/amazon/sv1"
                return AwsDevice(default_simulator_arn, self.aws_session)
        except Exception as e:
            warnings.warn(f"Failed to create device: {e}", stacklevel=2)
            raise RuntimeError(f"Device creation failed: {e}") from e

    def simulate(self, circuit: QuantumCircuit, shots: int = 1000) -> dict[str, int]:
        """
        Simulate quantum circuit using AWS Braket.

        Args:
            circuit: Quantum circuit to simulate
            shots: Number of measurement shots

        Returns:
            Dictionary of measurement counts
        """
        try:
            # Convert Qiskit circuit to Braket format
            braket_circuit = self._convert_qiskit_to_braket(circuit)

            # Submit job to AWS Braket
            job = self._submit_job(braket_circuit, shots)

            # Wait for job completion
            result = self._wait_for_job_completion(job)

            # Extract measurement counts
            counts = self._extract_counts(result)

            # Update statistics
            self.job_stats["total_jobs"] += 1
            self.job_stats["successful_jobs"] += 1

            return counts

        except Exception as e:
            # Update statistics
            self.job_stats["total_jobs"] += 1
            self.job_stats["failed_jobs"] += 1

            # Fallback to local simulator if enabled
            if self.enable_fallback:
                self.job_stats["fallbacks"] += 1
                warnings.warn(
                    f"AWS Braket execution failed: {e}, falling back to local simulator",
                    stacklevel=2,
                )
                return self._simulate_with_qiskit(circuit, shots)
            else:
                raise RuntimeError(f"AWS Braket simulation failed: {e}") from e

    def _convert_qiskit_to_braket(self, circuit: QuantumCircuit) -> Any:
        """Convert Qiskit circuit to Braket circuit format."""
        try:
            from braket.circuits import Circuit as BraketCircuit

            # Create Braket circuit
            braket_circuit = BraketCircuit()

            # Create qubit index mapping
            qubit_to_index = {qubit: i for i, qubit in enumerate(circuit.qubits)}

            # Apply each operation
            for instruction in circuit.data:
                gate_name = instruction.operation.name.lower()
                qubit_indices = [qubit_to_index[q] for q in instruction.qubits]

                # Skip measurement and barrier operations
                if gate_name in ["measure", "barrier", "delay"]:
                    continue

                # Single-qubit gates
                if len(qubit_indices) == 1:
                    self._apply_single_qubit_gate(braket_circuit, gate_name, qubit_indices[0], instruction)

                # Two-qubit gates
                elif len(qubit_indices) == 2:
                    self._apply_two_qubit_gate(braket_circuit, gate_name, qubit_indices, instruction)

                # Multi-qubit gates
                elif len(qubit_indices) >= 3:
                    self._apply_multi_qubit_gate(braket_circuit, gate_name, qubit_indices, instruction)

                else:
                    warnings.warn(f"Unsupported gate: {gate_name}, skipping", stacklevel=2)

            return braket_circuit

        except Exception as e:
            raise RuntimeError(f"Circuit conversion failed: {e}") from e

    def _apply_single_qubit_gate(self, braket_circuit: Any, gate_name: str, qubit: int, instruction: Any) -> None:
        """Apply single-qubit gate to Braket circuit."""
        try:
            # Handle parameters
            params = []
            for param in instruction.params:
                if isinstance(param, Parameter):
                    # For now, use default value for parameters
                    params.append(0.0)
                else:
                    params.append(float(param))

            # Apply gate based on name
            if gate_name == "x":
                braket_circuit.x(qubit)
            elif gate_name == "y":
                braket_circuit.y(qubit)
            elif gate_name == "z":
                braket_circuit.z(qubit)
            elif gate_name == "h":
                braket_circuit.h(qubit)
            elif gate_name == "s":
                braket_circuit.s(qubit)
            elif gate_name == "sdg":
                braket_circuit.si(qubit)  # S dagger
            elif gate_name == "t":
                braket_circuit.t(qubit)
            elif gate_name == "tdg":
                braket_circuit.ti(qubit)  # T dagger
            elif gate_name == "rx" and params:
                braket_circuit.rx(params[0], qubit)
            elif gate_name == "ry" and params:
                braket_circuit.ry(params[0], qubit)
            elif gate_name == "rz" and params:
                braket_circuit.rz(params[0], qubit)
            elif gate_name == "p" and params:
                braket_circuit.phaseshift(params[0], qubit)
            elif gate_name == "u1" and params:
                braket_circuit.u1(params[0], qubit)
            elif gate_name == "u2" and len(params) >= 2:
                braket_circuit.u2(params[0], params[1], qubit)
            elif gate_name == "u3" and len(params) >= 3:
                braket_circuit.u3(params[0], params[1], params[2], qubit)
            else:
                warnings.warn(f"Unsupported single-qubit gate: {gate_name}", stacklevel=2)

        except Exception as e:
            warnings.warn(f"Failed to apply {gate_name} gate: {e}", stacklevel=2)

    def _apply_two_qubit_gate(
        self, braket_circuit: Any, gate_name: str, qubit_indices: list[int], instruction: Any
    ) -> None:
        """Apply two-qubit gate to Braket circuit."""
        try:
            control, target = qubit_indices[0], qubit_indices[1]

            if gate_name == "cx" or gate_name == "cnot":
                braket_circuit.cnot(control, target)
            elif gate_name == "cy":
                braket_circuit.cy(control, target)
            elif gate_name == "cz":
                braket_circuit.cz(control, target)
            elif gate_name == "swap":
                braket_circuit.swap(control, target)
            elif gate_name == "crx" and instruction.params:
                braket_circuit.crx(float(instruction.params[0]), control, target)
            elif gate_name == "cry" and instruction.params:
                braket_circuit.cry(float(instruction.params[0]), control, target)
            elif gate_name == "crz" and instruction.params:
                braket_circuit.crz(float(instruction.params[0]), control, target)
            else:
                warnings.warn(f"Unsupported two-qubit gate: {gate_name}", stacklevel=2)

        except Exception as e:
            warnings.warn(f"Failed to apply {gate_name} gate: {e}", stacklevel=2)

    def _apply_multi_qubit_gate(
        self, braket_circuit: Any, gate_name: str, qubit_indices: list[int], instruction: Any
    ) -> None:
        """Apply multi-qubit gate to Braket circuit."""
        try:
            if gate_name == "ccx" or gate_name == "ccnot":
                if len(qubit_indices) >= 3:
                    control1, control2, target = qubit_indices[0], qubit_indices[1], qubit_indices[2]
                    braket_circuit.ccnot(control1, control2, target)
            else:
                warnings.warn(f"Unsupported multi-qubit gate: {gate_name}", stacklevel=2)

        except Exception as e:
            warnings.warn(f"Failed to apply {gate_name} gate: {e}", stacklevel=2)

    def _submit_job(self, braket_circuit: Any, shots: int) -> Any:
        """Submit circuit execution job to AWS Braket."""
        try:
            # Submit job with specified shots
            job = self.device.run(braket_circuit, shots=shots)
            return job
        except Exception as e:
            raise RuntimeError(f"Job submission failed: {e}") from e

    def _wait_for_job_completion(self, job: Any) -> Any:
        """Wait for job completion with timeout."""
        try:
            import time

            start_time = time.time()
            while True:
                # Check job status
                status = job.state()

                if status == "COMPLETED":
                    return job.result()
                elif status == "FAILED":
                    raise RuntimeError(f"Job failed with status: {status}")
                elif status == "CANCELLED":
                    raise RuntimeError("Job was cancelled")

                # Check timeout
                elapsed_time = time.time() - start_time
                if elapsed_time > self.poll_timeout_seconds:
                    raise RuntimeError(f"Job timeout after {self.poll_timeout_seconds} seconds")

                # Wait before next check
                time.sleep(self.poll_interval_seconds)

        except Exception as e:
            raise RuntimeError(f"Job monitoring failed: {e}") from e

    def _extract_counts(self, result: Any) -> dict[str, int]:
        """Extract measurement counts from Braket result."""
        try:
            # Get measurement results
            measurements = result.measurements

            if not measurements:
                return {}

            # Convert to counts dictionary
            counts: dict[str, int] = {}
            for measurement in measurements:
                # Convert measurement to bitstring
                bitstring = "".join(str(bit) for bit in measurement)
                counts[bitstring] = counts.get(bitstring, 0) + 1

            return counts

        except Exception as e:
            warnings.warn(f"Failed to extract counts: {e}", stacklevel=2)
            # Return empty counts as fallback
            return {}

    def _simulate_with_qiskit(self, circuit: QuantumCircuit, shots: int) -> dict[str, int]:
        """Fallback simulation using Qiskit."""
        try:
            from qiskit.providers.basic_provider import BasicProvider

            provider = BasicProvider()
            backend = provider.get_backend("basic_simulator")
            job = backend.run(circuit, shots=shots)
            counts = job.result().get_counts()

            return {str(k): v for k, v in counts.items()}

        except ImportError as err:
            raise RuntimeError("Neither AWS Braket nor Qiskit BasicProvider available") from err

    def get_backend_info(self) -> dict[str, Any]:
        """Get information about the backend configuration."""
        info: dict[str, Any] = {
            "name": "aws_braket",
            "device_arn": self.device_arn,
            "region": self.region,
            "braket_available": self.braket_available,
            "shots": self.shots,
            "enable_fallback": self.enable_fallback,
            "job_stats": self.job_stats.copy(),
        }

        if self.braket_available:
            try:
                # Add device information
                info["device_name"] = getattr(self.device, "name", "Unknown")
                info["device_type"] = getattr(self.device, "type", "Unknown")
                info["device_status"] = getattr(self.device, "status", "Unknown")

                # Add AWS session info (without credentials)
                info["aws_region"] = self.aws_session.region

            except Exception as e:
                logger.debug(f"Failed to get Braket backend info: {e}")

        return info

    def get_available_devices(self, region: str | None = None) -> list[dict[str, Any]]:
        """Get list of available quantum devices in the specified region."""
        try:
            from braket.aws.aws_device import AwsDevice

            target_region = region or self.region
            devices = AwsDevice.get_devices(self.aws_session, aws_region=target_region)

            device_list = []
            for device in devices:
                device_info = {
                    "arn": device.arn,
                    "name": device.name,
                    "type": device.type,
                    "status": device.status,
                    "provider": device.provider_name,
                    "qubit_count": device.properties.qubits,
                }
                device_list.append(device_info)

            return device_list

        except Exception as e:
            warnings.warn(f"Failed to get available devices: {e}", stacklevel=2)
            return []

    def estimate_cost(self, circuit: QuantumCircuit, shots: int = 1000) -> dict[str, float]:
        """Estate execution cost for the given circuit."""
        try:
            # Get device pricing information (access to ensure properties are available)
            _ = self.device.properties

            # Basic cost estimation (simplified)
            if self.device.type == "SIMULATOR":
                # Simulators typically charge per task
                cost_per_task = 0.005  # Example: $0.005 per task
                estimated_cost = cost_per_task
            else:
                # Quantum hardware typically charges per shot
                cost_per_shot = 0.00001  # Example: $0.00001 per shot
                estimated_cost = cost_per_shot * shots

            return {
                "estimated_cost_usd": estimated_cost,
                "currency": "USD",
                "shots": shots,
                "device_type": self.device.type,
            }

        except Exception as e:
            warnings.warn(f"Cost estimation failed: {e}", stacklevel=2)
            return {"estimated_cost_usd": 0.0, "currency": "USD", "error": str(e)}

    def can_simulate(self, circuit: QuantumCircuit, **kwargs: Any) -> tuple[bool, str]:
        """
        Check if backend can simulate the given circuit.

        Returns:
            (can_simulate, reason)
        """
        try:
            # Check circuit size constraints
            num_qubits = circuit.num_qubits

            if self.device.type == "SIMULATOR":
                # Simulators typically support more qubits
                if num_qubits > 34:  # SV1 limit
                    return False, f"Circuit has {num_qubits} qubits, exceeds simulator limit of 34"
            else:
                # Quantum hardware has stricter limits
                device_qubits = getattr(self.device.properties, "qubits", 0)
                if num_qubits > device_qubits:
                    return False, f"Circuit has {num_qubits} qubits, exceeds device limit of {device_qubits}"

            # Check for unsupported operations
            for instruction in circuit.data:
                gate_name = instruction.operation.name.lower()
                if gate_name in ["measure", "barrier", "delay"]:
                    continue

                # Check if gate is supported
                if not self._is_gate_supported(gate_name):
                    return False, f"Gate '{gate_name}' is not supported by AWS Braket"

            return True, "Can simulate"

        except Exception as e:
            return False, f"Error checking circuit compatibility: {e}"

    def _is_gate_supported(self, gate_name: str) -> bool:
        """Check if a gate is supported by AWS Braket."""
        supported_gates = {
            # Single-qubit gates
            "x",
            "y",
            "z",
            "h",
            "s",
            "sdg",
            "t",
            "tdg",
            "rx",
            "ry",
            "rz",
            "p",
            "u1",
            "u2",
            "u3",
            # Two-qubit gates
            "cx",
            "cnot",
            "cy",
            "cz",
            "swap",
            "crx",
            "cry",
            "crz",
            # Multi-qubit gates
            "ccx",
            "ccnot",
        }
        return gate_name in supported_gates


def is_aws_braket_available() -> bool:
    """Check if AWS Braket is available for use."""
    return importlib.util.find_spec("braket") is not None


def list_aws_braket_devices(region: str = "us-east-1") -> list[dict[str, Any]]:
    """List available AWS Braket devices."""
    if not is_aws_braket_available():
        return []

    try:
        backend = AWSBraketBackend(region=region)
        return backend.get_available_devices()
    except Exception:
        return []


def create_aws_braket_backend(
    device_arn: str | None = None,
    region: str = "us-east-1",
    shots: int = 1000,
    enable_fallback: bool = True,
    **kwargs: Any,
) -> AWSBraketBackend:
    """
    Factory function to create an AWS Braket backend.

    Args:
        device_arn: ARN of the quantum device/simulator to use
        region: AWS region for Braket service
        shots: Number of shots for circuit execution
        enable_fallback: Enable fallback to local simulator on cloud failures
        **kwargs: Additional backend options

    Returns:
        Configured AWSBraketBackend instance
    """
    return AWSBraketBackend(
        device_arn=device_arn,
        region=region,
        shots=shots,
        enable_fallback=enable_fallback,
        **kwargs,
    )


def benchmark_aws_braket(
    circuits: list[QuantumCircuit],
    shots: int = 1000,
    device_arn: str | None = None,
) -> dict[str, Any]:
    """
    Benchmark AWS Braket backend performance.

    Args:
        circuits: List of quantum circuits to benchmark
        shots: Number of shots per circuit
        device_arn: Device ARN to use (None for default)

    Returns:
        Benchmark results
    """
    import time

    if not circuits:
        return {"error": "No circuits provided for benchmarking"}

    try:
        backend = create_aws_braket_backend(device_arn=device_arn, shots=shots)
        results: dict[str, Any] = {
            "backend_info": backend.get_backend_info(),
            "circuit_results": [],
            "total_time": 0.0,
            "success_rate": 0.0,
        }

        successful_runs = 0
        start_time = time.time()

        for i, circuit in enumerate(circuits):
            circuit_result = {
                "circuit_index": i,
                "num_qubits": circuit.num_qubits,
                "depth": circuit.depth(),
                "success": False,
                "execution_time": 0.0,
                "error": None,
            }

            try:
                circuit_start = time.time()
                counts = backend.simulate(circuit, shots)
                circuit_end = time.time()

                circuit_result["success"] = True
                circuit_result["execution_time"] = circuit_end - circuit_start
                circuit_result["counts_sample"] = dict(list(counts.items())[:3])
                successful_runs += 1

            except Exception as e:
                circuit_result["error"] = str(e)

            results["circuit_results"].append(circuit_result)

        results["total_time"] = time.time() - start_time
        results["success_rate"] = successful_runs / len(circuits)

        return results

    except Exception as e:
        return {"error": f"Benchmark failed: {e}"}
