# benchmarks/algos/q20_bell_cirq.py
"""Bell pair authored in Cirq."""
import numpy as np
import cirq

from benchmarks.harness import sv_pipeline
from qvm.ir import QuantumCircuit

NAME = "bell_cirq"
FRAMEWORK = "cirq"
CATEGORY = "small"


def build():
    q0, q1 = cirq.LineQubit.range(2)
    native = cirq.Circuit(cirq.H(q0), cirq.CNOT(q0, q1))
    return native, QuantumCircuit.from_cirq(native), None


def run_pipeline(qc, extra):
    return sv_pipeline(qc, extra)


def reference(native):
    p = np.zeros(4)
    p[0] = p[3] = 0.5
    return p


def validate(probs, qc, extra):
    assert abs(probs[0] - .5) < 1e-9 and abs(probs[3] - .5) < 1e-9
