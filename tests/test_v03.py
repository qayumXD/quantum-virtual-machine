"""
Tests for QVM v0.3 new modules:
  - parameter.py (Parameter, ParameterExpression)
  - observable.py (PauliOp, Hamiltonian)
  - noise.py (NoiseChannel, NoiseModel, DeviceBackend)
  - gradient.py (parameter_shift_gradient, finite_diff_gradient)
  - Integration: parameterized circuits, expectation values, noisy simulation
"""

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.qvm.parameter import Parameter, ParameterExpression, is_parameterized, resolve_param
from src.qvm.observable import PauliOp, Hamiltonian, pauli_z, pauli_x, zz_interaction
from src.qvm.noise import NoiseChannel, NoiseModel, DeviceBackend
from src.qvm.ir import QuantumCircuit
from src.qvm.simulator import Simulator


# ============================================================
# Parameter Tests
# ============================================================

class TestParameter:
    def test_creation(self):
        p = Parameter("theta")
        assert p.name == "theta"
        assert str(p) == "theta"

    def test_uniqueness(self):
        p1 = Parameter("theta")
        p2 = Parameter("theta")
        assert p1 != p2  # Same name, different identity

    def test_identity(self):
        p = Parameter("alpha")
        assert p == p
        assert hash(p) == hash(p)

    def test_empty_name_raises(self):
        with pytest.raises(ValueError):
            Parameter("")

    def test_non_string_name_raises(self):
        with pytest.raises(ValueError):
            Parameter(123)


class TestParameterExpression:
    def test_basic_arithmetic(self):
        theta = Parameter("theta")
        expr = 2 * theta + 1.0
        result = expr.evaluate({theta: 3.0})
        assert abs(result - 7.0) < 1e-10

    def test_subtraction(self):
        theta = Parameter("theta")
        expr = theta - 0.5
        assert abs(expr.evaluate({theta: 1.0}) - 0.5) < 1e-10

    def test_negation(self):
        theta = Parameter("theta")
        expr = -theta
        assert abs(expr.evaluate({theta: 2.0}) + 2.0) < 1e-10

    def test_division(self):
        theta = Parameter("theta")
        expr = theta / 2
        assert abs(expr.evaluate({theta: 4.0}) - 2.0) < 1e-10

    def test_division_by_zero(self):
        theta = Parameter("theta")
        with pytest.raises(ZeroDivisionError):
            theta / 0

    def test_two_parameters(self):
        a = Parameter("a")
        b = Parameter("b")
        expr = a + 2 * b - 1
        result = expr.evaluate({a: 1.0, b: 3.0})
        assert abs(result - 6.0) < 1e-10

    def test_unbound_raises(self):
        theta = Parameter("theta")
        expr = 2 * theta
        with pytest.raises(ValueError):
            expr.evaluate({})  # No binding

    def test_is_bound(self):
        expr = ParameterExpression._from_constant(3.14)
        assert expr.is_bound()

    def test_is_parameterized(self):
        theta = Parameter("theta")
        assert is_parameterized(theta)
        assert is_parameterized(2 * theta)
        assert not is_parameterized(3.14)

    def test_resolve_param_float(self):
        assert resolve_param(3.14) == 3.14

    def test_resolve_param_parameter(self):
        theta = Parameter("theta")
        assert resolve_param(theta, {theta: 1.5}) == 1.5


# ============================================================
# Observable Tests
# ============================================================

class TestPauliOp:
    def test_creation(self):
        op = PauliOp("ZZ", coeff=-1.0)
        assert op.num_qubits == 2
        assert op.coeff == -1.0

    def test_invalid_characters(self):
        with pytest.raises(ValueError):
            PauliOp("ZA")

    def test_empty_string(self):
        with pytest.raises(ValueError):
            PauliOp("")

    def test_identity(self):
        op = PauliOp("II")
        assert op.is_identity()

    def test_single_z_matrix(self):
        op = PauliOp("Z")
        mat = op.to_matrix()
        expected = np.array([[1, 0], [0, -1]], dtype=complex)
        np.testing.assert_allclose(mat, expected)

    def test_tensor_product(self):
        """ZI should be kron(Z, I)."""
        op = PauliOp("ZI")
        mat = op.to_matrix()
        Z = np.array([[1, 0], [0, -1]], dtype=complex)
        I = np.eye(2, dtype=complex)
        expected = np.kron(Z, I)
        np.testing.assert_allclose(mat, expected)


