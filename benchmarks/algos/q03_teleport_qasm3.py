# benchmarks/algos/q03_teleport_qasm3.py
"""Quantum teleportation in OpenQASM 3.0 — mid-circuit measurement plus
classical feedback (if-based corrections). Stresses the control-flow path
of the parser AND the simulator's classical memory."""
import math
import numpy as np
from qvm.qasm3_parser import OpenQASM3Parser

from benchmarks.harness import sv_pipeline  # noqa: F401 (unused; shots below)
from qvm.simulator import Simulator

NAME = "teleport_qasm3"
FRAMEWORK = "qasm3"
CATEGORY = "textbook"
MATCH_NATIVE = False           # validated statistically via shots
THETA = 0.8                    # |psi> = Ry(theta)|0>; P(measure 1) = sin^2(theta/2)
SHOTS = 3000

QASM = f"""OPENQASM 3.0;
include "stdgates.inc";
qubit[3] q;
bit[2] mid;
bit[1] out;
ry({THETA}) q[0];
h q[1];
cx q[1], q[2];
cx q[0], q[1];
h q[0];
mid[0] = measure q[0];
mid[1] = measure q[1];
if (mid[1] == 1) {{
  x q[2];
}}
if (mid[0] == 1) {{
  z q[2];
}}
out[0] = measure q[2];
"""


def build():
    native = None
    qc = OpenQASM3Parser().parse(QASM)
    return native, qc, None


def run_pipeline(qc, extra):
    counts = Simulator().sample(qc, shots=SHOTS, seed=7)
    return counts, f"shots={SHOTS}"


def reference(native):
    return None


def validate(counts, qc, extra):
    p_one = sum(c for bits, c in counts.items() if bits.strip()[-1] == "1") / SHOTS
    expected = math.sin(THETA / 2) ** 2
    assert abs(p_one - expected) < 0.04, (
        f"teleported state fidelity off: P(1)={p_one:.3f} expected {expected:.3f}"
    )
