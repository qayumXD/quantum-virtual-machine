# benchmarks/algos/q11_dj_qiskit.py
"""Deutsch-Jozsa, balanced oracle f(x) = parity(x), in Qiskit.
A balanced function must NEVER yield the all-zeros outcome."""
import numpy as np
from qiskit import QuantumCircuit as QK

from qvm.ir import QuantumCircuit
from benchmarks.harness import shots_pipeline_factory

NAME = "deutsch_jozsa_qiskit"
FRAMEWORK = "qiskit"
CATEGORY = "textbook"
MATCH_NATIVE = False
N_INPUT = 3
SHOTS = 1024


def build():
    qc = QK(N_INPUT + 1, N_INPUT)
    qc.x(N_INPUT)
    qc.h(N_INPUT)
    qc.h(range(N_INPUT))
    for i in range(N_INPUT):          # balanced oracle: parity of input bits
        qc.cx(i, N_INPUT)
    qc.h(range(N_INPUT))
    qc.measure(range(N_INPUT), range(N_INPUT))
    from qvm.ir import QuantumCircuit
    return qc, QuantumCircuit.from_qiskit(qc), None


def run_pipeline(qc, extra):
    return shots_pipeline_factory(SHOTS, seed=3)(qc, extra)


def reference(native):
    return None


def validate(counts, qc, extra):
    zeros = counts.get("000", 0)
    assert zeros == 0, f"balanced DJ produced |000> {zeros} times (must be impossible)"