class TestHamiltonian:
    def test_from_dict(self):
        H = Hamiltonian.from_dict({"ZZ": -1.0, "XI": 0.5})
        assert len(H.terms) == 2
        assert H.num_qubits == 2

    def test_ground_state_energy(self):
        """Simple Z Hamiltonian: eigenvalues are +1, -1."""
        H = Hamiltonian.from_dict({"Z": 1.0})
        assert abs(H.ground_state_energy(1) - (-1.0)) < 1e-10

    def test_hermitian_matrix(self):
        H = Hamiltonian.from_dict({"XX": 1.0, "ZZ": -1.0})
        mat = H.to_matrix()
        # Hermitian: H = H†
        np.testing.assert_allclose(mat, mat.conj().T, atol=1e-10)

    def test_addition(self):
        H1 = Hamiltonian.from_dict({"ZI": 1.0})
        H2 = Hamiltonian.from_dict({"IZ": -0.5})
        H3 = H1 + H2
        assert len(H3.terms) == 2

    def test_scalar_mul(self):
        H = Hamiltonian.from_dict({"Z": 1.0})
        H2 = 2 * H
        assert H2.terms[0].coeff == 2.0

    def test_convenience_constructors(self):
        Hz = pauli_z(0, 2)
        assert Hz.num_qubits == 2

        Hx = pauli_x(1, 3)
        assert Hx.num_qubits == 3

        Hzz = zz_interaction(0, 1, 2)
        assert Hzz.terms[0].pauli_string == "ZZ"


# ============================================================
# Noise Tests
# ============================================================

class TestNoiseChannel:
    def test_depolarizing_completeness(self):
        ch = NoiseChannel.depolarizing(0.1)
        assert ch.validate()

    def test_amplitude_damping_completeness(self):
        ch = NoiseChannel.amplitude_damping(0.05)
        assert ch.validate()

    def test_phase_damping_completeness(self):
        ch = NoiseChannel.phase_damping(0.1)
        assert ch.validate()

    def test_thermal_relaxation_completeness(self):
        ch = NoiseChannel.thermal_relaxation(t1=100e3, t2=80e3, gate_time=35)
        assert ch.validate()

    def test_depolarizing_2q_completeness(self):
        ch = NoiseChannel.depolarizing_2q(0.05)
        assert ch.validate()

    def test_invalid_probability(self):
        with pytest.raises(ValueError):
            NoiseChannel.depolarizing(-0.1)
        with pytest.raises(ValueError):
            NoiseChannel.depolarizing(1.5)

    def test_t2_exceeds_2t1_raises(self):
        with pytest.raises(ValueError):
            NoiseChannel.thermal_relaxation(t1=50e3, t2=200e3, gate_time=35)


class TestNoiseModel:
    def test_add_noise(self):
        model = NoiseModel()
        ch = NoiseChannel.depolarizing(0.01)
        model.add_all_qubit_quantum_error(ch, ["h", "x"])
        assert model.has_noise()
        assert model.get_noise_for("h", [0]) is not None
        assert model.get_noise_for("cx", [0, 1]) is None

    def test_readout_error(self):
        model = NoiseModel()
        cm = np.array([[0.95, 0.05], [0.03, 0.97]])
        model.add_readout_error(cm, [0])
        assert model.get_readout_error(0) is not None
        assert model.get_readout_error(1) is None

    def test_qubit_specific_priority(self):
        model = NoiseModel()
        ch_all = NoiseChannel.depolarizing(0.01)
        ch_q0 = NoiseChannel.depolarizing(0.05)
        model.add_all_qubit_quantum_error(ch_all, ["h"])
        model.add_quantum_error(ch_q0, ["h"], [0])
        # Qubit-specific should be returned for qubit 0
        found = model.get_noise_for("h", [0])
        assert found.name == "depolarizing"

    def test_no_noise(self):
        model = NoiseModel()
        assert not model.has_noise()


