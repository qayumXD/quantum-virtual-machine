# tests/test_interop_roundtrip.py
"""Foolproof interop guarantees:

1. No silent drops: every supported gate survives conversion; unsupported
   operations raise UnsupportedGateError instead of vanishing.
2. Physical equivalence: converted circuits produce the same measurement
   probability distributions as the QVM simulator (Qiskit and Cirq agree).
3. Round trips preserve circuit structure.
4. Parameterized circuits convert symbolically in both directions.

Run: pytest tests/test_interop_roundtrip.py -v
"""
import math

import numpy as np
import pytest

try:
    import qiskit
    from qiskit.quantum_info import Statevector as QKStatevector
except ImportError:
    qiskit = None

try:
    import cirq
except ImportError:
    cirq = None

from qvm.ir import QuantumCircuit
from qvm.parameter import Parameter, ParameterExpression
from qvm.simulator import Simulator
from qvm.exceptions import (
    UnsupportedGateError,
    QVMConversionError,
    QVMResourceLimitError,
)

needs_qiskit = pytest.mark.skipif(qiskit is None, reason="Qiskit not installed")
needs_cirq = pytest.mark.skipif(cirq is None, reason="Cirq not installed")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def build_full_gate_circuit() -> QuantumCircuit:
    """Exercise the entire canonical gate vocabulary on 3 qubits."""
    qc = QuantumCircuit(3)
    # paramless 1q
    qc.add_operation("h", [0])
    qc.add_operation("x", [1])
    qc.add_operation("y", [2])
    qc.add_operation("z", [0])
    qc.add_operation("s", [1])
    qc.add_operation("sdg", [1])
    qc.add_operation("t", [2])
    qc.add_operation("tdg", [2])
    qc.add_operation("sx", [0])
    qc.add_operation("sxdg", [0])
    qc.add_operation("id", [1])
    # parameterized 1q (irregular angles to catch convention errors)
    qc.add_operation("rx", [0], params=[0.3])
    qc.add_operation("ry", [1], params=[-0.7])
    qc.add_operation("rz", [2], params=[1.1])
    qc.add_operation("p", [0], params=[0.9])
    # 2q
    qc.add_operation("cx", [0, 1])
    qc.add_operation("cz", [1, 2])
    qc.add_operation("swap", [0, 2])
    # parameterized 2q
    qc.add_operation("rxx", [0, 1], params=[0.4])
    qc.add_operation("rzz", [1, 2], params=[-0.5])
    qc.add_operation("cp", [0, 2], params=[1.3])
    # 3q
    qc.add_operation("ccx", [0, 1, 2])
    return qc


def qvm_probs(qc: QuantumCircuit) -> np.ndarray:
    state, _ = Simulator().simulate(qc)
    return np.abs(state) ** 2


def qiskit_probs(qk) -> np.ndarray:
    return np.asarray(QKStatevector.from_instruction(qk).probabilities())


def cirq_probs(cr, num_qubits: int) -> np.ndarray:
    """Convert a Cirq statevector to QVM/Qiskit little-endian ordering.

    Cirq orders amplitudes with the first qubit in ``qubit_order`` as the
    most significant bit; QVM/Qiskit treat qubit 0 as the least significant
    bit.  The mapping is a bit-reversal permutation of the indices (not a
    simple array flip).
    """
    sim = cirq.Simulator(dtype=np.complex128)
    vec = sim.simulate(
        cr, qubit_order=cirq.LineQubit.range(num_qubits)
    ).final_state_vector
    probs = np.abs(vec) ** 2
    idx = np.arange(probs.size)
    rev = np.zeros(idx.size, dtype=int)
    for q in range(num_qubits):
        rev |= ((idx >> q) & 1) << (num_qubits - 1 - q)
    return probs[rev]


def assert_probabilities_close(p1, p2, tol=1e-8):
    assert len(p1) == len(p2), f"state dimension mismatch: {len(p1)} vs {len(p2)}"
    assert np.allclose(p1, p2, atol=tol), (
        f"probability distributions diverge:\n  p1={np.round(p1, 8)}\n  p2={np.round(p2, 8)}"
    )


