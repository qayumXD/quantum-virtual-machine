# benchmarks/algos/q04_grover3_qasm3.py
"""Grover search over 3 qubits marking |101>, two iterations, in OpenQASM 3.0."""
import math
import numpy as np
from qvm.qasm3_parser import OpenQASM3Parser
from benchmarks.harness import sv_pipeline

NAME = "grover3_qasm3"
FRAMEWORK = "qasm3"
CATEGORY = "textbook"

MARKED = 0b101

ORACLE = """x q[1];
h q[1];
ccx q[0], q[2], q[1];
h q[1];
x q[1];
"""

DIFFUSER = """h q[0]; h q[1]; h q[2];
x q[0]; x q[1]; x q[2];
h q[2];
ccx q[0], q[1], q[2];
h q[2];
x q[0]; x q[1]; x q[2];
h q[0]; h q[1]; h q[2];
"""

N_ITER = int(math.floor(math.pi / 4 * math.sqrt(8)))   # = 2


def _make_qasm():
    body = "h q[0]; h q[1]; h q[2];\n" + (ORACLE + DIFFUSER) * N_ITER
    header = 'OPENQASM 3.0;\ninclude "stdgates.inc";\nqubit[3] q;\n'
    return header + body


def build():
    native = None
    qc = OpenQASM3Parser().parse(_make_qasm())
    return native, qc, None


def run_pipeline(qc, extra):
    return sv_pipeline(qc, extra)


def reference(native):
    # exact ideal Grover amplitudes after k iterations
    amps = np.full(8, 1 / math.sqrt(8))
    for _ in range(N_ITER):
        amps[MARKED] *= -1
        mean = amps.mean()
        amps = 2 * mean - amps
    return np.abs(amps) ** 2


def validate(probs, qc, extra):
    assert probs[MARKED] > 0.75, f"|{MARKED:03b}> prob only {probs[MARKED]:.3f}"
    assert max(i for i in range(8) if i != MARKED) is not None
    assert probs[MARKED] >= max(p for i, p in enumerate(probs) if i != MARKED)
