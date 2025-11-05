"""Smoke tests exercising all registered algorithms to boost coverage."""

from __future__ import annotations

import pytest

from ariadne.algorithms import AlgorithmParameters, get_algorithm, get_algorithms_by_category, list_algorithms
from ariadne.algorithms.error_correction import SurfaceCode
from ariadne.algorithms.machine_learning import VQC, QuantumNeuralNetwork
from ariadne.algorithms.specialized import AmplitudeAmplification, QuantumWalk

ALGORITHM_PARAMS: dict[str, AlgorithmParameters] = {
    "bell": AlgorithmParameters(n_qubits=2),
    "ghz": AlgorithmParameters(n_qubits=4),
    "qft": AlgorithmParameters(n_qubits=3),
    "qpe": AlgorithmParameters(n_qubits=4),
    "grover": AlgorithmParameters(n_qubits=3, custom_params={"marked_state": "101"}),
    "bernstein_vazirani": AlgorithmParameters(n_qubits=4, custom_params={"hidden_string": "1010"}),
    "qaoa": AlgorithmParameters(
        n_qubits=4,
        custom_params={
            "layers": 3,
            "gamma": [0.1, 0.2, 0.3],
            "beta": [0.4, 0.5, 0.6],
        },
    ),
    "vqe": AlgorithmParameters(n_qubits=4, custom_params={"depth": 2, "hardware_efficient": False}),
    "steane": AlgorithmParameters(
        n_qubits=7, custom_params={"introduce_error": True, "error_qubit": 1, "error_type": "Z"}
    ),
    "qsvm": AlgorithmParameters(
        n_qubits=3,
        custom_params={"use_feature_map": True, "use_variational": True, "data_point": [0.1, 0.2, 0.3]},
    ),
    "deutsch_jozsa": AlgorithmParameters(n_qubits=3, custom_params={"function_type": "parity"}),
    "simon": AlgorithmParameters(n_qubits=6, custom_params={"hidden_period": "101"}),
}


@pytest.mark.parametrize("algorithm_name", sorted(ALGORITHM_PARAMS.keys()))
def test_algorithm_constructors_and_circuits(algorithm_name: str) -> None:
    algorithm_cls = get_algorithm(algorithm_name)
    params = ALGORITHM_PARAMS[algorithm_name]
    algorithm = algorithm_cls(params)

    circuit = algorithm.create_circuit()
    assert circuit.num_qubits >= params.n_qubits

    analysis = algorithm.analyze_circuit_properties()
    assert analysis["n_qubits"] >= params.n_qubits

    education = algorithm.get_educational_content()
    assert "overview" in education and education["overview"]


def test_algorithm_registry_category_lookup() -> None:
    category_map: dict[str, set[str]] = {}
    for name, params in ALGORITHM_PARAMS.items():
        algorithm_cls = get_algorithm(name)
        category = algorithm_cls(params).metadata.category
        category_map.setdefault(category, set()).add(name)

    for category, names in category_map.items():
        registered = set(get_algorithms_by_category(category))
        if registered:
            assert names & registered
        else:
            unknown = set(get_algorithms_by_category("unknown"))
            assert names <= unknown

    assert set(list_algorithms()) == set(ALGORITHM_PARAMS.keys())


def test_unregistered_algorithm_classes_cover_additional_modules() -> None:
    vqc = VQC(
        AlgorithmParameters(n_qubits=3, custom_params={"data_point": [0.1, 0.2, 0.3], "trainable_params": [0.1] * 12})
    )
    vqc_circuit = vqc.create_circuit()
    assert vqc_circuit.num_qubits == 3

    qnn = QuantumNeuralNetwork(
        AlgorithmParameters(
            n_qubits=3,
            custom_params={"input_data": [0.2, 0.3, 0.4], "weights": [0.1] * 18, "layers": 3},
        )
    )
    assert qnn.create_circuit().num_qubits == 3

    surface = SurfaceCode(AlgorithmParameters(n_qubits=9))
    assert surface.create_circuit().num_qubits >= 9

    walk = QuantumWalk(AlgorithmParameters(n_qubits=4, custom_params={"steps": 2}))
    assert walk.create_circuit().num_qubits == 4

    amp = AmplitudeAmplification(AlgorithmParameters(n_qubits=3, custom_params={"iterations": 2}))
    assert amp.create_circuit().num_qubits == 3
