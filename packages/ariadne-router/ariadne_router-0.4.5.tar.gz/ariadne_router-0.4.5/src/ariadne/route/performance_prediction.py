"""
Performance Prediction Models for Dynamic Routing

This module implements performance prediction models for different quantum backends,
including memory scoring, gate complexity scoring, and cost-aware routing for cloud backends.
"""

from __future__ import annotations

from dataclasses import dataclass

from qiskit import QuantumCircuit

from ..router import BackendType
from .analyze import analyze_circuit


@dataclass
class BackendCapabilities:
    """Capabilities and constraints for different backends."""

    max_qubits: int
    memory_limit_mb: float
    cost_per_shot: float  # For cloud backends
    cost_per_task: float  # For cloud backends
    speed_factor: float
    accuracy_factor: float
    parallelizable: bool
    clifford_optimized: bool
    gate_support: set[str]


@dataclass
class PerformanceScores:
    """Performance scores for backend selection."""

    backend: BackendType
    memory_score: float
    gate_complexity_score: float
    cost_score: float
    speed_score: float
    total_score: float
    confidence: float


@dataclass
class HybridExecutionPlan:
    """Plan for hybrid execution across multiple backends."""

    segments: list[tuple[QuantumCircuit, BackendType]]
    partition_points: list[int]
    expected_speedup: float
    cost_estimate: float
    confidence: float


