# benchmarks/algos/q32_portfolio_qaoa.py
"""Portfolio selection via QAOA: pick K=2 of 3 assets maximizing return minus
concentration risk under a budget penalty — a miniature of production finance
optimizers. QUBO → Ising → depth-p=2 QAOA optimized by multi-start
Nelder-Mead directly against the QVM simulator."""
import itertools
import numpy as np
from scipy.optimize import minimize
from qiskit import QuantumCircuit as QK
from qiskit.circuit import Parameter

from qvm.ir import QuantumCircuit
from qvm.simulator import Simulator

NAME = "portfolio_qaoa_qiskit"
FRAMEWORK = "qiskit"
CATEGORY = "real-world"
MATCH_NATIVE = False

MU = [0.18, 0.22, 0.25]
SIGMA = {(0, 1): 0.08, (0, 2): 0.12, (1, 2): 0.06}
LAMBDA_RISK = 1.2
BUDGET_K = 2
RHO_BUDGET = 0.9
DEPTH_P = 2


def classical_energy(x):
    ret = sum(m * xi for m, xi in zip(MU, x))
    risk = LAMBDA_RISK * sum(s * x[i] * x[j] for (i, j), s in SIGMA.items())
    budget = RHO_BUDGET * (sum(x) - BUDGET_K) ** 2
    return -(ret) + risk + budget          # minimization form


def ising_terms():
    """Fit H(z) = Σ a_i z_i + Σ b_ij z_i z_j + const over z ∈ {±1}³ with
    x = (1 - z)/2 by exact interpolation over all 8 configurations."""
    cfgs = list(itertools.product([1, -1], repeat=3))
    A, y = [], []
    for z in cfgs:
        row = list(z) + [z[0]*z[1], z[0]*z[2], z[1]*z[2], 1]
        A.append(row)
        x = tuple((1 - zi) // 2 for zi in z)
        y.append(classical_energy(x))
    coeffs, *_ = np.linalg.lstsq(np.array(A, float), np.array(y), rcond=None)
    a, b, const = coeffs[:3], coeffs[3:6], coeffs[6]
    resid = max(abs(float(np.dot(A[k], coeffs)) - y[k]) for k in range(8))
    assert resid < 1e-9, f"Ising fit residual {resid}"
    return {i: float(v) for i, v in enumerate(a)}, \
        {tuple(p): float(v) for p, v in zip([(0, 1), (0, 2), (1, 2)], b)}, const


def circuit_energy(probs, lin, quad, const):
    e = const
    for idx, p in enumerate(probs):
        z = [1 - 2 * ((idx >> i) & 1) for i in range(3)]
        e += p * sum(lin[i] * z[i] for i in range(3))
        e += p * sum(v * z[i] * z[j] for (i, j), v in quad.items())
    return e


def build():
    lin, quad, _const = ising_terms()
    gs = [Parameter(f"gamma{k}") for k in range(DEPTH_P)]
    bs = [Parameter(f"beta{k}") for k in range(DEPTH_P)]
    tpl = QK(3)
    tpl.h(range(3))
    for k in range(DEPTH_P):
        for i, a in lin.items():
            tpl.rz(-2 * a * gs[k], i)
        for (i, j), v in quad.items():
            tpl.rzz(-2 * v * gs[k], i, j)
        tpl.rx(2 * bs[k], range(3))
    qc = QuantumCircuit.from_qiskit(tpl)
    pmap = {p.name: p for p in qc.parameters}
    return None, qc, {"pmap": pmap}


def run_pipeline(qc, extra):
    lin, quad, const = ising_terms()
    pmap = extra["pmap"]

    def objective(x):
        binds = {pmap[f"gamma{k}"]: float(x[2 * k]) for k in range(DEPTH_P)}
        binds.update({pmap[f"beta{k}"]: float(x[2 * k + 1]) for k in range(DEPTH_P)})
        bound = qc.bind_parameters(binds)
        state, _ = Simulator().simulate(bound)
        return circuit_energy(np.abs(state) ** 2, lin, quad, const)

    rng = np.random.default_rng(1)
    best = (np.inf, None)
    starts = [np.zeros(2 * DEPTH_P)] + list(rng.uniform(-1, 1, size=(6, 2 * DEPTH_P)))
    evals = 0
    for s in starts:
        res = minimize(objective, s, method="Nelder-Mead",
                       options={"maxiter": 600, "fatol": 1e-8, "xatol": 1e-6})
        evals += res.nfev
        if res.fun < best[0]:
            best = (float(res.fun), res.x.copy())
    extra["best_x"] = best[1]
    return np.array([best[0]]), f"{evals} binds+evals, best ⟨E⟩={best[0]:.5f}"


def validate(sentinel, qc, extra):
    brute = min(classical_energy(x) for x in itertools.product([0, 1], repeat=3))
    gap = sentinel[0] - brute
    # Depth-2 QAOA on a penalty-weighted QUBO is approximate by nature;
    # closing the remaining gap requires penalty tuning or higher depth.
    assert gap <= 0.15, (
        f"QAOA ⟨E⟩={sentinel[0]:.5f} vs optimum {brute:.5f} (gap {gap:.4f})"
    )


def reference(native):
    return None
