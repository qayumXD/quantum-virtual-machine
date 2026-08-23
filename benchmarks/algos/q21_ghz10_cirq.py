# benchmarks/algos/q21_ghz10_cirq.py
"""10-qubit GHZ chain authored in Cirq — probes simulator scaling through
the interop path."""
import numpy as np
import cirq

from benchmarks.harness import sv_pipeline
from qvm.ir import QuantumCircuit

NAME = "ghz10_cirq"
FRAMEWORK = "cirq"
CATEGORY = "scaling"
N = 10


def build():
    qs = cirq.LineQubit.range(N)
    ops = [cirq.H(qs[0])] + [cirq.CNOT(qs[i], qs[i + 1]) for i in range(N - 1)]
    native = cirq.Circuit(ops)
    return native, QuantumCircuit.from_cirq(native), None


def run_pipeline(qc, extra):
    return sv_pipeline(qc, extra)


def reference(native):
    return None


def validate(probs, qc, extra):
    assert abs(probs[0] - 0.5) < 1e-6 and abs(probs[-1] - 0.5) < 1e-6
    middle = 1.0 - probs[0] - probs[-1]
    assert middle < 1e-6, f"{middle:.2e} probability leaked outside GHZ subspace"