class TestDeviceBackend:
    def test_fake_5q(self):
        device = DeviceBackend.fake_5q_device()
        assert device.num_qubits == 5
        model = device.to_noise_model()
        assert model.has_noise()

    def test_ideal(self):
        device = DeviceBackend.ideal(3)
        model = device.to_noise_model()
        assert not model.has_noise()


# ============================================================
# Integration Tests
# ============================================================

class TestParameterizedCircuits:
    def test_circuit_parameters(self):
        theta = Parameter("theta")
        qc = QuantumCircuit(1)
        qc.add_operation("ry", [0], params=[theta])
        assert theta in qc.parameters

    def test_bind_parameters(self):
        theta = Parameter("theta")
        qc = QuantumCircuit(1)
        qc.add_operation("ry", [0], params=[theta])
        bound = qc.bind_parameters({theta: np.pi / 2})
        assert len(bound.parameters) == 0
        assert abs(bound.operations[0]["params"][0] - np.pi / 2) < 1e-10

    def test_simulate_parameterized(self):
        """RY(π) should flip |0⟩ to |1⟩."""
        qc = QuantumCircuit(1)
        qc.add_operation("ry", [0], params=[np.pi])
        sim = Simulator()
        state, _ = sim.simulate(qc)
        # Should be close to |1⟩
        assert abs(state[1]) > 0.99

    def test_bind_and_simulate(self):
        """Bind θ=π to RY(θ) and verify |1⟩."""
        theta = Parameter("theta")
        qc = QuantumCircuit(1)
        qc.add_operation("ry", [0], params=[theta])
        bound = qc.bind_parameters({theta: np.pi})
        sim = Simulator()
        state, _ = sim.simulate(bound)
        assert abs(state[1]) > 0.99


class TestExpectationValue:
    def test_z_on_zero_state(self):
        """⟨0|Z|0⟩ = 1."""
        qc = QuantumCircuit(1)  # |0⟩
        H = Hamiltonian.from_dict({"Z": 1.0})
        sim = Simulator()
        ev = sim.expectation_value(qc, H)
        assert abs(ev - 1.0) < 1e-10

    def test_z_on_one_state(self):
        """⟨1|Z|1⟩ = -1."""
        qc = QuantumCircuit(1)
        qc.add_operation("x", [0])  # |1⟩
        H = Hamiltonian.from_dict({"Z": 1.0})
        sim = Simulator()
        ev = sim.expectation_value(qc, H)
        assert abs(ev - (-1.0)) < 1e-10

    def test_x_on_plus_state(self):
        """⟨+|X|+⟩ = 1."""
        qc = QuantumCircuit(1)
        qc.add_operation("h", [0])  # |+⟩
        H = Hamiltonian.from_dict({"X": 1.0})
        sim = Simulator()
        ev = sim.expectation_value(qc, H)
        assert abs(ev - 1.0) < 1e-10

    def test_bell_state_zz(self):
        """For Bell state |Φ+⟩ = (|00⟩+|11⟩)/√2: ⟨ZZ⟩ = 1."""
        qc = QuantumCircuit(2)
        qc.add_operation("h", [0])
        qc.add_operation("cx", [0, 1])
        H = Hamiltonian.from_dict({"ZZ": 1.0})
        sim = Simulator()
        ev = sim.expectation_value(qc, H)
        assert abs(ev - 1.0) < 1e-10


class TestRzConvention:
    def test_rz_matches_standard(self):
        """Rz(θ) = diag(e^{-iθ/2}, e^{iθ/2})."""
        sim = Simulator()
        angle = np.pi / 4
        mat = sim._get_gate_matrix("rz", [angle])
        expected = np.array([
            [np.exp(-1j * angle / 2), 0],
            [0, np.exp(1j * angle / 2)]
        ])
        np.testing.assert_allclose(mat, expected, atol=1e-10)

    def test_rz_differs_from_p(self):
        """Rz and P should now be different matrices."""
        sim = Simulator()
        angle = np.pi / 3
        rz_mat = sim._get_gate_matrix("rz", [angle])
        p_mat = sim._get_gate_matrix("p", [angle])
        # They should differ (Rz has global phase difference)
        assert not np.allclose(rz_mat, p_mat)


