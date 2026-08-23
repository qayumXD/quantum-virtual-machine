# benchmarks/algos/q30_qaoa_maxcut.py
"""Industry-flavored QAOA: MaxCut on a 4-cycle (chip partitioning style),
p=1. The parameterized template is imported symbolically from Qiskit and
bound through QVM's own bind_parameters() on every evaluation."""
import math
import numpy as np
from qiskit import QuantumCircuit as QK

from qvm.ir import QuantumCircuit
from qvm.simulator import Simulator

NAME = "qaoa_maxcut_qiskit"
FRAMEWORK = "qiskit"
CATEGORY = "real-world"
MATCH_NATIVE = False
EDGES = [(0, 1), (1, 2), (2, 3), (3, 0)]      # square: maxcut = 4
N = 4


def cut_of(idx: int) -> int:
    return sum(((idx >> i) & 1) != ((idx >> j) & 1) for i, j in EDGES)


def expected_cut(qc: QuantumCircuit) -> float:
    state, _ = Simulator().simulate(qc)
    probs = np.abs(state) ** 2
    total = 0.0
    for i, j in EDGES:
        e_zz = sum(
            p * (1 - 2 * ((idx >> i) & 1)) * (1 - 2 * ((idx >> j) & 1))
            for idx, p in enumerate(probs)
        )
        total += (1 - e_zz) / 2
    return total


def build():
    gamma, beta = "gamma", "beta"
    tpl = QK(N)
    tpl.h(range(N))
    gq, bq = __import__("qiskit").circuit.Parameter(gamma), __import__("qiskit").circuit.Parameter(beta)
    for i, j in EDGES:
        tpl.rzz(-gq, i, j)
    tpl.rx(2 * bq, range(N))
    qc = QuantumCircuit.from_qiskit(tpl)          # symbolic import through the pivot
    pmap = {p.name: p for p in qc.parameters}
    assert set(pmap) == {"gamma", "beta"}, f"unexpected params: {list(pmap)}"
    return None, qc, {"pmap": pmap}


def run_pipeline(qc, extra):
    pmap = extra["pmap"]
    best_cut, best_probs = -1.0, None
    evals = 0
    for g in np.linspace(-math.pi, math.pi, 21):
        for b in np.linspace(-math.pi / 2, math.pi / 2, 15):
            bound = qc.bind_parameters({pmap["gamma"]: float(g), pmap["beta"]: float(b)})
            c = expected_cut(bound)
            evals += 1
            if c > best_cut:
                state, _ = Simulator().simulate(bound)
                best_cut, best_probs = c, np.abs(state) ** 2
    extra["best_probs"] = best_probs
    extra["evals"] = evals
    return np.array([best_cut]), f"{evals} binds+evals, best ⟨cut⟩={best_cut:.4f}"


def validate(sentinel, qc, extra):
    # p=1 QAOA is approximate: expected cut plateaus well below the brute-force
    # optimum of 4 even though the MOST LIKELY states are the exact bisections.
    assert sentinel[0] >= 2.9, f"QAOA ⟨cut⟩={sentinel[0]:.3f} (< 2.9; ratio {sentinel[0]/4:.2f})"
    top = int(np.argmax(extra["best_probs"]))
    assert cut_of(top) == 4, f"most-likely state |{top:04b}> cuts only {cut_of(top)}/4"
    second = int(np.argsort(extra["best_probs"])[-2])
    assert cut_of(second) == 4, "both bipartitions should dominate the distribution"


def reference(native):
    return None
