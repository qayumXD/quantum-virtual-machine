# benchmarks/algos/q13_qft_roundtrip_qiskit.py
"""Quantum Fourier Transform + inverse QFT on |101> — must refocus to a
delta. The inverse is constructed as the *exact reverse op sequence* of the
forward ladder with negated angles, so U_inv ≡ U† by construction."""
import math
import numpy as np
from qiskit import QuantumCircuit as QK

from qvm.ir import QuantumCircuit
from benchmarks.harness import sv_pipeline

NAME = "qft_roundtrip_qiskit"
FRAMEWORK = "qiskit"
CATEGORY = "textbook"
INPUT = 0b101
N = 3


def forward_ops(n):
    """Forward QFT as an explicit op log: ("h", q) | ("cp", ctrl, tgt, ang)
    | ("swap", a, b). Standard textbook MSB-first ladder (little-endian)."""
    ops = []
    for j in reversed(range(n)):
        ops.append(("h", j))
        for i in reversed(range(j)):
            ops.append(("cp", i, j, math.pi / (2 ** (j - i))))
    for i in range(n // 2):
        ops.append(("swap", i, n - 1 - i))
    return ops


def append_ops(qc, ops, negate=False, reverse=False):
    seq = reversed(ops) if reverse else ops
    for op in seq:
        if op[0] == "h":
            qc.h(op[1])
        elif op[0] == "cp":
            ang = -op[3] if negate else op[3]
            qc.cp(ang, op[1], op[2])
        elif op[0] == "swap":
            qc.swap(op[1], op[2])


def build():
    fwd = forward_ops(N)
    qc = QK(N)
    qc.x(0); qc.x(2)                      # prepare |101>
    append_ops(qc, fwd)
    append_ops(qc, fwd, negate=True, reverse=True)   # exact U†
    return qc, QuantumCircuit.from_qiskit(qc), None


def run_pipeline(qc, extra):
    return sv_pipeline(qc, extra)


def reference(native):
    p = np.zeros(1 << N)
    p[INPUT] = 1.0
    return p


def validate(probs, qc, extra):
    assert probs[INPUT] > 0.99, f"QFT round-trip lost focus: P(|{INPUT:03b}>)={probs[INPUT]:.4f}"