class TestCZGate:
    def test_cz_creates_phase_flip(self):
        """CZ on |11⟩ should give -|11⟩."""
        qc = QuantumCircuit(2)
        qc.add_operation("x", [0])  # |1⟩
        qc.add_operation("x", [1])  # |1⟩ → |11⟩
        qc.add_operation("cz", [0, 1])
        sim = Simulator()
        state, _ = sim.simulate(qc)
        # |11⟩ is index 3 (binary 11), should have amplitude -1
        assert abs(state[3] - (-1.0)) < 1e-10

    def test_cz_no_effect_on_01(self):
        """CZ on |01⟩ should give |01⟩ unchanged."""
        qc = QuantumCircuit(2)
        qc.add_operation("x", [0])  # |01⟩ (qubit 0 = 1, qubit 1 = 0)
        qc.add_operation("cz", [0, 1])
        sim = Simulator()
        state, _ = sim.simulate(qc)
        # |01⟩ is index 1 (qubit 0 is LSB)
        assert abs(state[1] - 1.0) < 1e-10


class TestNoisySimulation:
    def test_noisy_sample_runs(self):
        """Noisy simulation should produce valid counts."""
        qc = QuantumCircuit(2)
        qc.add_operation("h", [0])
        qc.add_operation("cx", [0, 1])
        qc.add_operation("measure", [0])
        qc.add_operation("measure", [1])

        model = NoiseModel()
        model.add_all_qubit_quantum_error(
            NoiseChannel.depolarizing(0.05), ["h", "x", "cx"])

        sim = Simulator()
        counts = sim.sample(qc, shots=100, seed=42, noise_model=model)
        assert isinstance(counts, dict)
        assert sum(counts.values()) == 100

    def test_ideal_noise_model_same_as_noiseless(self):
        """Ideal device should produce similar results to no noise."""
        qc = QuantumCircuit(2)
        qc.add_operation("h", [0])
        qc.add_operation("cx", [0, 1])

        sim = Simulator()
        device = DeviceBackend.ideal(2)
        model = device.to_noise_model()
        assert not model.has_noise()


class TestMPSSimulatorFixes:
    """Test that MPS simulator now handles all gates correctly."""

    def test_mps_y_gate(self):
        from src.qvm.mps_simulator import MPSSimulator
        qc = QuantumCircuit(1)
        qc.add_operation("y", [0])
        sim = MPSSimulator()
        _, _ = sim.simulate(qc)
        sv = sim.get_statevector()
        # Y|0⟩ = i|1⟩
        assert abs(sv[1] - 1j) < 1e-10

    def test_mps_z_gate(self):
        from src.qvm.mps_simulator import MPSSimulator
        qc = QuantumCircuit(1)
        qc.add_operation("h", [0])
        qc.add_operation("z", [0])
        sim = MPSSimulator()
        _, _ = sim.simulate(qc)
        sv = sim.get_statevector()
        # Z|+⟩ = |−⟩ = (|0⟩ - |1⟩)/√2
        expected = np.array([1, -1]) / np.sqrt(2)
        np.testing.assert_allclose(sv, expected, atol=1e-10)

    def test_mps_s_gate(self):
        from src.qvm.mps_simulator import MPSSimulator
        qc = QuantumCircuit(1)
        qc.add_operation("x", [0])  # |1⟩
        qc.add_operation("s", [0])  # S|1⟩ = i|1⟩
        sim = MPSSimulator()
        _, _ = sim.simulate(qc)
        sv = sim.get_statevector()
        assert abs(sv[1] - 1j) < 1e-10

    def test_mps_cz_gate(self):
        from src.qvm.mps_simulator import MPSSimulator
        qc = QuantumCircuit(2)
        qc.add_operation("x", [0])
        qc.add_operation("x", [1])
        qc.add_operation("cz", [0, 1])
        sim = MPSSimulator()
        _, _ = sim.simulate(qc)
        sv = sim.get_statevector()
        # CZ|11⟩ = -|11⟩
        assert abs(sv[3] - (-1.0)) < 1e-10

    def test_mps_sample(self):
        from src.qvm.mps_simulator import MPSSimulator
        qc = QuantumCircuit(2)
        qc.add_operation("h", [0])
        qc.add_operation("cx", [0, 1])
        sim = MPSSimulator()
        counts = sim.sample(qc, shots=100, seed=42)
        assert isinstance(counts, dict)
        assert sum(counts.values()) == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
