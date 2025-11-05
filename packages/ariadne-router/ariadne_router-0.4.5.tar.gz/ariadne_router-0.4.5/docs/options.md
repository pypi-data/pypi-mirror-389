# Ariadne Configuration Options

This page provides a comprehensive list of all the configuration options available in Ariadne.

## Global Options

| Option | Type | Default | Description |
|---|---|---|---|
| `default_shots` | `int` | `1000` | Default number of shots for simulations. |
| `random_seed` | `int` | `None` | Global random seed for reproducibility. |
| `log_level` | `str` | `"INFO"` | Logging level for the Ariadne logger. |
| `cache_dir` | `str` | `None` | Directory to store cached results. |
| `data_dir` | `str` | `None` | Directory to store other Ariadne data. |

## Backend Options

These options can be configured for each backend individually.

| Option | Type | Default | Description |
|---|---|---|---|
| `priority` | `int` | `5` | Priority of the backend in the routing decision (1-10, higher is more preferred). |
| `enabled` | `bool` | `True` | Enable or disable the backend. |
| `capacity_boost` | `float` | `1.0` | A factor to boost the perceived capacity of the backend. |
| `memory_limit_mb` | `int` | `None` | Memory limit for the backend in megabytes. |
| `timeout_seconds` | `float` | `None` | Timeout for the backend in seconds. |
| `device_id` | `int` | `0` | ID of the GPU device to use. |
| `use_gpu` | `bool` | `True` | Whether to use the GPU for this backend. |
| `custom_options` | `dict` | `{}` | Backend-specific custom options. |

## Optimization Options

| Option | Type | Default | Description |
|---|---|---|---|
| `default_level` | `int` | `2` | Default optimization level (0-3). |
| `enable_synthesis` | `bool` | `True` | Enable circuit synthesis. |
| `enable_commutation_analysis` | `bool` | `True` | Enable commutation analysis. |
| `enable_gate_fusion` | `bool` | `True` | Enable gate fusion. |
| `basis_gates` | `list[str]` | `None` | List of basis gates for transpilation. |
| `coupling_map` | `list[list[int]]` | `None` | Coupling map for transpilation. |
| `seed_transpiler` | `int` | `None` | Seed for the transpiler. |
| `max_optimization_passes` | `int` | `100` | Maximum number of optimization passes. |
| `optimization_timeout` | `float` | `30.0` | Timeout for the optimization process in seconds. |

## Error Mitigation Options

| Option | Type | Default | Description |
|---|---|---|---|
| `enable_zne` | `bool` | `False` | Enable Zero-Noise Extrapolation (ZNE). |
| `enable_cdr` | `bool` | `False` | Enable Clifford Data Regression (CDR). |
| `enable_symmetry_verification` | `bool` | `False` | Enable symmetry verification. |
| `zne_noise_factors` | `list[float]` | `[1.0, 1.5, 2.0]` | Noise factors for ZNE. |
| `zne_extrapolation_method` | `str` | `"linear"` | Extrapolation method for ZNE. |
| `cdr_clifford_fraction` | `float` | `0.1` | Fraction of Clifford circuits to use for CDR. |
| `cdr_num_training_circuits` | `int` | `100` | Number of training circuits for CDR. |

## Analysis Options

| Option | Type | Default | Description |
|---|---|---|---|
| `enable_quantum_advantage_detection` | `bool` | `True` | Enable quantum advantage detection. |
| `enable_resource_estimation` | `bool` | `True` | Enable resource estimation. |
| `enable_performance_prediction` | `bool` | `True` | Enable performance prediction. |
| `advantage_confidence_threshold` | `float` | `0.7` | Confidence threshold for quantum advantage. |
| `classical_intractability_threshold` | `int` | `30` | Qubit threshold for classical intractability. |
| `include_fault_tolerant_estimates` | `bool` | `False` | Include fault-tolerant estimates in resource estimation. |
| `target_error_rate` | `float` | `1e-6` | Target error rate for fault-tolerant estimation. |

## Performance Options

| Option | Type | Default | Description |
|---|---|---|---|
| `enable_result_caching` | `bool` | `True` | Enable result caching. |
| `cache_size_mb` | `int` | `1024` | Size of the result cache in megabytes. |
| `cache_ttl_hours` | `int` | `24` | Time-to-live for cached results in hours. |
| `enable_performance_tracking` | `bool` | `True` | Enable performance tracking. |
| `enable_calibration` | `bool` | `True` | Enable backend calibration. |
| `calibration_interval_simulations` | `int` | `10` | Number of simulations between calibrations. |
| `memory_pool_size_mb` | `int` | `4096` | Size of the memory pool in megabytes. |
| `enable_memory_mapping` | `bool` | `True` | Enable memory mapping. |
| `cleanup_interval_minutes` | `int` | `30` | Interval for cleaning up memory in minutes. |
