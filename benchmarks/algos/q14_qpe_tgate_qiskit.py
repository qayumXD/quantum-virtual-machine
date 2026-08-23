# benchmarks/algos/q14_qpe_tgate_qiskit.py
"""Quantum Phase Estimation of the T gate (phase φ = 1/8), 3 counting
qubits. Exact eigenphase ⇒ deterministic '001' on the counting register.
The inverse QFT over the counting register is built as the exact reverse of
a forward-QFT op log, guaranteeing U_inv ≡ U†."""
import math
import numpy as np
from qiskit import QuantumCircuit as QK

from qvm.ir import QuantumCircuit

NAME = "qpe_tgate_qiskit"
FRAMEWORK = "qiskit"
CATEGORY = "advanced"
N_COUNT = 3


def _forward_qft_ops(n):
    """Standard textbook QFT op log (MSB-first ladder + final reversal)."""
    ops = []
    for j in reversed(range(n)):
        ops.append(("h", j))
        for i in reversed(range(j)):
            ops.append(("cp", i, j, math.pi / (2 ** (j - i))))
    for i in range(n // 2):
        ops.append(("swap", i, n - 1 - i))
    return ops


def build():
    qc = QK(N_COUNT + 1)
    eig = N_COUNT                          # qubit 3 holds |1> = T eigenstate
    qc.x(eig)
    qc.h(range(N_COUNT))
    # controlled-U^(2^k): T = diag(1, e^{iπ/4}) ⇒ phase kickback cp(2^k·π/4)
    for k in range(N_COUNT):
        qc.cp((2 ** k) * math.pi / 4, k, eig)
    # exact inverse QFT over the counting register
    fwd = _forward_qft_ops(N_COUNT)
    for op in reversed(fwd):
        if op[0] == "h":
            qc.h(op[1])
        elif op[0] == "cp":
            qc.cp(-op[3], op[1], op[2])
        else:
            qc.swap(op[1], op[2])
    return qc, QuantumCircuit.from_qiskit(qc), None


def run_pipeline(qc, extra):
    from benchmarks.harness import sv_pipeline
    return sv_pipeline(qc, extra)


def reference(native):
    return None   # marginal-based validation (eigenstate qubit traced out)


def validate(probs, qc, extra):
    marg = np.zeros(1 << N_COUNT)
    for idx, p in enumerate(probs):
        marg[idx & ((1 << N_COUNT) - 1)] += p      # low bits = counting register
    best = int(np.argmax(marg))
    assert best == 0b001, f"QPE peak at {best:03b}, expected 001 (φ=1/8)"
    assert marg[best] > 0.95, f"QPE peak only {marg[best]:.4f}"
