# benchmarks/algos/q02_ghz5_qasm3.py
"""GHZ-5 authored in OpenQASM 3.0."""
import numpy as np
from qvm.qasm3_parser import OpenQASM3Parser
from benchmarks.harness import sv_pipeline

NAME = "ghz5_qasm3"
FRAMEWORK = "qasm3"
CATEGORY = "small"

QASM = """OPENQASM 3.0;
include "stdgates.inc";
qubit[5] q;
h q[0];
cx q[0], q[1];
cx q[1], q[2];
cx q[2], q[3];
cx q[3], q[4];
"""

N = 5


def build():
    native = None
    qc = OpenQASM3Parser().parse(QASM)
    assert qc.num_qubits == N, f"expected {N} qubits, got {qc.num_qubits}"
    return native, qc, None


def run_pipeline(qc, extra):
    return sv_pipeline(qc, extra)


def reference(native):
    p = np.zeros(1 << N)
    p[0] = p[(1 << N) - 1] = 0.5
    return p


def validate(probs, qc, extra):
    assert abs(probs[0] - 0.5) < 1e-7 and abs(probs[-1] - 0.5) < 1e-7, probs.round(4)
