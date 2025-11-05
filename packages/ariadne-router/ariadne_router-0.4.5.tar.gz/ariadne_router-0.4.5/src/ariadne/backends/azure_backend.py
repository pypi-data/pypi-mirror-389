"""
Azure Quantum Backend for Ariadne

This module integrates Azure Quantum, Microsoft's quantum computing service,
providing access to quantum hardware and simulators through the Azure cloud.

Azure Quantum Features:
- Access to quantum hardware from multiple providers (IonQ, Honeywell, QCI)
- Cloud-based quantum simulators
- Hybrid quantum-classical algorithms
- Quantum job management and monitoring
- Error mitigation and noise characterization
"""

from __future__ import annotations

import importlib.util
import logging
import os
import warnings
from typing import Any

from qiskit import QuantumCircuit
from qiskit.circuit import Parameter

logger = logging.getLogger(__name__)


class AzureQuantumBackend:
    """Azure Quantum-based quantum backend for Ariadne."""

    def __init__(
        self,
        workspace_id: str | None = None,
        resource_id: str | None = None,
        location: str = "eastus",
        shots: int = 1000,
        enable_fallback: bool = True,
        poll_timeout_seconds: int = 300,
        poll_interval_seconds: int = 5,
        credential_type: str = "default",
    ):
        """
        Initialize Azure Quantum backend.

        Args:
            workspace_id: Azure Quantum workspace ID
            resource_id: Azure Quantum resource ID
            location: Azure region for the Quantum workspace
            shots: Number of shots for circuit execution
            enable_fallback: Enable fallback to local simulator on cloud failures
            poll_timeout_seconds: Timeout for job polling in seconds
            poll_interval_seconds: Interval between job status checks
            credential_type: Type of Azure credentials to use ('default', 'service_principal', 'managed_identity')
        """
        self.workspace_id = workspace_id
        self.resource_id = resource_id
        self.location = location
        self.shots = shots
        self.enable_fallback = enable_fallback
        self.poll_timeout_seconds = poll_timeout_seconds
        self.poll_interval_seconds = poll_interval_seconds
        self.credential_type = credential_type

        # Check Azure Quantum availability
        self.azure_quantum_available = self._check_azure_quantum_availability()
        if not self.azure_quantum_available:
            raise RuntimeError("Azure Quantum SDK not available")

        # Initialize Azure workspace and target
        self.workspace = self._create_workspace()
        self.target = self._get_or_create_target()

        # Track job statistics
        self.job_stats = {
            "total_jobs": 0,
            "successful_jobs": 0,
            "failed_jobs": 0,
            "fallbacks": 0,
        }

    def _check_azure_quantum_availability(self) -> bool:
        """Check if Azure Quantum SDK is installed and available."""
        return importlib.util.find_spec("azure.quantum") is not None

    def _create_workspace(self) -> Any:
        """Create Azure Quantum workspace."""
        try:
            from azure.identity import ClientSecretCredential, DefaultAzureCredential, ManagedIdentityCredential
            from azure.quantum import Workspace

            # Create appropriate credential based on type
            if self.credential_type == "service_principal":
                # For service principal, client_id and client_secret should be in environment variables
                client_id = os.getenv("AZURE_CLIENT_ID")
                client_secret = os.getenv("AZURE_CLIENT_SECRET")
                tenant_id = os.getenv("AZURE_TENANT_ID")

                if not all([client_id, client_secret, tenant_id]):
                    raise ValueError("Service principal credentials not fully configured in environment variables")

                credential = ClientSecretCredential(
                    tenant_id=tenant_id, client_id=client_id, client_secret=client_secret
                )
            elif self.credential_type == "managed_identity":
                credential = ManagedIdentityCredential()
            else:  # default
                credential = DefaultAzureCredential()

            # Create workspace
            if self.workspace_id and self.resource_id:
                return Workspace(resource_id=self.resource_id, location=self.location, credential=credential)
            else:
                # Try to get from environment variables
                workspace_id = self.workspace_id or os.getenv("AZURE_QUANTUM_WORKSPACE_ID")
                resource_id = self.resource_id or os.getenv("AZURE_QUANTUM_RESOURCE_ID")

                if not workspace_id or not resource_id:
                    raise ValueError("Azure Quantum workspace credentials not provided")

                return Workspace(
                    workspace_id=workspace_id, resource_id=resource_id, location=self.location, credential=credential
                )

        except Exception as e:
            warnings.warn(f"Failed to create Azure Quantum workspace: {e}", stacklevel=2)
            raise RuntimeError(f"Azure Quantum workspace creation failed: {e}") from e

    def _get_or_create_target(self) -> Any:
        """Get or create quantum target."""
        try:
            # Use default simulator for reliability
            target_id = "microsoft.simulator"

            # Get target from workspace
            targets = self.workspace.get_targets()

            # Check if specified target exists
            for target in targets:
                if target.id == target_id:
                    return target

            # If not found, use the first available simulator
            for target in targets:
                if "simulator" in target.id.lower():
                    return target

            # Fallback to first available target
            if targets:
                return targets[0]

            raise RuntimeError("No quantum targets available in workspace")

        except Exception as e:
            warnings.warn(f"Failed to get quantum target: {e}", stacklevel=2)
            raise RuntimeError(f"Target creation failed: {e}") from e

    def simulate(self, circuit: QuantumCircuit, shots: int = 1000) -> dict[str, int]:
        """
        Simulate quantum circuit using Azure Quantum.

        Args:
            circuit: Quantum circuit to simulate
            shots: Number of measurement shots

        Returns:
            Dictionary of measurement counts
        """
        try:
            # Convert Qiskit circuit to Azure Quantum format
            azure_circuit = self._convert_qiskit_to_azure(circuit)

            # Submit job to Azure Quantum
            job = self._submit_job(azure_circuit, shots)

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
                    f"Azure Quantum execution failed: {e}, falling back to local simulator",
                    stacklevel=2,
                )
                return self._simulate_with_qiskit(circuit, shots)
            else:
                raise RuntimeError(f"Azure Quantum simulation failed: {e}") from e

    def _convert_qiskit_to_azure(self, circuit: QuantumCircuit) -> Any:
        """Convert Qiskit circuit to Azure Quantum circuit format."""
        try:
            from azure.quantum.circuit import Circuit as AzureCircuit

            # Create Azure Quantum circuit
            azure_circuit = AzureCircuit()

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
                    self._apply_single_qubit_gate(azure_circuit, gate_name, qubit_indices[0], instruction)

                # Two-qubit gates
                elif len(qubit_indices) == 2:
                    self._apply_two_qubit_gate(azure_circuit, gate_name, qubit_indices, instruction)

                # Multi-qubit gates
                elif len(qubit_indices) >= 3:
                    self._apply_multi_qubit_gate(azure_circuit, gate_name, qubit_indices, instruction)

                else:
                    warnings.warn(f"Unsupported gate: {gate_name}, skipping", stacklevel=2)

            return azure_circuit

        except Exception as e:
            raise RuntimeError(f"Circuit conversion failed: {e}") from e

    def _apply_single_qubit_gate(self, azure_circuit: Any, gate_name: str, qubit: int, instruction: Any) -> None:
        """Apply single-qubit gate to Azure Quantum circuit."""
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
                azure_circuit.x(qubit)
            elif gate_name == "y":
                azure_circuit.y(qubit)
            elif gate_name == "z":
                azure_circuit.z(qubit)
            elif gate_name == "h":
                azure_circuit.h(qubit)
            elif gate_name == "s":
                azure_circuit.s(qubit)
            elif gate_name == "sdg":
                azure_circuit.sdg(qubit)  # S dagger
            elif gate_name == "t":
                azure_circuit.t(qubit)
            elif gate_name == "tdg":
                azure_circuit.tdg(qubit)  # T dagger
            elif gate_name == "rx" and params:
                azure_circuit.rx(params[0], qubit)
            elif gate_name == "ry" and params:
                azure_circuit.ry(params[0], qubit)
            elif gate_name == "rz" and params:
                azure_circuit.rz(params[0], qubit)
            elif gate_name == "p" and params:
                azure_circuit.p(params[0], qubit)
            elif gate_name == "u1" and params:
                azure_circuit.u1(params[0], qubit)
            elif gate_name == "u2" and len(params) >= 2:
                azure_circuit.u2(params[0], params[1], qubit)
            elif gate_name == "u3" and len(params) >= 3:
                azure_circuit.u3(params[0], params[1], params[2], qubit)
            else:
                warnings.warn(f"Unsupported single-qubit gate: {gate_name}", stacklevel=2)

        except Exception as e:
            warnings.warn(f"Failed to apply {gate_name} gate: {e}", stacklevel=2)

    def _apply_two_qubit_gate(
        self, azure_circuit: Any, gate_name: str, qubit_indices: list[int], instruction: Any
    ) -> None:
        """Apply two-qubit gate to Azure Quantum circuit."""
        try:
            control, target = qubit_indices[0], qubit_indices[1]

            if gate_name == "cx" or gate_name == "cnot":
                azure_circuit.cx(control, target)
            elif gate_name == "cy":
                azure_circuit.cy(control, target)
            elif gate_name == "cz":
                azure_circuit.cz(control, target)
            elif gate_name == "swap":
                azure_circuit.swap(control, target)
            elif gate_name == "crx" and instruction.params:
                azure_circuit.crx(float(instruction.params[0]), control, target)
            elif gate_name == "cry" and instruction.params:
                azure_circuit.cry(float(instruction.params[0]), control, target)
            elif gate_name == "crz" and instruction.params:
                azure_circuit.crz(float(instruction.params[0]), control, target)
            else:
                warnings.warn(f"Unsupported two-qubit gate: {gate_name}", stacklevel=2)

        except Exception as e:
            warnings.warn(f"Failed to apply {gate_name} gate: {e}", stacklevel=2)

    def _apply_multi_qubit_gate(
        self, azure_circuit: Any, gate_name: str, qubit_indices: list[int], instruction: Any
    ) -> None:
        """Apply multi-qubit gate to Azure Quantum circuit."""
        try:
            if gate_name == "ccx" or gate_name == "ccnot":
                if len(qubit_indices) >= 3:
                    control1, control2, target = qubit_indices[0], qubit_indices[1], qubit_indices[2]
                    azure_circuit.ccx(control1, control2, target)
            else:
                warnings.warn(f"Unsupported multi-qubit gate: {gate_name}", stacklevel=2)

        except Exception as e:
            warnings.warn(f"Failed to apply {gate_name} gate: {e}", stacklevel=2)

    def _submit_job(self, azure_circuit: Any, shots: int) -> Any:
        """Submit circuit execution job to Azure Quantum."""
        try:
            # Submit job with specified shots
            job = self.target.submit(azure_circuit, shots=shots)
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
                status = job.status

                if status == "Succeeded":
                    return job.get_results()
                elif status == "Failed":
                    raise RuntimeError(f"Job failed with status: {status}")
                elif status == "Cancelled":
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
        """Extract measurement counts from Azure Quantum result."""
        try:
            # Get measurement results
            measurements = result.get("measurements", [])

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
            raise RuntimeError("Neither Azure Quantum nor Qiskit BasicProvider available") from err

    def get_backend_info(self) -> dict[str, Any]:
        """Get information about the backend configuration."""
        info: dict[str, Any] = {
            "name": "azure_quantum",
            "workspace_id": self.workspace_id,
            "resource_id": self.resource_id,
            "location": self.location,
            "azure_quantum_available": self.azure_quantum_available,
            "shots": self.shots,
            "enable_fallback": self.enable_fallback,
            "credential_type": self.credential_type,
            "job_stats": self.job_stats.copy(),
        }

        if self.azure_quantum_available:
            try:
                # Add target information
                info["target_id"] = getattr(self.target, "id", "Unknown")
                info["target_name"] = getattr(self.target, "name", "Unknown")
                info["target_provider"] = getattr(self.target, "provider_id", "Unknown")

                # Add workspace info (without credentials)
                info["workspace_location"] = getattr(self.workspace, "location", "Unknown")

            except Exception as e:
                logger.debug(f"Failed to get Azure backend info: {e}")

        return info

    def get_available_targets(self) -> list[dict[str, Any]]:
        """Get list of available quantum targets in the workspace."""
        try:
            targets = self.workspace.get_targets()

            target_list = []
            for target in targets:
                target_info = {
                    "id": target.id,
                    "name": target.name,
                    "provider_id": target.provider_id,
                    "status": target.current_availability,
                    "average_queue_time": getattr(target, "average_queue_time", None),
                }

                # Add qubit count if available
                if hasattr(target, "qubit_count"):
                    target_info["qubit_count"] = target.qubit_count

                target_list.append(target_info)

            return target_list

        except Exception as e:
            warnings.warn(f"Failed to get available targets: {e}", stacklevel=2)
            return []

    def estimate_cost(self, circuit: QuantumCircuit, shots: int = 1000) -> dict[str, float]:
        """Estimate execution cost for the given circuit."""
        try:
            # Basic cost estimation (simplified)
            if "simulator" in self.target.id.lower():
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
                "target_type": "simulator" if "simulator" in self.target.id.lower() else "hardware",
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

            if "simulator" in self.target.id.lower():
                # Simulators typically support more qubits
                if num_qubits > 30:  # Conservative limit
                    return False, f"Circuit has {num_qubits} qubits, exceeds simulator limit of 30"
            else:
                # Quantum hardware has stricter limits
                # Try to get qubit count from target
                target_qubits = getattr(self.target, "qubit_count", 20)  # Default conservative estimate
                if num_qubits > target_qubits:
                    return False, f"Circuit has {num_qubits} qubits, exceeds target limit of {target_qubits}"

            # Check for unsupported operations
            for instruction in circuit.data:
                gate_name = instruction.operation.name.lower()
                if gate_name in ["measure", "barrier", "delay"]:
                    continue

                # Check if gate is supported
                if not self._is_gate_supported(gate_name):
                    return False, f"Gate '{gate_name}' is not supported by Azure Quantum"

            return True, "Can simulate"

        except Exception as e:
            return False, f"Error checking circuit compatibility: {e}"

    def _is_gate_supported(self, gate_name: str) -> bool:
        """Check if a gate is supported by Azure Quantum."""
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


