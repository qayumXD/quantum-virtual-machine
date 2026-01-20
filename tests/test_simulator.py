# tests/test_simulator.py

import pytest
import numpy as np
from src.qvm.ir import QuantumCircuit
from src.qvm.parser import QASMParser
from src.qvm.simulator import Simulator

# Initialize simulator globally for tests
sim = Simulator()

def assert_probabilities_almost_equal(actual_probs, expected_probs, tolerance=1e-7):
    """Helper to assert if probability arrays are almost equal."""
    assert np.allclose(actual_probs, expected_probs, atol=tolerance), \
        f"Expected probabilities {expected_probs}, but got {actual_probs}"

def test_single_qubit_h_gate():
    """Test Hadamard gate on a single qubit."""
    circuit_desc = [{"name": "h", "qubits": [0]}]
    qc = QASMParser.parse(circuit_desc, 1)
    state = sim.simulate(qc)
    probs = sim.get_probabilities(state)
    # H|0> = (1/sqrt(2))(|0> + |1>) -> probs [0.5, 0.5]
    assert_probabilities_almost_equal(probs, [0.5, 0.5])
    # Also check statevector directly if possible
    expected_state = (1/np.sqrt(2)) * np.array([1, 1], dtype=complex)
    assert np.allclose(state, expected_state)

def test_single_qubit_x_gate():
    """Test Pauli-X gate on a single qubit."""
    circuit_desc = [{"name": "x", "qubits": [0]}]
    qc = QASMParser.parse(circuit_desc, 1)
    state = sim.simulate(qc)
    probs = sim.get_probabilities(state)
    # X|0> = |1> -> probs [0.0, 1.0]
    assert_probabilities_almost_equal(probs, [0.0, 1.0])
    expected_state = np.array([0, 1], dtype=complex)
    assert np.allclose(state, expected_state)

def test_single_qubit_ry_pi_over_2_gate():
    """Test RY(pi/2) gate on a single qubit."""
    circuit_desc = [{"name": "ry", "qubits": [0], "params": [np.pi/2]}]
    qc = QASMParser.parse(circuit_desc, 1)
    state = sim.simulate(qc)
    probs = sim.get_probabilities(state)
    # RY(pi/2)|0> = (1/sqrt(2))(|0> + |1>) -> probs [0.5, 0.5]
    assert_probabilities_almost_equal(probs, [0.5, 0.5])
    expected_state = (1/np.sqrt(2)) * np.array([1, 1], dtype=complex)
    assert np.allclose(state, expected_state)

def test_bell_state_circuit():
    """Test the Bell state circuit for two qubits."""
    circuit_desc = [
        {"name": "h", "qubits": [0]},
        {"name": "cx", "qubits": [0, 1]}
    ]
    qc = QASMParser.parse(circuit_desc, 2)
    state = sim.simulate(qc)
    probs = sim.get_probabilities(state)
    # Bell state (Phi+) is (1/sqrt(2))(|00> + |11>) -> probs [0.5, 0.0, 0.0, 0.5]
    expected_probs = [0.5, 0.0, 0.0, 0.5]
    assert_probabilities_almost_equal(probs, expected_probs)
    expected_state = (1/np.sqrt(2)) * np.array([1, 0, 0, 1], dtype=complex)
    assert np.allclose(state, expected_state)

def test_ghz_state_circuit():
    """Test the GHZ state circuit for three qubits."""
    circuit_desc = [
        {"name": "h", "qubits": [0]},
        {"name": "cx", "qubits": [0, 1]},
        {"name": "cx", "qubits": [0, 2]}
    ]
    qc = QASMParser.parse(circuit_desc, 3)
    state = sim.simulate(qc)
    probs = sim.get_probabilities(state)
    # GHZ state is (1/sqrt(2))(|000> + |111>) -> probs [0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5]
    expected_probs = [0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5]
    assert_probabilities_almost_equal(probs, expected_probs)
    expected_state = (1/np.sqrt(2)) * np.array([1, 0, 0, 0, 0, 0, 0, 1], dtype=complex)
    assert np.allclose(state, expected_state)

def test_unsupported_gate():
    """Test handling of unsupported gates."""
    circuit_desc = [{"name": "fredkin", "qubits": [0, 1, 2]}]
    qc = QASMParser.parse(circuit_desc, 3)
    with pytest.raises(ValueError, match="Unsupported gate operation: fredkin"):
        sim.simulate(qc)

def test_invalid_qubit_for_single_gate():
    """Test error for single-qubit gate acting on multiple qubits."""
    circuit_desc = [{"name": "h", "qubits": [0, 1]}]
    qc = QASMParser.parse(circuit_desc, 2)
    with pytest.raises(ValueError, match="gate must act on a single qubit"):
        sim.simulate(qc)

def test_invalid_qubit_for_cnot_gate():
    """Test error for CNOT gate acting on non-two qubits."""
    circuit_desc = [{"name": "cx", "qubits": [0]}]
    qc = QASMParser.parse(circuit_desc, 2)
    with pytest.raises(ValueError, match="gate must act on two qubits"):
        sim.simulate(qc)
