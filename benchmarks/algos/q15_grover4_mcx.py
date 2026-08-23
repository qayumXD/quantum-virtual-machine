# benchmarks/algos/q15_grover4_mcx.py
"""Grover search over 4 qubits marking |1111>, oracle + diffuser built with
native Qiskit multi-controlled gates (mcz / mcx) — proving the importer's
exact lowering widens the usable circuit universe end-to-end."""
import math
import numpy as np
from qiskit import QuantumCircuit as QK

from qvm.ir import QuantumCircuit
from benchmarks.harness import sv_pipeline

NAME = "grover4_mcx_qiskit"
FRAMEWORK = "qiskit"
CATEGORY = "advanced"
MARKED = 0b1111
N = 4
N_ITER = int(math.floor(math.pi / 4 * math.sqrt(16)))   # = 3


def build():
    qc = QK(N)
    qc.h(range(N))
    for _ in range(N_ITER):
        # oracle: phase flip on |1111> via MCP(pi) == MCZ
        qc.mcp(math.pi, [0, 1, 2], 3)
        # diffuser: H^4 X^4 MCP(pi) X^4 H^4
        qc.h(range(N)); qc.x(range(N))
        qc.mcp(math.pi, [0, 1, 2], 3)
        qc.x(range(N)); qc.h(range(N))
    return qc, QuantumCircuit.from_qiskit(qc), None


def run_pipeline(qc, extra):
    return sv_pipeline(qc, extra)


def reference(native):
    amps = np.full(1 << N, 1 / math.sqrt(1 << N))
    for _ in range(N_ITER):
        amps[MARKED] *= -1
        amps = 2 * amps.mean() - amps
    return np.abs(amps) ** 2


def validate(probs, qc, extra):
    assert probs[MARKED] > 0.7, f"|{MARKED:04b}> prob only {probs[MARKED]:.3f}"
    assert int(np.argmax(probs)) == MARKED, "marked state is not dominant"
