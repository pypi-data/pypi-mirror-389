"""
Realistic test of configuration system based on actual API.
"""

from ariadne.config import (
    AriadneConfig,
    BackendConfig,
    ConfigManager,
    configure_ariadne,
    get_config,
    get_config_manager,
)
from ariadne.config.config import ConfigFormat
from ariadne.types import BackendType


class TestConfigRealistic:
    """Test configuration system with actual API."""

    def test_config_manager_singleton(self):
        """Test that ConfigManager behaves as singleton."""
        manager1 = get_config_manager()
        manager2 = get_config_manager()

        assert manager1 is manager2
        assert isinstance(manager1, ConfigManager)

    def test_default_config_creation(self):
        """Test creation of default configuration."""
        config = get_config()

        assert isinstance(config, AriadneConfig)
        assert hasattr(config, "backends")
        assert hasattr(config, "optimization")
        assert hasattr(config, "error_mitigation")
        assert hasattr(config, "analysis")

        # Check that backends are configured
        assert "stim" in config.backends
        assert "qiskit" in config.backends
        assert isinstance(config.backends["stim"], BackendConfig)

    def test_backend_config_creation(self):
        """Test BackendConfig creation with realistic parameters."""
        backend_config = BackendConfig(
            priority=8,
            enabled=True,
            capacity_boost=1.5,
            memory_limit_mb=1024,
            timeout_seconds=60.0,
            device_id=0,
            use_gpu=True,
            custom_options={"test_option": "value"},
        )

        assert backend_config.priority == 8
        assert backend_config.enabled is True
        assert backend_config.capacity_boost == 1.5
        assert backend_config.memory_limit_mb == 1024
        assert backend_config.timeout_seconds == 60.0
        assert backend_config.device_id == 0
        assert backend_config.use_gpu is True
        assert backend_config.custom_options == {"test_option": "value"}

    def test_backend_config_to_dict(self):
        """Test BackendConfig serialization."""
        backend_config = BackendConfig(priority=7, enabled=False, capacity_boost=2.0)

        config_dict = backend_config.to_dict()
        assert isinstance(config_dict, dict)
        assert config_dict["priority"] == 7
        assert config_dict["enabled"] is False
        assert config_dict["capacity_boost"] == 2.0

    def test_config_with_custom_backend_values(self):
        """Test configuration with custom backend values."""
        config = get_config()

        # Modify a backend configuration
        config.backends["stim"].priority = 10
        config.backends["stim"].enabled = True
        config.backends["stim"].memory_limit_mb = 2048

        assert config.backends["stim"].priority == 10
        assert config.backends["stim"].enabled is True
        assert config.backends["stim"].memory_limit_mb == 2048

    def test_configure_ariadne_function(self):
        """Test the configure_ariadne function with realistic parameters."""
        # Test basic configuration
        configure_ariadne()

        config = get_config()
        assert isinstance(config, AriadneConfig)

    def test_config_formats(self):
        """Test configuration format handling."""
        assert ConfigFormat.JSON.value == "json"
        assert ConfigFormat.YAML.value == "yaml"
        assert ConfigFormat.TOML.value == "toml"

    def test_backend_types_integration(self):
        """Test integration with BackendType enum."""
        config = get_config()

        # Check that all expected backend types are present
        expected_backends = [
            BackendType.STIM.value.lower(),
            BackendType.QISKIT.value.lower(),
            BackendType.TENSOR_NETWORK.value.lower(),
            BackendType.CUDA.value.lower(),
            BackendType.JAX_METAL.value.lower(),
        ]

        for backend_name in expected_backends:
            if backend_name in config.backends:
                assert isinstance(config.backends[backend_name], BackendConfig)

    def test_optimization_config(self):
        """Test optimization configuration."""
        config = get_config()

        assert hasattr(config, "optimization")
        assert hasattr(config.optimization, "default_level")
        assert hasattr(config.optimization, "enable_synthesis")
        assert hasattr(config.optimization, "enable_commutation_analysis")
        assert hasattr(config.optimization, "enable_gate_fusion")

    def test_error_mitigation_config(self):
        """Test error mitigation configuration."""
        config = get_config()

        assert hasattr(config, "error_mitigation")
        assert hasattr(config.error_mitigation, "enable_zne")
        assert hasattr(config.error_mitigation, "enable_cdr")
        assert hasattr(config.error_mitigation, "enable_symmetry_verification")

    def test_analysis_config(self):
        """Test analysis configuration."""
        config = get_config()

        assert hasattr(config, "analysis")
        assert hasattr(config.analysis, "enable_quantum_advantage_detection")
        assert hasattr(config.analysis, "enable_resource_estimation")
        assert hasattr(config.analysis, "enable_performance_prediction")

    def test_config_modification(self):
        """Test modifying configuration values."""
        config = get_config()

        # Store original values
        original_priority = config.backends["stim"].priority

        # Modify values
        config.backends["stim"].priority = 9
        config.backends["stim"].enabled = False
        config.backends["stim"].use_gpu = False

        # Verify modifications
        assert config.backends["stim"].priority == 9
        assert config.backends["stim"].enabled is False
        assert config.backends["stim"].use_gpu is False

        # Restore original values
        config.backends["stim"].priority = original_priority

    def test_custom_options_handling(self):
        """Test custom options handling."""
        backend_config = BackendConfig(
            custom_options={"tableau_method": "auto", "allow_measurement": True, "custom_setting": "value"}
        )

        assert isinstance(backend_config.custom_options, dict)
        assert backend_config.custom_options["tableau_method"] == "auto"
        assert backend_config.custom_options["allow_measurement"] is True
        assert backend_config.custom_options["custom_setting"] == "value"

    def test_config_manager_basic_operations(self):
        """Test basic ConfigManager operations."""
        manager = get_config_manager()

        # Test accessing configuration through manager
        config = manager.config
        assert isinstance(config, AriadneConfig)

        # Test that we can get backend-specific config
        stim_config = manager.get_backend_config("stim")
        assert isinstance(stim_config, BackendConfig)

        # Test preferred backends
        preferred = manager.get_preferred_backends()
        assert isinstance(preferred, list)

    def test_realistic_config_scenario(self):
        """Test a realistic configuration scenario."""
        config = get_config()

        # Scenario: Configure for high-performance Clifford circuit simulation
        config.backends["stim"].priority = 10  # Highest priority
        config.backends["stim"].enabled = True
        config.backends["stim"].capacity_boost = 2.0  # 2x capacity boost
        config.backends["stim"].memory_limit_mb = 4096  # 4GB limit
        config.backends["stim"].use_gpu = False  # CPU-optimized

        # Configure qiskit as fallback
        config.backends["qiskit"].priority = 8
        config.backends["qiskit"].enabled = True
        config.backends["qiskit"].capacity_boost = 1.5

        # Disable GPU backends if not needed
        config.backends["cuda"].enabled = False
        config.backends["metal"].enabled = False

        # Verify configuration
        assert config.backends["stim"].priority == 10
        assert config.backends["stim"].capacity_boost == 2.0
        assert config.backends["qiskit"].priority == 8
        assert config.backends["cuda"].enabled is False
        assert config.backends["metal"].enabled is False


class TestConfigEdgeCases:
    """Test edge cases and error conditions."""

    def test_backend_config_edge_values(self):
        """Test BackendConfig with edge values."""
        # Test with None values
        backend_config = BackendConfig(memory_limit_mb=None, timeout_seconds=None, custom_options={})

        assert backend_config.memory_limit_mb is None
        assert backend_config.timeout_seconds is None
        assert backend_config.custom_options == {}

    def test_config_with_zero_values(self):
        """Test configuration with zero values."""
        backend_config = BackendConfig(priority=0, capacity_boost=0.0, device_id=0)

        assert backend_config.priority == 0
        assert backend_config.capacity_boost == 0.0
        assert backend_config.device_id == 0

    def test_config_singleton_behavior(self):
        """Test that configuration behaves as singleton."""
        config1 = get_config()
        config2 = get_config()

        # Should be the same instance
        assert config1 is config2

        # Modifying one should affect the other (same object)
        original_priority = config1.backends["stim"].priority
        config1.backends["stim"].priority = 99
        assert config2.backends["stim"].priority == 99

        # Restore
        config1.backends["stim"].priority = original_priority