class PerformancePredictor:
    """
    Advanced performance prediction for quantum circuit routing.

    This class implements sophisticated models for predicting execution time,
    memory usage, and cost across different quantum backends.
    """

    def __init__(self) -> None:
        """Initialize the performance predictor with backend capabilities."""
        self.backend_capabilities = self._initialize_backend_capabilities()

        # Performance model parameters
        self.memory_weight = 0.3
        self.complexity_weight = 0.4
        self.cost_weight = 0.2
        self.speed_weight = 0.1

        # Hybrid execution thresholds
        self.hybrid_threshold_qubits = 20
        self.hybrid_threshold_depth = 50

    def _initialize_backend_capabilities(self) -> dict[BackendType, BackendCapabilities]:  # noqa: PLR0915
        """Initialize capabilities for all available backends."""
        capabilities = {
            # Local simulators
            BackendType.STIM: BackendCapabilities(
                max_qubits=100,
                memory_limit_mb=1024.0,
                cost_per_shot=0.0,
                cost_per_task=0.0,
                speed_factor=10.0,
                accuracy_factor=9.5,
                parallelizable=True,
                clifford_optimized=True,
                gate_support={"x", "y", "z", "h", "s", "sdg", "cx", "cz", "swap"},
            ),
            BackendType.QISKIT: BackendCapabilities(
                max_qubits=30,
                memory_limit_mb=8192.0,
                cost_per_shot=0.0,
                cost_per_task=0.0,
                speed_factor=3.0,
                accuracy_factor=8.0,
                parallelizable=False,
                clifford_optimized=False,
                gate_support={"x", "y", "z", "h", "s", "sdg", "cx", "cz", "swap", "rx", "ry", "rz", "u1", "u2", "u3"},
            ),
            BackendType.TENSOR_NETWORK: BackendCapabilities(
                max_qubits=50,
                memory_limit_mb=4096.0,
                cost_per_shot=0.0,
                cost_per_task=0.0,
                speed_factor=6.0,
                accuracy_factor=9.0,
                parallelizable=True,
                clifford_optimized=False,
                gate_support={"x", "y", "z", "h", "s", "sdg", "cx", "cz", "swap", "rx", "ry", "rz", "u1", "u2", "u3"},
            ),
            BackendType.CUDA: BackendCapabilities(
                max_qubits=28,
                memory_limit_mb=16384.0,
                cost_per_shot=0.0,
                cost_per_task=0.0,
                speed_factor=9.0,
                accuracy_factor=7.5,
                parallelizable=True,
                clifford_optimized=False,
                gate_support={"x", "y", "z", "h", "s", "sdg", "cx", "cz", "swap", "rx", "ry", "rz", "u1", "u2", "u3"},
            ),
            BackendType.JAX_METAL: BackendCapabilities(
                max_qubits=25,
                memory_limit_mb=8192.0,
                cost_per_shot=0.0,
                cost_per_task=0.0,
                speed_factor=8.0,
                accuracy_factor=7.0,
                parallelizable=True,
                clifford_optimized=False,
                gate_support={"x", "y", "z", "h", "s", "sdg", "cx", "cz", "swap", "rx", "ry", "rz", "u1", "u2", "u3"},
            ),
            BackendType.MPS: BackendCapabilities(
                max_qubits=100,
                memory_limit_mb=2048.0,
                cost_per_shot=0.0,
                cost_per_task=0.0,
                speed_factor=7.0,
                accuracy_factor=8.5,
                parallelizable=True,
                clifford_optimized=False,
                gate_support={"x", "y", "z", "h", "s", "sdg", "cx", "cz", "swap", "rx", "ry", "rz", "u1", "u2", "u3"},
            ),
            # Cloud backends
            BackendType.AWS_BRAKET: BackendCapabilities(
                max_qubits=34,
                memory_limit_mb=16384.0,
                cost_per_shot=0.00001,
                cost_per_task=0.005,
                speed_factor=5.0,
                accuracy_factor=8.5,
                parallelizable=True,
                clifford_optimized=False,
                gate_support={
                    "x",
                    "y",
                    "z",
                    "h",
                    "s",
                    "sdg",
                    "cx",
                    "cz",
                    "swap",
                    "rx",
                    "ry",
                    "rz",
                    "u1",
                    "u2",
                    "u3",
                    "crx",
                    "cry",
                    "crz",
                    "ccx",
                },
            ),
            BackendType.AZURE_QUANTUM: BackendCapabilities(
                max_qubits=30,
                memory_limit_mb=16384.0,
                cost_per_shot=0.00001,
                cost_per_task=0.005,
                speed_factor=5.0,
                accuracy_factor=8.5,
                parallelizable=True,
                clifford_optimized=False,
                gate_support={
                    "x",
                    "y",
                    "z",
                    "h",
                    "s",
                    "sdg",
                    "cx",
                    "cz",
                    "swap",
                    "rx",
                    "ry",
                    "rz",
                    "u1",
                    "u2",
                    "u3",
                    "crx",
                    "cry",
                    "crz",
                    "ccx",
                },
            ),
        }

        # Add other backends with default capabilities
        for backend in BackendType:
            if backend not in capabilities:
                capabilities[backend] = BackendCapabilities(
                    max_qubits=20,
                    memory_limit_mb=4096.0,
                    cost_per_shot=0.0,
                    cost_per_task=0.0,
                    speed_factor=3.0,
                    accuracy_factor=7.0,
                    parallelizable=False,
                    clifford_optimized=False,
                    gate_support={"x", "y", "z", "h", "s", "sdg", "cx", "cz", "swap"},
                )

        return capabilities

    def calculate_memory_score(self, circuit: QuantumCircuit, backend: BackendType) -> float:
        """
        Calculate memory score based on circuit size and backend memory constraints.

        Args:
            circuit: Quantum circuit to analyze
            backend: Target backend

        Returns:
            Memory score (0.0 to 1.0, higher is better)
        """
        capabilities = self.backend_capabilities[backend]

        # Estimate memory requirement for the circuit
        if circuit.num_qubits <= 20:
            # State vector simulation: 16 bytes per complex number * 2^n
            estimated_memory_mb = (2**circuit.num_qubits) * 16 / (1024 * 1024)
        else:
            # For larger circuits, assume tensor network or MPS simulation
            # Memory scales more favorably for these methods
            estimated_memory_mb = circuit.num_qubits**2 * 16 / (1024 * 1024)

        # Calculate memory efficiency score
        if estimated_memory_mb > capabilities.memory_limit_mb:
            return 0.0  # Cannot fit in memory

        # Higher score for more efficient memory usage
        memory_efficiency = 1.0 - (estimated_memory_mb / capabilities.memory_limit_mb)

        # Boost score for memory-efficient backends
        if backend in [BackendType.TENSOR_NETWORK, BackendType.MPS]:
            memory_efficiency *= 1.2

        return float(min(1.0, memory_efficiency))

    def calculate_gate_complexity_score(self, circuit: QuantumCircuit, backend: BackendType) -> float:
        """
        Calculate gate complexity score based on circuit depth and backend capabilities.

        Args:
            circuit: Quantum circuit to analyze
            backend: Target backend

        Returns:
            Gate complexity score (0.0 to 1.0, higher is better)
        """
        capabilities = self.backend_capabilities[backend]
        analysis = analyze_circuit(circuit)

        # Base complexity score from circuit properties
        depth = analysis.get("depth", 0)
        two_qubit_gates = analysis.get("two_qubit_gates", 0)
        total_gates = analysis.get("total_gates", 0)
        clifford_ratio = analysis.get("clifford_ratio", 0.0)

        # Calculate complexity factors
        depth_factor = 1.0 / (1.0 + depth / 50.0)  # Normalize depth
        gate_factor = 1.0 / (1.0 + total_gates / 100.0)  # Normalize gate count
        entanglement_factor = 1.0 / (1.0 + two_qubit_gates / 20.0)  # Normalize entanglement

        # Backend-specific optimizations
        backend_score = 1.0

        # Clifford circuits get huge boost on Clifford-optimized backends
        if clifford_ratio > 0.9 and capabilities.clifford_optimized:
            backend_score *= 3.0
        elif clifford_ratio > 0.9 and not capabilities.clifford_optimized:
            backend_score *= 0.3

        # Parallelizable backends get boost for parallelizable circuits
        parallelization = analysis.get("parallelization_factor", 1.0)
        if capabilities.parallelizable and parallelization > 2.0:
            backend_score *= 1.5

        # GPU backends get boost for large circuits
        if backend in [BackendType.CUDA, BackendType.JAX_METAL] and circuit.num_qubits > 15:
            backend_score *= 1.3

        # Tensor networks get boost for structured circuits
        if backend == BackendType.TENSOR_NETWORK:
            treewidth = analysis.get("treewidth_estimate", 0)
            if treewidth < 15:
                backend_score *= 1.5

        # MPS gets boost for low-entanglement circuits
        if backend == BackendType.MPS:
            entanglement = analysis.get("entanglement_entropy_estimate", 0.0)
            if entanglement < circuit.num_qubits * 0.3:
                backend_score *= 1.5

        # Combine all factors
        complexity_score = depth_factor * 0.3 + gate_factor * 0.3 + entanglement_factor * 0.2 + backend_score * 0.2

        return float(min(1.0, complexity_score))

    def calculate_cost_score(self, circuit: QuantumCircuit, backend: BackendType, shots: int = 1000) -> float:
        """
        Calculate cost score for cloud backends.

        Args:
            circuit: Quantum circuit to analyze
            backend: Target backend
            shots: Number of shots

        Returns:
            Cost score (0.0 to 1.0, higher is better)
        """
        capabilities = self.backend_capabilities[backend]

        # Local backends have no cost
        if capabilities.cost_per_shot == 0.0 and capabilities.cost_per_task == 0.0:
            return 1.0

        # Calculate estimated cost
        if capabilities.cost_per_shot > 0:
            estimated_cost = capabilities.cost_per_shot * shots
        else:
            estimated_cost = capabilities.cost_per_task

        # Normalize cost (lower cost = higher score)
        # Use a logarithmic scale to handle wide cost ranges
        if estimated_cost <= 0:
            return 1.0

        # Reference cost point (e.g., $0.01)
        reference_cost = 0.01
        cost_score = reference_cost / (reference_cost + estimated_cost)

        return float(min(1.0, cost_score))

    def calculate_speed_score(self, circuit: QuantumCircuit, backend: BackendType) -> float:
        """
        Calculate speed score based on backend speed factors and circuit properties.

        Args:
            circuit: Quantum circuit to analyze
            backend: Target backend

        Returns:
            Speed score (0.0 to 1.0, higher is better)
        """
        capabilities = self.backend_capabilities[backend]
        analysis = analyze_circuit(circuit)

        # Base speed score from backend capabilities
        base_speed = capabilities.speed_factor / 10.0  # Normalize to 0-1 range

        # Adjust for circuit properties
        clifford_ratio = analysis.get("clifford_ratio", 0.0)
        parallelization = analysis.get("parallelization_factor", 1.0)

        # Clifford-optimized backends get massive boost for Clifford circuits
        if clifford_ratio > 0.9 and capabilities.clifford_optimized:
            base_speed = min(1.0, base_speed * 3.0)

        # Parallelizable backends get boost for parallelizable circuits
        if capabilities.parallelizable and parallelization > 2.0:
            base_speed = min(1.0, base_speed * 1.2)

        return float(min(1.0, base_speed))

    def predict_backend_performance(
        self, circuit: QuantumCircuit, backend: BackendType, shots: int = 1000
    ) -> PerformanceScores:
        """
        Predict overall performance for a circuit on a specific backend.

        Args:
            circuit: Quantum circuit to analyze
            backend: Target backend
            shots: Number of shots

        Returns:
            Performance scores for the backend
        """
        # Check if backend can handle the circuit
        capabilities = self.backend_capabilities[backend]
        if circuit.num_qubits > capabilities.max_qubits:
            return PerformanceScores(
                backend=backend,
                memory_score=0.0,
                gate_complexity_score=0.0,
                cost_score=0.0,
                speed_score=0.0,
                total_score=0.0,
                confidence=0.0,
            )

        # Calculate individual scores
        memory_score = self.calculate_memory_score(circuit, backend)
        gate_complexity_score = self.calculate_gate_complexity_score(circuit, backend)
        cost_score = self.calculate_cost_score(circuit, backend, shots)
        speed_score = self.calculate_speed_score(circuit, backend)

        # Calculate combined score using the specified formula: memory_score * gate_complexity_score
        combined_score = memory_score * gate_complexity_score

        # Apply weights for final score
        total_score = (
            self.memory_weight * memory_score
            + self.complexity_weight * gate_complexity_score
            + self.cost_weight * cost_score
            + self.speed_weight * speed_score
        )

        # Calculate confidence based on how well the backend matches the circuit
        confidence = min(1.0, combined_score)

        return PerformanceScores(
            backend=backend,
            memory_score=memory_score,
            gate_complexity_score=gate_complexity_score,
            cost_score=cost_score,
            speed_score=speed_score,
            total_score=total_score,
            confidence=confidence,
        )

    def should_use_hybrid_execution(self, circuit: QuantumCircuit) -> bool:
        """
        Determine if hybrid execution should be used for a circuit.

        Args:
            circuit: Quantum circuit to analyze

        Returns:
            True if hybrid execution is recommended
        """
        # Use hybrid execution for large or deep circuits
        if circuit.num_qubits > self.hybrid_threshold_qubits:
            return True

        if circuit.depth() > self.hybrid_threshold_depth:
            return True

        # Also consider circuit complexity
        analysis = analyze_circuit(circuit)
        classical_complexity = analysis.get("classical_simulation_complexity", 0.0)

        # If classical complexity is very high, hybrid execution might help
        if classical_complexity > 1e6:
            return True

        return False

    def create_hybrid_execution_plan(self, circuit: QuantumCircuit, shots: int = 1000) -> HybridExecutionPlan:
        """
        Create a plan for hybrid execution across multiple backends.

        Args:
            circuit: Quantum circuit to execute
            shots: Number of shots

        Returns:
            Hybrid execution plan
        """
        analysis = analyze_circuit(circuit)
        clifford_ratio = analysis.get("clifford_ratio", 0.0)

        segments = []
        partition_points = []

        # Strategy 1: Partition by Clifford/non-Clifford regions
        if clifford_ratio > 0.2 and clifford_ratio < 0.8:
            clifford_segment, non_clifford_segment = self._partition_by_clifford_regions(circuit)
            if clifford_segment and non_clifford_segment:
                segments.append((clifford_segment, BackendType.STIM))
                segments.append((non_clifford_segment, BackendType.TENSOR_NETWORK))
                partition_points.append(clifford_segment.num_qubits)

        # Strategy 2: Partition by circuit depth
        elif circuit.depth() > self.hybrid_threshold_depth:
            depth_segments = self._partition_by_depth(circuit)
            for i, segment in enumerate(depth_segments):
                # Choose optimal backend for each segment
                best_backend = self._find_best_backend_for_segment(segment, shots)
                segments.append((segment, best_backend))
                if i > 0:
                    partition_points.append(sum(s.num_qubits for s in depth_segments[:i]))

        # Strategy 3: Partition by qubit count
        elif circuit.num_qubits > self.hybrid_threshold_qubits:
            qubit_segments = self._partition_by_qubits(circuit)
            for i, segment in enumerate(qubit_segments):
                best_backend = self._find_best_backend_for_segment(segment, shots)
                segments.append((segment, best_backend))
                if i > 0:
                    partition_points.append(sum(s.num_qubits for s in qubit_segments[:i]))

        # If no partitioning strategy worked, use single backend
        if not segments:
            best_backend = self._find_best_backend_for_segment(circuit, shots)
            segments.append((circuit, best_backend))

        # Calculate expected speedup and cost
        expected_speedup = self._estimate_hybrid_speedup(segments)
        cost_estimate = self._estimate_hybrid_cost(segments, shots)

        return HybridExecutionPlan(
            segments=segments,
            partition_points=partition_points,
            expected_speedup=expected_speedup,
            cost_estimate=cost_estimate,
            confidence=0.8,  # High confidence for hybrid execution
        )

    def _partition_by_clifford_regions(
        self, circuit: QuantumCircuit
    ) -> tuple[QuantumCircuit | None, QuantumCircuit | None]:
        """Partition circuit into Clifford and non-Clifford regions."""
        from qiskit import QuantumCircuit

        clifford_gates = {"x", "y", "z", "h", "s", "sdg", "cx", "cz", "swap"}

        clifford_circuit = QuantumCircuit(circuit.num_qubits)
        non_clifford_circuit = QuantumCircuit(circuit.num_qubits)

        has_clifford = False
        has_non_clifford = False

        for instruction, qubits, clbits in circuit.data:
            gate_name = instruction.operation.name

            if gate_name in clifford_gates:
                clifford_circuit.append(instruction, qubits, clbits)
                has_clifford = True
            else:
                non_clifford_circuit.append(instruction, qubits, clbits)
                has_non_clifford = True

        return (clifford_circuit if has_clifford else None, non_clifford_circuit if has_non_clifford else None)

    def _partition_by_depth(self, circuit: QuantumCircuit, max_depth: int = 25) -> list[QuantumCircuit]:
        """Partition circuit by depth to create smaller segments."""
        from qiskit import QuantumCircuit

        if circuit.depth() <= max_depth:
            return [circuit]

        segments = []
        current_segment = QuantumCircuit(circuit.num_qubits)
        current_depth = 0

        for instruction, qubits, clbits in circuit.data:
            # Estimate depth contribution of this instruction
            depth_contribution = 1  # Simplified assumption

            if current_depth + depth_contribution > max_depth:
                # Save current segment and start a new one
                segments.append(current_segment)
                current_segment = QuantumCircuit(circuit.num_qubits)
                current_depth = 0

            current_segment.append(instruction, qubits, clbits)
            current_depth += depth_contribution

        # Add the last segment
        if current_segment.data:
            segments.append(current_segment)

        return segments

    def _partition_by_qubits(self, circuit: QuantumCircuit, max_qubits: int = 15) -> list[QuantumCircuit]:
        """Partition circuit by qubit count to create smaller segments."""
        from qiskit import QuantumCircuit

        if circuit.num_qubits <= max_qubits:
            return [circuit]

        # Simple strategy: split qubits in half
        mid = circuit.num_qubits // 2

        # Create two segments with different qubit subsets
        segment1 = QuantumCircuit(mid)
        segment2 = QuantumCircuit(circuit.num_qubits - mid)

        # This is a simplified implementation
        # A more sophisticated approach would analyze qubit connectivity
        for instruction, qubits, clbits in circuit.data:
            # Determine which segment this instruction belongs to
            qubit_indices = [circuit.qubits.index(q) for q in qubits]

            if all(idx < mid for idx in qubit_indices):
                # Instruction belongs to first segment
                new_qubits = [segment1.qubits[idx] for idx in qubit_indices]
                segment1.append(instruction, new_qubits, clbits)
            else:
                # Instruction belongs to second segment
                new_qubits = [segment2.qubits[idx - mid] for idx in qubit_indices if idx >= mid]
                segment2.append(instruction, new_qubits, clbits)

        return [segment1, segment2]

    def _find_best_backend_for_segment(self, segment: QuantumCircuit, shots: int) -> BackendType:
        """Find the best backend for a specific circuit segment."""
        best_score = 0.0
        best_backend = BackendType.QISKIT  # Default fallback

        for backend in BackendType:
            scores = self.predict_backend_performance(segment, backend, shots)
            if scores.total_score > best_score:
                best_score = scores.total_score
                best_backend = backend

        return best_backend

    def _estimate_hybrid_speedup(self, segments: list[tuple[QuantumCircuit, BackendType]]) -> float:
        """Estimate speedup from hybrid execution."""
        if len(segments) <= 1:
            return 1.0

        # Simplified speedup estimation
        # In practice, this would consider parallel execution and backend-specific optimizations
        base_time = sum(self._estimate_segment_time(seg, backend) for seg, backend in segments)

        # Assume some parallelization is possible
        parallel_time = base_time / len(segments) * 0.7  # 30% efficiency gain

        return base_time / parallel_time if parallel_time > 0 else 1.0

    def _estimate_segment_time(self, segment: QuantumCircuit, backend: BackendType) -> float:
        """Estimate execution time for a circuit segment."""
        capabilities = self.backend_capabilities[backend]

        # Base time from backend speed factor
        base_time = 1.0 / capabilities.speed_factor if capabilities.speed_factor > 0 else 1.0

        # Adjust for circuit complexity
        complexity_factor = 1.0 + segment.depth() / 50.0
        qubit_factor = 1.0 + segment.num_qubits / 20.0

        return float(base_time * complexity_factor * qubit_factor)

    def _estimate_hybrid_cost(self, segments: list[tuple[QuantumCircuit, BackendType]], shots: int) -> float:
        """Estimate total cost for hybrid execution."""
        total_cost = 0.0

        for _segment, backend in segments:
            capabilities = self.backend_capabilities[backend]

            if capabilities.cost_per_shot > 0:
                total_cost += capabilities.cost_per_shot * shots
            elif capabilities.cost_per_task > 0:
                total_cost += capabilities.cost_per_task

        return total_cost
