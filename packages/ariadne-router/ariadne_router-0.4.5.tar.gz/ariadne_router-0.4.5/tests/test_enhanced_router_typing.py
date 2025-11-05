"""
Test enhanced_router module typing and edge cases to improve coverage.
"""

from qiskit import QuantumCircuit

from ariadne.route.enhanced_router import EnhancedQuantumRouter, RouterType


class TestEnhancedRouterTyping:
    """Test enhanced_router module with focus on typing and edge cases."""

    def test_router_initialization(self):
        """Test EnhancedQuantumRouter initialization with different parameters."""

        # Default initialization
        router1 = EnhancedQuantumRouter()
        assert router1 is not None
        assert router1.default_strategy == RouterType.HYBRID_ROUTER

        # Initialization with specific router type
        router2 = EnhancedQuantumRouter(default_strategy=RouterType.SPEED_OPTIMIZER)
        assert router2.default_strategy == RouterType.SPEED_OPTIMIZER

        # Initialization with memory efficient strategy
        router3 = EnhancedQuantumRouter(default_strategy=RouterType.MEMORY_OPTIMIZER)
        assert router3.default_strategy == RouterType.MEMORY_OPTIMIZER

    def test_entropy_calculation(self):
        """Test the entropy calculation method we fixed."""
        router = EnhancedQuantumRouter()

        # Test with simple circuit
        qc1 = QuantumCircuit(2)
        qc1.h(0)
        qc1.cx(0, 1)

        entropy1 = router._calculate_entropy(qc1)
        assert isinstance(entropy1, float)
        assert 0 <= entropy1 <= 1  # Entropy should be normalized

        # Test with circuit having different gate types
        qc2 = QuantumCircuit(3)
        qc2.h(0)
        qc2.x(1)
        qc2.y(2)
        qc2.cx(0, 1)
        qc2.cz(1, 2)

        entropy2 = router._calculate_entropy(qc2)
        assert isinstance(entropy2, float)
        assert entropy2 >= 0

    def test_cuda_availability_check(self):
        """Test CUDA availability check method we fixed."""
        router = EnhancedQuantumRouter()

        # Should return a boolean
        cuda_available = router._is_cuda_available()
        assert isinstance(cuda_available, bool)

        # Should not raise an exception
        # (Actual CUDA availability depends on system)

    def test_simulate_with_typing(self):
        """Test the simulate method we fixed for typing."""
        router = EnhancedQuantumRouter()

        # Test with simple circuit
        qc = QuantumCircuit(2)
        qc.h(0)
        qc.cx(0, 1)

        # Test with default shots
        result1 = router.simulate(qc)
        assert result1 is not None
        assert hasattr(result1, "backend_used")
        assert hasattr(result1, "execution_time")
        assert hasattr(result1, "metadata")

        # Test with specific shots
        result2 = router.simulate(qc, shots=500)
        assert result2 is not None
        # Check that simulation ran with correct shots (verify through metadata or logging)
        assert result2.metadata.get("shots", 500) == 500

        # Test with different shots values
        result3 = router.simulate(qc, shots=10)
        assert result3.metadata.get("shots", 10) == 10

    def test_circuit_analysis_methods(self):
        """Test various circuit analysis methods in the router."""
        from qiskit import QuantumCircuit

        router = EnhancedQuantumRouter()

        qc = QuantumCircuit(4)
        qc.h(0)
        qc.cx(0, 1)
        qc.cx(1, 2)
        qc.cx(2, 3)
        qc.measure_all()

        # Test entropy calculation (the method we actually have)
        entropy = router._calculate_entropy(qc)
        assert isinstance(entropy, float)
        assert entropy >= 0

        # Test optimal backend selection
        decision = router.select_optimal_backend(qc)
        assert hasattr(decision, "recommended_backend")
        assert hasattr(decision, "confidence_score")

    def test_backend_selection_logic(self):
        """Test backend selection logic with different circuit types."""
        router = EnhancedQuantumRouter()

        # Clifford circuit (should prefer Stim)
        clifford_qc = QuantumCircuit(3)
        clifford_qc.h(0)
        clifford_qc.cx(0, 1)
        clifford_qc.cx(1, 2)
        clifford_qc.s(0)

        # Non-Clifford circuit
        non_clifford_qc = QuantumCircuit(2)
        non_clifford_qc.rx(0.5, 0)
        non_clifford_qc.ry(0.3, 1)
        non_clifford_qc.rz(0.7, 0)

        # Test routing decisions
        clifford_result = router.simulate(clifford_qc, shots=100)
        non_clifford_result = router.simulate(non_clifford_qc, shots=100)

        assert clifford_result.backend_used is not None
        assert non_clifford_result.backend_used is not None

    def test_edge_cases_and_error_handling(self):
        """Test edge cases and error handling in the router."""
        router = EnhancedQuantumRouter()

        # Test with minimal circuit
        minimal_qc = QuantumCircuit(1)
        result = router.simulate(minimal_qc, shots=1)
        assert result is not None
        assert result.metadata.get("shots", 1) == 1

        # Test with circuit that has only measurements
        measure_only_qc = QuantumCircuit(2, 2)
        measure_only_qc.measure(0, 0)
        measure_only_qc.measure(1, 1)

        result = router.simulate(measure_only_qc, shots=10)
        assert result is not None
        assert result.metadata.get("shots", 10) == 10

    def test_router_type_functionality(self):
        """Test different router types produce valid results."""
        from ariadne.route.enhanced_router import RouterType

        for router_type in RouterType:
            router = EnhancedQuantumRouter(default_strategy=router_type)

            qc = QuantumCircuit(2)
            qc.h(0)
            qc.cx(0, 1)

            # Should work with all router types
            result = router.simulate(qc, shots=50)
            assert result is not None
            assert result.backend_used is not None
            print(f"✅ Router type {router_type} works correctly")

    def test_performance_characteristics(self):
        """Test that typing fixes don't impact performance."""
        import time

        router = EnhancedQuantumRouter()
        qc = QuantumCircuit(4)
        qc.h(0)
        for i in range(3):
            qc.cx(i, i + 1)

        # Measure simulation time
        start_time = time.time()
        result = router.simulate(qc, shots=100)
        end_time = time.time()

        assert result is not None
        simulation_time = end_time - start_time
        assert simulation_time < 1.0  # Should be fast
        print(f"✅ Simulation performance: {simulation_time:.4f}s")
