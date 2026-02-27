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

def test_sampling_bell_state_counts():
    """Sampling should reflect Bell state probabilities."""
    circuit_desc = [
        {"name": "h", "qubits": [0]},
        {"name": "cx", "qubits": [0, 1]},
    ]
    qc = QASMParser.parse(circuit_desc, 2)
    counts = sim.sample(qc, shots=2000, seed=42)
    total = sum(counts.values())
    assert set(counts.keys()) == {"00", "11"}
    assert abs(counts["00"] / total - 0.5) < 0.05
    assert abs(counts["11"] / total - 0.5) < 0.05

def test_sampling_respects_measure_subset():
    """If measure ops are present, only those qubits are reported."""
    circuit_desc = [
        {"name": "h", "qubits": [0]},
        {"name": "measure", "qubits": [0]},
    ]
    qc = QASMParser.parse(circuit_desc, 2)  # 2 qubits, only q0 measured
    counts = sim.sample(qc, shots=500, seed=7)
    assert set(counts.keys()) <= {"0", "1"}
    total = sum(counts.values())
    assert abs(counts.get("0", 0) / total - 0.5) < 0.08

def test_depolarizing_noise_mixes_distribution():
    """Depolarizing noise should move probabilities toward uniform."""
    qc = QASMParser.parse([{"name": "h", "qubits": [0]}], 1)
    counts = sim.sample(qc, shots=2000, seed=1, depol_prob=1.0)
    total = sum(counts.values())
    p0 = counts.get("0", 0) / total
    p1 = counts.get("1", 0) / total
    assert abs(p0 - 0.5) < 0.08
    assert abs(p1 - 0.5) < 0.08

def test_readout_noise_flips_bits():
    """Readout noise should introduce bit flips roughly at the specified rate."""
    qc = QASMParser.parse([{"name": "id", "qubits": [0]}], 1)
    counts = sim.sample(qc, shots=2000, seed=2, readout_error=0.2)
    total = sum(counts.values())
    p1 = counts.get("1", 0) / total
    assert 0.12 <= p1 <= 0.28

def test_measure_and_collapse_helper():
    """Measurement collapse should leave a single basis component."""
    state = (1/np.sqrt(2)) * np.array([1, 1], dtype=complex)
    outcome, collapsed = Simulator._measure_and_collapse(state, [0], 1, np.random.default_rng(0))
    assert outcome in ("0", "1")
    assert np.isclose(np.linalg.norm(collapsed), 1.0)
    assert np.count_nonzero(np.abs(collapsed) > 1e-9) == 1

def test_sample_with_collapse_runs():
    """Smoke test for collapse-based sampling respecting measurement ops."""
    circuit_desc = [
        {"name": "h", "qubits": [0]},
        {"name": "cx", "qubits": [0, 1]},
        {"name": "measure", "qubits": [0]},
        {"name": "cx", "qubits": [0, 1]},
    ]
    qc = QASMParser.parse(circuit_desc, 2)
    counts = sim.sample_with_collapse(qc, shots=500, seed=3)
    total = sum(counts.values())
    assert total == 500
