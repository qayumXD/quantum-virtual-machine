# benchmarks/algos/q22_qft_roundtrip_cirq.py
"""QFT + inverse QFT on |100> authored in Cirq."""
import math
import numpy as np
import cirq

from benchmarks.harness import sv_pipeline
from qvm.ir import QuantumCircuit

NAME = "qft_roundtrip_cirq"
FRAMEWORK = "cirq"
CATEGORY = "textbook"
INPUT = 0b100
N = 3


def build():
    qs = cirq.LineQubit.range(N)
    ops = [cirq.X(qs[2])]
    for k in range(N):
        ops.append(cirq.H(qs[k]))
        for m in range(k + 1, N):
            ops.append(cirq.CZPowGate(exponent=1 / (2 ** (m - k)))(qs[m], qs[k]))
    for i in range(N // 2):
        ops.append(cirq.SWAP(qs[i], qs[N - 1 - i]))
    for i in range(N // 2):
        ops.append(cirq.SWAP(qs[i], qs[N - 1 - i]))
    for k in reversed(range(N)):
        for m in reversed(range(k + 1, N)):
            ops.append(cirq.CZPowGate(exponent=-1 / (2 ** (m - k)))(qs[m], qs[k]))
        ops.append(cirq.H(qs[k]))
    native = cirq.Circuit(ops)
    return native, QuantumCircuit.from_cirq(native), None


def run_pipeline(qc, extra):
    return sv_pipeline(qc, extra)


def reference(native):
    p = np.zeros(1 << N)
    p[INPUT] = 1.0
    return p


def validate(probs, qc, extra):
    assert probs[INPUT] > 0.99, f"P(|{INPUT:03b}>)={probs[INPUT]:.4f}"
