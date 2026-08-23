# benchmarks/algos/q01_bell_qasm.py
"""Bell pair authored in OpenQASM 2.0 — smallest end-to-end smoke test.
Measurement-free so the statevector (not a collapsed trajectory) is checked."""
import numpy as np
from qvm.parser import OpenQASM2Parser
from benchmarks.harness import sv_pipeline

NAME = "bell_qasm2"
FRAMEWORK = "qasm2"
CATEGORY = "small"

QASM = """OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0];
cx q[0],q[1];
"""


def build():
    native = None  # no external framework involved; QVM IS the native stack here
    qc = OpenQASM2Parser.parse(QASM)
    return native, qc, None


def run_pipeline(qc, extra):
    return sv_pipeline(qc, extra)


def reference(native):
    p = np.zeros(4)
    p[0b00] = p[0b11] = 0.5
    return p


def validate(probs, qc, extra):
    assert abs(probs[0b00] - 0.5) < 1e-9 and abs(probs[0b11] - 0.5) < 1e-9, probs