def op_signature(qc: QuantumCircuit):
    """Comparable structural signature of a circuit's gate list."""
    sig = []
    for op in qc.operations:
        if op["name"] in ("measure", "barrier"):
            continue
        params = tuple(
            float(p) if isinstance(p, (int, float))
            else getattr(p, "name", str(p))
            for p in op.get("params") or []
        )
        sig.append((op["name"], tuple(op["qubits"]), params))
    return sorted(sig)


# ---------------------------------------------------------------------------
# 1. Triple-engine equivalence over the full gate vocabulary
# ---------------------------------------------------------------------------

@needs_qiskit
def test_full_gate_set_matches_qiskit():
    qc = build_full_gate_circuit()
    assert_probabilities_close(qvm_probs(qc), qiskit_probs(qc.to_qiskit()))


@needs_cirq
def test_full_gate_set_matches_cirq():
    qc = build_full_gate_circuit()
    assert_probabilities_close(qvm_probs(qc), cirq_probs(qc.to_cirq(), qc.num_qubits))


@needs_qiskit
@needs_cirq
def test_qiskit_and_cirq_agree_with_each_other():
    """The IR pivot produces mutually consistent exports."""
    qc = build_full_gate_circuit()
    assert_probabilities_close(
        qiskit_probs(qc.to_qiskit()), cirq_probs(qc.to_cirq(), qc.num_qubits)
    )


# ---------------------------------------------------------------------------
# 2. New simulator kernels (rxx / rzz / cp) validated against frameworks
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("gate,matrix_gate", [("rxx", "rxx"), ("rzz", "rzz"), ("cp", "cp")])
@needs_qiskit
def test_two_qubit_rotation_kernels_match_qiskit(gate, matrix_gate):
    for angle in (0.0, 0.25, -1.7, math.pi / 2):
        qc = QuantumCircuit(2)
        qc.add_operation("ry", [0], params=[0.6])       # non-trivial input state
        qc.add_operation("ry", [1], params=[-0.2])
        qc.add_operation(gate, [0, 1], params=[angle])
        assert_probabilities_close(qvm_probs(qc), qiskit_probs(qc.to_qiskit()))


# ---------------------------------------------------------------------------
# 3. No silent drops — regression tests for the original bug
# ---------------------------------------------------------------------------

@needs_qiskit
def test_to_qiskit_preserves_every_gate():
    qc = build_full_gate_circuit()
    qk = qc.to_qiskit()
    exported_names = [inst.operation.name.lower() for inst in qk.data]
    assert len(exported_names) == len(qc.operations), "operations were dropped!"
    for name in ("t", "swap", "cz", "ry", "sx", "ccx", "rzz", "cp", "rxx"):
        assert name in exported_names, f"gate '{name}' silently dropped"


@needs_cirq
def test_to_cirq_preserves_every_gate():
    qc = build_full_gate_circuit()
    cr = qc.to_cirq()
    exported_ops = list(cr.all_operations())
    assert len(exported_ops) == len(qc.operations), "operations were dropped!"


@needs_qiskit
def test_roundtrip_qvm_to_qiskit_and_back_structure():
    qc = build_full_gate_circuit()
    back = QuantumCircuit.from_qiskit(qc.to_qiskit())
    assert op_signature(back) == op_signature(qc)


@needs_cirq
def test_roundtrip_qvm_to_cirq_and_back_structure():
    qc = QuantumCircuit(3)
    qc.add_operation("h", [0])
    qc.add_operation("x", [1])
    qc.add_operation("s", [1])
    qc.add_operation("sdg", [1])
    qc.add_operation("t", [2])
    qc.add_operation("tdg", [2])
    qc.add_operation("sx", [0])
    qc.add_operation("sxdg", [0])
    qc.add_operation("rx", [0], params=[0.3])
    qc.add_operation("rz", [2], params=[1.1])
    qc.add_operation("cx", [0, 1])
    qc.add_operation("cz", [1, 2])
    qc.add_operation("swap", [0, 2])
    qc.add_operation("rzz", [1, 2], params=[-0.5])
    qc.add_operation("ccx", [0, 1, 2])
    back = QuantumCircuit.from_cirq(qc.to_cirq())
    assert op_signature(back) == op_signature(qc)


