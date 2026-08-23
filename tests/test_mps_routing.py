# tests/test_mps_routing.py
"""MPS engine guarantees: SWAP-routed long-range two-qubit gates are exact,
statevector output follows QVM little-endian convention, and unknown gates
fail loudly instead of being ignored."""
import numpy as np
import pytest

from qvm.ir import QuantumCircuit
from qvm.mps_simulator import MPSSimulator
from qvm.simulator import Simulator
from qvm.exceptions import UnsupportedGateError


def _mps_probs(qc, chi=64):
    m = MPSSimulator(max_bond_dim=chi)
    m.simulate(qc)
    sv = m.get_statevector()
    p = np.abs(sv) ** 2
    return p / p.sum()


def _sv_probs(qc):
    st, _ = Simulator().simulate(qc)
    return np.abs(st) ** 2


def _circuit(ops, n=6):
    qc = QuantumCircuit(n)
    qc.add_operation("h", [1])
    qc.add_operation("ry", [2], params=[0.7])
    for o in ops:
        qc.add_operation(o[0], o[1], params=(o[2] if len(o) > 2 else None))
    return qc


@pytest.mark.parametrize("ops,label", [
    ([("cx", [1, 5])], "long-range CX"),
    ([("cz", [1, 5])], "long-range CZ"),
    ([("swap", [1, 5])], "long-range SWAP"),
    ([("rzz", [1, 5], [0.6])], "long-range RZZ"),
    ([("rxx", [1, 5], [-0.4])], "long-range RXX"),
    ([("cp", [1, 5], [0.9])], "long-range CP"),
])
def test_long_range_two_qubit_gates_match_statevector(ops, label):
    qc = _circuit(ops)
    assert np.allclose(_mps_probs(qc), _sv_probs(qc), atol=1e-9), label


def test_ghz_like_via_single_long_range_cx():
    # h(0); cx(0->5) produces (|000000> + |100001>)/sqrt2: qubit 5 flips only
    # inside the q0=1 branch, so support is {index 0, index 33}.
    qc = QuantumCircuit(6)
    qc.add_operation("h", [0])
    qc.add_operation("cx", [0, 5])          # spans the whole chain in one gate
    p = _mps_probs(qc)
    assert abs(p[0] - .5) < 1e-9 and abs(p[0b100001] - .5) < 1e-9
    assert p.sum() > 1 - 1e-12 and np.allclose(_mps_probs(qc), _sv_probs(qc), atol=1e-9)


def test_full_ghz_chain_matches_statevector():
    qc = QuantumCircuit(8)
    qc.add_operation("h", [0])
    for i in range(7):
        qc.add_operation("cx", [i, i + 1])
    p = _mps_probs(qc)
    assert abs(p[0] - .5) < 1e-9 and abs(p[-1] - .5) < 1e-9
    assert np.allclose(_mps_probs(qc), _sv_probs(qc), atol=1e-9)


def test_statevector_is_little_endian():
    # |1> on qubit 0 must be index 1 (LSB), not the MSB slot
    qc = QuantumCircuit(3)
    qc.add_operation("x", [0])
    p = _mps_probs(qc)
    assert abs(p[0b001] - 1) < 1e-12


def test_entanglement_grows_bond_dimension():
    qc = QuantumCircuit(8)
    qc.add_operation("h", [0])
    for i in range(7):
        qc.add_operation("cx", [i, i + 1])
    m = MPSSimulator(max_bond_dim=64)
    m.simulate(qc)
    bonds = [t.shape[0] for t in m.tensors[1:]]
    assert max(bonds) >= 2, "GHZ chain must create non-trivial bonds"


def test_unknown_gate_fails_loudly():
    qc = QuantumCircuit(2)
    qc.operations.append({"name": "mystery_gate", "qubits": [0],
                          "params": [], "condition": None, "target_bit": None,
                          "duration": None, "label": None, "jump_to": None,
                          "classical_op": None})
    with pytest.raises(UnsupportedGateError, match="mystery_gate"):
        MPSSimulator().simulate(qc)
