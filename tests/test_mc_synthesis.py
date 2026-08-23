# tests/test_mc_synthesis.py
"""Exactness guarantees for multi-controlled gate synthesis and their
integration through IR macros, auto-lowering, import, and export."""
import math

import numpy as np
import pytest

try:
    import qiskit
    from qiskit import QuantumCircuit as QK
    from qiskit.quantum_info import Operator, Statevector as QKStatevector
except ImportError:
    qiskit = None

from qvm import synthesis
from qvm.ir import QuantumCircuit
from qvm.simulator import Simulator
from qvm.exceptions import UnsupportedGateError, QVMConversionError

needs_qiskit = pytest.mark.skipif(qiskit is None, reason="Qiskit not installed")


def _ops_to_qvm_circuit(ops, num_qubits):
    qc = QuantumCircuit(num_qubits)
    for o in ops:
        qc.add_operation(o["name"], list(o["qubits"]),
                         params=list(o["params"]) or None)
    return qc


def _qvm_probs(qc):
    state, _ = Simulator().simulate(qc)
    return np.abs(state) ** 2


def _qk_probs(qk):
    return np.asarray(QKStatevector.from_instruction(qk).probabilities(), float)


# ---------------------------------------------------------------------------
# Exact unitary equivalence against Qiskit's reference implementations
# ---------------------------------------------------------------------------

@needs_qiskit
@pytest.mark.parametrize("k", [1, 2, 3, 4])
@pytest.mark.parametrize("kind,lam", [("mcp", 0.7 * math.pi), ("mcz", None)])
def test_mcp_family_exact(k, kind, lam):
    angle = math.pi if lam is None else lam
    ref = QK(k + 1)
    if kind == "mcz":
        ref.h(k); ref.mcx(list(range(k)), k); ref.h(k)
    else:
        ref.mcp(angle, list(range(k)), k)
    expected = Operator(ref).data

    ops = synthesis.lower_macro(kind, list(range(k + 1)),
                                [] if lam is None else [angle])
    got = Operator(_ops_to_qvm_circuit(ops, k + 1).to_qiskit()).data
    assert np.allclose(got, expected, atol=1e-9), f"{kind} k={k} inexact"


@needs_qiskit
@pytest.mark.parametrize("k", [1, 2, 3, 4])
@pytest.mark.parametrize("kind,theta", [("mcry", 0.9), ("mcrz", -1.3), ("mcrx", 0.4)])
def test_mc_rotation_exact(k, kind, theta):
    ref = QK(k + 1)
    getattr(ref, kind)(theta, list(range(k)), k)
    expected = Operator(ref).data

    ops = synthesis.lower_macro(kind, list(range(k + 1)), [theta])
    got = Operator(_ops_to_qvm_circuit(ops, k + 1).to_qiskit()).data
    assert np.allclose(got, expected, atol=1e-9)


# ---------------------------------------------------------------------------
# IR integration: macros accepted at construction, lowered by engines
# ---------------------------------------------------------------------------

def test_ir_accepts_macros_and_validates():
    qc = QuantumCircuit(5)
    qc.add_operation("mcx", [0, 1, 2], params=[], target=None) if False else \
        qc.add_operation("mcx", [0, 1, 2, 4])
    qc.add_operation("mcphase", [1, 2, 3, 4], params=[0.5])   # alias -> mcp
    names = {op["name"] for op in qc.operations}
    assert "mcx" in names and "mcp" in names                  # canonicalized

    with pytest.raises(ValueError, match="distinct"):
        QuantumCircuit(3).add_operation("mcx", [0, 1, 1])
    with pytest.raises(ValueError, match="at least one control"):
        QuantumCircuit(3).add_operation("mcz", [2])


def test_simulator_auto_lowers_macros():
    # GHZ-4 built through a single 3-control mcx
    qc = QuantumCircuit(4)
    qc.add_operation("h", [0])
    qc.add_operation("cx", [0, 1])
    qc.add_operation("cx", [1, 2])
    qc.add_operation("mcx", [0, 1, 2, 3])   # flips q3 on the |111> branch
    p = _qvm_probs(qc)
    assert abs(p[0] - .5) < 1e-9 and abs(p[-1] - .5) < 1e-9, p[[0, -1]]


def test_lowered_is_noop_without_macros():
    qc = QuantumCircuit(2)
    qc.add_operation("h", [0]); qc.add_operation("cx", [0, 1])
    assert qc.lowered() is qc


def test_symbolic_macro_requires_binding():
    theta = __import__("qvm.parameter", fromlist=["Parameter"]).Parameter("theta")
    qc = QuantumCircuit(3)
    qc.add_operation("mcry", [0, 1, 2], params=[theta])
    with pytest.raises(QVMConversionError, match="Bind symbolic"):
        qc.lowered()


# ---------------------------------------------------------------------------
# Import / export integration
# ---------------------------------------------------------------------------

@needs_qiskit
def test_from_qiskit_lowers_mc_gates():
    qk = QK(4)
    qk.h(0)
    qk.mcx([0, 1, 2], 3)                     # 3-control X
    qk.mcp(0.8, [0, 1, 2], 3)
    qc = QuantumCircuit.from_qiskit(qk)
    macro_names = {"mcx", "mcz", "mcp", "mcry", "mcrz"}
    assert not any(op["name"] in macro_names for op in qc.operations), \
        "importer must emit lowered vocabulary, not macros"
    assert np.allclose(_qvm_probs(qc), _qk_probs(qk), atol=1e-9)


@needs_qiskit
def test_transpile_foreign_kwarg():
    qk = QK(2)
    qk.swap(0, 1)                             # in-vocab control case first
    ok_circuit = QuantumCircuit.from_qiskit(qk)
    assert len(ok_circuit.operations) == 1

    qk2 = QK(2)
    from qiskit.circuit.library import UnitaryGate
    qk2.append(UnitaryGate(np.array([[1, 0], [0, -1]])), [0])   # foreign 'unitary'
    with pytest.raises(UnsupportedGateError):
        QuantumCircuit.from_qiskit(qk2)
    lowered = QuantumCircuit.from_qiskit(qk2, transpile_foreign=True)
    assert np.allclose(_qvm_probs(lowered), _qk_probs(qk2), atol=1e-9)


@needs_qiskit
def test_export_macro_to_qiskit_roundtrip():
    qc = QuantumCircuit(4)
    qc.add_operation("h", [0])
    qc.add_operation("mcx", [0, 1, 2, 3])
    qk = qc.to_qiskit()
    assert any(inst.operation.name == "mcx" for inst in qk.data)
    assert np.allclose(_qvm_probs(qc), _qk_probs(qk), atol=1e-9)