# ---------------------------------------------------------------------------
# 4. Explicit failures instead of silent corruption
# ---------------------------------------------------------------------------

def test_export_control_flow_raises():
    qc = QuantumCircuit(1)
    qc.add_operation("label", [], label="loop_start")
    with pytest.raises(UnsupportedGateError):
        qc.to_qiskit()
    with pytest.raises(UnsupportedGateError):
        qc.to_cirq()


def test_add_operation_rejects_unknown_gate():
    qc = QuantumCircuit(1)
    with pytest.raises(UnsupportedGateError):
        qc.add_operation("fancy_gate", [0])


def test_add_operation_enforces_arity():
    qc = QuantumCircuit(2)
    with pytest.raises(ValueError, match="acts on 2 qubit"):
        qc.add_operation("cx", [0])
    with pytest.raises(ValueError, match="distinct qubits"):
        qc.add_operation("cx", [0, 0])
    with pytest.raises(ValueError, match="acts on 1 qubit"):
        qc.add_operation("h", [0, 1])


@needs_qiskit
def test_import_unknown_qiskit_gate_raises():
    from qiskit.circuit.library import UnitaryGate
    qk = qiskit.QuantumCircuit(1)
    qk.append(UnitaryGate(np.array([[0, 1j], [-1j, 0]])), [0])
    with pytest.raises(UnsupportedGateError, match="unitary"):
        QuantumCircuit.from_qiskit(qk)


@needs_cirq
def test_import_exotic_cirq_gate_raises():
    cr = cirq.Circuit(cirq.ISWAP(cirq.LineQubit(0), cirq.LineQubit(1)))
    with pytest.raises(UnsupportedGateError):
        QuantumCircuit.from_cirq(cr)


@needs_cirq
def test_empty_cirq_circuit_does_not_crash():
    back = QuantumCircuit.from_cirq(cirq.Circuit())
    assert back.num_qubits == 1
    assert back.operations == []


# ---------------------------------------------------------------------------
# 5. Measurement fidelity
# ---------------------------------------------------------------------------

@needs_cirq
def test_measure_key_roundtrip_through_cirq():
    qc = QuantumCircuit(2)
    qc.add_classical_register("m", 2)
    qc.add_operation("h", [0])
    qc.add_operation("measure", [0], target_bit=("m", 0))
    qc.add_operation("measure", [1], target_bit=("m", 1))
    back = QuantumCircuit.from_cirq(qc.to_cirq())
    targets = sorted(op["target_bit"] for op in back.operations if op["name"] == "measure")
    assert targets == [("m", 0), ("m", 1)]


def test_parse_measure_key_formats():
    parse = QuantumCircuit._parse_measure_key
    assert parse("c[3]") == ("c", 3)
    assert parse("m[12]") == ("m", 12)
    assert parse("('c', 0)") == ("c", 0)          # legacy tuple-string
    assert parse("5") == ("c", 5)                  # bare index


@needs_qiskit
def test_bell_state_via_aer_counts():
    qc = QuantumCircuit(2)
    qc.add_classical_register("c", 2)
    qc.add_operation("h", [0])
    qc.add_operation("cx", [0, 1])
    qc.add_operation("measure", [0], target_bit=("c", 0))
    qc.add_operation("measure", [1], target_bit=("c", 1))
    counts = qc.run_qiskit_simulator(shots=512)
    total = sum(counts.values())
    assert total == 512
    parity_even = counts.get("00", 0) + counts.get("11", 0)
    assert parity_even == 512, "Bell state must only yield even-parity outcomes"


# ---------------------------------------------------------------------------
# 6. Parameterized circuits
# ---------------------------------------------------------------------------

