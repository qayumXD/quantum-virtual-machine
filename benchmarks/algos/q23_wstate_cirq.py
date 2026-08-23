# benchmarks/algos/q23_wstate_cirq.py
"""W-state on 3 qubits authored in Cirq (same recipe as the Qiskit variant,
with CRy manually decomposed into vocabulary rotations)."""
import math
import numpy as np
import cirq

from benchmarks.harness import sv_pipeline
from qvm.ir import QuantumCircuit

NAME = "wstate3_cirq"
FRAMEWORK = "cirq"
CATEGORY = "textbook"
EXCITED = [0b001, 0b010, 0b100]


def build():
    q0, q1, q2 = cirq.LineQubit.range(3)
    theta = 2 * math.acos(math.sqrt(2 / 3))
    half = math.pi / 2
    ops = [
        cirq.ry(theta)(q0),
        cirq.X(q0),
        # CRy(pi/2) control=q0 target=q1, decomposed
        cirq.ry(half / 2)(q1), cirq.CNOT(q0, q1), cirq.ry(-half / 2)(q1), cirq.CNOT(q0, q1),
        cirq.X(q0),
        # move the still-empty branch's excitation onto q2 via zero-flag Toffoli
        cirq.X(q0), cirq.X(q1),
        cirq.TOFFOLI(q0, q1, q2),
        cirq.X(q1), cirq.X(q0),
    ]
    native = cirq.Circuit(ops)
    return native, QuantumCircuit.from_cirq(native), None


def run_pipeline(qc, extra):
    return sv_pipeline(qc, extra)


def reference(native):
    p = np.zeros(8)
    for i in EXCITED:
        p[i] = 1 / 3
    return p


def validate(probs, qc, extra):
    for i in EXCITED:
        assert abs(probs[i] - 1 / 3) < 1e-9, f"|{i:03b}>={probs[i]:.6f}"
