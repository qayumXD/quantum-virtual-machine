# benchmarks/algos/q12_wstate_qiskit.py
"""W-state on 3 qubits (equal superposition of single excitations).
Built only from the shared gate vocabulary: ry, x, cx, ccx."""
import numpy as np
from qiskit import QuantumCircuit as QK
import math

from benchmarks.harness import sv_pipeline

NAME = "wstate3_qiskit"
FRAMEWORK = "qiskit"
CATEGORY = "textbook"
EXCITED = [0b001, 0b010, 0b100]


def build():
    qc = QK(3)
    theta = 2 * math.acos(math.sqrt(2 / 3))       # P(q0=1) = 1/3
    # split remaining amplitude onto q1 within the q0=0 branch
    qc.ry(theta, 0)
    qc.x(0)
    # CRy(pi/2) control=q0 target=q1, decomposed into vocabulary gates
    qc.ry(math.pi / 4, 1)
    qc.cx(0, 1)
    qc.ry(-math.pi / 4, 1)
    qc.cx(0, 1)
    qc.x(0)
    # move the still-empty branch's excitation to q2 via Toffoli on zero-flags
    qc.x(0); qc.x(1)
    qc.ccx(0, 1, 2)
    qc.x(0); qc.x(1)
    from qvm.ir import QuantumCircuit
    return qc, QuantumCircuit.from_qiskit(qc), None


def run_pipeline(qc, extra):
    return sv_pipeline(qc, extra)


def reference(native):
    p = np.zeros(8)
    for i in EXCITED:
        p[i] = 1 / 3
    return p


def validate(probs, qc, extra):
    for i in EXCITED:
        assert abs(probs[i] - 1 / 3) < 1e-9, f"|{i:03b}>={probs[i]:.6f} != 1/3"
    others = sum(p for i, p in enumerate(probs) if i not in EXCITED)
    assert others < 1e-9, f"leakage outside W-space: {others:.2e}"