def is_azure_quantum_available() -> bool:
    """Check if Azure Quantum is available for use."""
    return importlib.util.find_spec("azure.quantum") is not None


def list_azure_quantum_targets(
    workspace_id: str | None = None, resource_id: str | None = None, location: str = "eastus"
) -> list[dict[str, Any]]:
    """List available Azure Quantum targets."""
    if not is_azure_quantum_available():
        return []

    try:
        backend = AzureQuantumBackend(workspace_id=workspace_id, resource_id=resource_id, location=location)
        return backend.get_available_targets()
    except Exception:
        return []


def create_azure_quantum_backend(
    workspace_id: str | None = None,
    resource_id: str | None = None,
    location: str = "eastus",
    shots: int = 1000,
    enable_fallback: bool = True,
    credential_type: str = "default",
    **kwargs: Any,
) -> AzureQuantumBackend:
    """
    Factory function to create an Azure Quantum backend.

    Args:
        workspace_id: Azure Quantum workspace ID
        resource_id: Azure Quantum resource ID
        location: Azure region for the Quantum workspace
        shots: Number of shots for circuit execution
        enable_fallback: Enable fallback to local simulator on cloud failures
        credential_type: Type of Azure credentials to use
        **kwargs: Additional backend options

    Returns:
        Configured AzureQuantumBackend instance
    """
    return AzureQuantumBackend(
        workspace_id=workspace_id,
        resource_id=resource_id,
        location=location,
        shots=shots,
        enable_fallback=enable_fallback,
        credential_type=credential_type,
        **kwargs,
    )


def benchmark_azure_quantum(
    circuits: list[QuantumCircuit],
    shots: int = 1000,
    workspace_id: str | None = None,
    resource_id: str | None = None,
) -> dict[str, Any]:
    """
    Benchmark Azure Quantum backend performance.

    Args:
        circuits: List of quantum circuits to benchmark
        shots: Number of shots per circuit
        workspace_id: Azure Quantum workspace ID
        resource_id: Azure Quantum resource ID

    Returns:
        Benchmark results
    """
    import time

    if not circuits:
        return {"error": "No circuits provided for benchmarking"}

    try:
        backend = create_azure_quantum_backend(workspace_id=workspace_id, resource_id=resource_id, shots=shots)
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
