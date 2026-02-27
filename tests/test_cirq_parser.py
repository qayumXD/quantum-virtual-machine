import math
import pytest

try:
    import cirq
    CIRQ_AVAILABLE = True
except ImportError:  # pragma: no cover
    CIRQ_AVAILABLE = False

from src.parser import CirqParser
from src.ir import QuantumCircuitIR


pytestmark = pytest.mark.skipif(not CIRQ_AVAILABLE, reason="Cirq not installed")


def test_basic_gates():
    q0, q1 = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(
        cirq.H(q0),
        cirq.CNOT(q0, q1),
        cirq.Z(q1),
    )
    ir = CirqParser().parse(circuit)
    assert isinstance(ir, QuantumCircuitIR)
    assert ir.num_qubits == 2
    assert [g.gate_type for g in ir.gates] == ["H", "CX", "Z"]
    assert [g.qubits for g in ir.gates] == [[0], [0, 1], [1]]


def test_rotations_and_params():
    q0 = cirq.LineQubit(0)
    angle = math.pi / 3
    circuit = cirq.Circuit(cirq.rx(angle)(q0), cirq.rz(angle / 2)(q0))
    ir = CirqParser().parse(circuit)
    assert len(ir.gates) == 2
    assert ir.gates[0].gate_type == "RX"
    assert pytest.approx(ir.gates[0].params[0]) == angle
    assert ir.gates[1].gate_type == "RZ"
    assert pytest.approx(ir.gates[1].params[0]) == angle / 2


def test_swap_and_measure():
    q0, q1 = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(cirq.SWAP(q0, q1), cirq.measure(q1, q0, key="m"))
    ir = CirqParser().parse(circuit)
    # Gates
    assert ir.gates[0].gate_type == "SWAP"
    # Measurements produce one entry per measured qubit in encounter order
    assert ir.measurements == [
        {"qubit": 1, "classical_bit": 0},
        {"qubit": 0, "classical_bit": 1},
    ]