@needs_qiskit
def test_symbolic_export_to_qiskit():
    theta = Parameter("theta")
    qc = QuantumCircuit(1)
    qc.add_operation("ry", [0], params=[theta])
    qk = qc.to_qiskit()
    qk_params = list(qk.parameters)
    assert len(qk_params) == 1 and qk_params[0].name == "theta"


@needs_qiskit
def test_unbound_expression_export_raises_clearly():
    theta = Parameter("theta")
    qc = QuantumCircuit(1)
    qc.add_operation("ry", [0], params=[2 * theta + 0.5])
    with pytest.raises(QVMConversionError, match="bind_parameters"):
        qc.to_qiskit()


@needs_qiskit
def test_import_parameterized_qiskit_circuit():
    beta = qiskit.circuit.Parameter("beta")
    qk = qiskit.QuantumCircuit(1)
    qk.ry(beta, 0)
    qk.rz(0.4, 0)
    qc = QuantumCircuit.from_qiskit(qk)
    free = qc.parameters
    assert len(free) == 1
    bound = qc.bind_parameters({next(iter(free)): math.pi})
    probs = qvm_probs(bound)
    assert abs(probs[-1] - 1.0) < 1e-9           # ry(pi)|0> = |1>


@needs_cirq
def test_import_symbolic_cirq_circuit():
    import sympy
    gamma = sympy.Symbol("gamma")
    cr = cirq.Circuit(cirq.rx(gamma).on(cirq.LineQubit(0)))
    qc = QuantumCircuit.from_cirq(cr)
    free = qc.parameters
    assert len(free) == 1 and next(iter(free)).name == "gamma"
    bound = qc.bind_parameters({next(iter(free)): 0.123})
    assert_probabilities_close(qvm_probs(bound), qvm_probs(_numeric_rx_circuit(0.123)))


def _numeric_rx_circuit(angle: float) -> QuantumCircuit:
    qc = QuantumCircuit(1)
    qc.add_operation("rx", [0], params=[angle])
    return qc


@needs_qiskit
def test_resource_limit_raises_domain_exception():
    qc = QuantumCircuit(1)
    qc.add_operation("label", [], label="top")
    qc.add_operation("jump", [], jump_to="top")   # infinite loop
    with pytest.raises(QVMResourceLimitError):
        Simulator().simulate(qc, max_ops=100)


# ---------------------------------------------------------------------------
# 7. Cross-framework bridge (cirq ↔ qiskit through the IR pivot)
# ---------------------------------------------------------------------------

@needs_qiskit
@needs_cirq
def test_cirq_to_qiskit_bridge_equivalence():
    cr = cirq.Circuit(
        cirq.X(cirq.LineQubit(0)),
        cirq.CNOT(cirq.LineQubit(0), cirq.LineQubit(1)),
        cirq.ry(0.8).on(cirq.LineQubit(2)),
    )
    qk = QuantumCircuit.cirq_to_qiskit(cr)
    assert_probabilities_close(qiskit_probs(qk), cirq_probs(cr, 3))


@needs_qiskit
@needs_cirq
def test_qiskit_to_cirq_bridge_equivalence():
    qk = qiskit.QuantumCircuit(2)
    qk.h(0)
    qk.cx(0, 1)
    qk.rz(0.4, 1)
    cr = QuantumCircuit.qiskit_to_cirq(qk)
    assert_probabilities_close(cirq_probs(cr, 2), qiskit_probs(qk))


# ---------------------------------------------------------------------------
# 8. Barrier handling
# ---------------------------------------------------------------------------

@needs_qiskit
def test_barrier_survives_qiskit_roundtrip():
    qc = QuantumCircuit(2)
    qc.add_operation("h", [0])
    qc.add_operation("barrier", [0, 1])
    qc.add_operation("cx", [0, 1])
    qk = qc.to_qiskit()
    assert any(inst.operation.name == "barrier" for inst in qk.data)
    back = QuantumCircuit.from_qiskit(qk)
    assert any(op["name"] == "barrier" for op in back.operations)
    assert_probabilities_close(qvm_probs(back), qvm_probs(qc))
