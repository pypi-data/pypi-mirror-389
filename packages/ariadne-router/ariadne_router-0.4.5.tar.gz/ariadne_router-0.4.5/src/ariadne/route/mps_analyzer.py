"""Analyzes a quantum circuit to determine if it's suitable for MPS simulation."""

import math

from qiskit import QuantumCircuit

from .topology_analyzer import detect_layout_properties


def should_use_mps(circuit: QuantumCircuit) -> bool:
    """
    The Feynman Intuition: Why Matrix Product States (MPS) work.

    Look, the universe is complicated, but sometimes, it's just not *that* complicated.
    Quantum mechanics tells us that a system of N qubits lives in a Hilbert space
    of dimension 2^N. That's a big number, exponentially big! If we had to keep track
    of all 2^N amplitudes, we'd run out of memory before we hit 50 qubits.

    But here's the trick, the physical intuition: most physically relevant states
    don't use that whole space. They are *sparse* in a very specific way.
    The entanglement between two halves of the system, when you cut it, often
    doesn't grow with the volume (the number of qubits), but only with the
    *area* (the boundary between the two halves). This is the "Area Law."

    Matrix Product States (MPS) exploit this. Instead of storing 2^N numbers,
    we store a chain of matrices. The size of these matrices—the 'bond dimension' (D)—
    is what limits the entanglement we can represent. If the entanglement is low,
    D can be small (maybe constant or logarithmic in N), and the simulation scales
    polynomially, not exponentially. It's a beautiful, simple idea: if the physics
    is local, the description should be local too.

    This function uses a simple heuristic to guess if the circuit is 'local enough'
    or 'small enough' to keep the entanglement low and the bond dimension manageable.

    Heuristic Criteria:
    1. Small System Size: Fewer than 15 qubits. (N < 15)
       - Count two-qubit gates and check if below threshold 2 * N^1.5
       - Also verify shallow depth (depth <= 5 * sqrt(N))
    2. Large System with Low Max Degree: For circuits with ≥15 qubits
       - Check if max degree in interaction graph ≤ 2 (chain-like or sparse)
       - Verify shallow depth relative to circuit width (depth <= N)
       - This handles low-entanglement structures like nearest-neighbor circuits

    Args:
        circuit: The quantum circuit to analyze.

    Returns:
        True if the circuit is likely suitable for efficient MPS simulation, False otherwise.
    """
    num_qubits = circuit.num_qubits
    depth = circuit.depth()

    # For small circuits, use the original two-qubit gate counting heuristic
    if num_qubits < 15:
        # Count two-qubit gates (entangling gates)
        two_qubit_gates = 0
        for instruction in circuit.data:
            if len(instruction.qubits) == 2:
                # We assume any two-qubit gate is an entangling gate for this heuristic
                # (e.g., CNOT, CZ, RXX, etc.)
                two_qubit_gates += 1

        # The threshold for two-qubit gates: 2 * N^1.5
        threshold = 2 * math.pow(num_qubits, 1.5)

        # Also check depth - deep circuits have high entanglement even with few gates
        depth_threshold = 5 * math.sqrt(num_qubits)

        return two_qubit_gates < threshold and depth <= depth_threshold

    # For larger circuits (≥15 qubits), check topology
    # Circuits with low max degree and shallow depth can still benefit from MPS
    try:
        props = detect_layout_properties(circuit)
        max_degree = int(props.get("max_degree", num_qubits))

        # Accept sparse circuits (max degree <= 2) with shallow depth
        # Shallow means depth doesn't exceed the number of qubits
        is_sparse = max_degree <= 2
        is_shallow = depth <= num_qubits

        return is_sparse and is_shallow
    except Exception:
        # If topology analysis fails, default to conservative False for large circuits
        return False
