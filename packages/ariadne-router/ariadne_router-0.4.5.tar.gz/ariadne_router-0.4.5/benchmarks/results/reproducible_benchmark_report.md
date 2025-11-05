# Ariadne Benchmark Report
**Timestamp:** 2025-10-29 15:29:21
**Environment:** macOS-26.0.1-arm64-arm-64bit
**Tests:** 13/13 passed

**Average execution time:** 0.2208s
## Backend Usage
- **mps:** 2 circuits (15.4%)
- **pennylane:** 1 circuits (7.7%)
- **stim:** 9 circuits (69.2%)
- **tensor_network:** 1 circuits (7.7%)
## Detailed Results
| Circuit | Backend | Time (s) | Status |
|---------|---------|----------|--------|
| small_clifford_ghz | stim | 0.0489 | ✅ Pass |
| small_clifford_ladder | stim | 0.0017 | ✅ Pass |
| medium_clifford_ghz | stim | 0.0018 | ✅ Pass |
| medium_clifford_stabilizer | stim | 0.0017 | ✅ Pass |
| large_clifford_ghz | stim | 0.0034 | ✅ Pass |
| large_clifford_surface_code | stim | 0.0045 | ✅ Pass |
| small_non_clifford | mps | 0.7187 | ✅ Pass |
| medium_non_clifford | tensor_network | 0.2857 | ✅ Pass |
| mixed_vqe_ansatz | mps | 0.4296 | ✅ Pass |
| mixed_qaoa | pennylane | 1.3710 | ✅ Pass |
| single_qubit | stim | 0.0011 | ✅ Pass |
| no_gates | stim | 0.0011 | ✅ Pass |
| measurement_only | stim | 0.0010 | ✅ Pass |
