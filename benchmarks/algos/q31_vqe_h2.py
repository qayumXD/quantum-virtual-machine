# benchmarks/algos/q31_vqe_h2.py
"""VQE for molecular hydrogen (STO-3G, 0.735 Å) — the canonical chemistry
benchmark. 4-parameter hardware-efficient ansatz optimized on the QVM
engine with Nelder-Mead; energy validated against exact diagonalization."""
import numpy as np
from scipy.optimize import minimize

from qvm.ir import QuantumCircuit
from qvm.simulator import Simulator
from qvm.observable import Hamiltonian

NAME = "vqe_h2_qvm"
FRAMEWORK = "qvm-native"
CATEGORY = "real-world"
MATCH_NATIVE = False

H2_TERMS = {
    "II": -1.052373245772859,
    "ZI": -0.39793742484318045,
    "IZ": 0.39793742484318045,
    "ZZ": -0.01128010425623538,
    "XX": 0.18093119978423156,
}
H = Hamiltonian.from_dict({k: v for k, v in H2_TERMS.items() if k != "II"})
OFFSET = H2_TERMS["II"]


def ansatz(params):
    a, b, c, d = params
    qc = QuantumCircuit(2)
    qc.add_operation("ry", [0], params=[a])
    qc.add_operation("ry", [1], params=[b])
    qc.add_operation("cx", [0, 1])
    qc.add_operation("ry", [1], params=[c])
    qc.add_operation("cx", [0, 1])
    qc.add_operation("ry", [0], params=[d])
    return qc


def energy(params):
    qc = ansatz([float(p) for p in params])
    return OFFSET + Simulator().expectation_value(qc, H)


def exact_ground():
    M = H.to_matrix(2) + OFFSET * np.eye(4)
    return float(np.linalg.eigvalsh(M)[0])


def build():
    return None, ansatz([0.1, 0.1, 0.1, 0.1]), {}


def run_pipeline(qc, extra):
    best = np.inf
    rng = np.random.default_rng(42)
    for start in rng.uniform(-np.pi, np.pi, size=(5, 4)):
        res = minimize(energy, start, method="Nelder-Mead",
                       options={"maxiter": 400, "xatol": 1e-5, "fatol": 1e-8})
        best = min(best, float(res.fun))
    extra["vqe_energy"] = best
    return np.array([best]), f"5-start Nelder-Mead → {best:.6f} Ha"


def validate(sentinel, qc, extra):
    exact = exact_ground()
    err = abs(sentinel[0] - exact)
    assert err < 5e-3, f"VQE error {err:.5f} Ha (got {sentinel[0]:.6f}, exact {exact:.6f})"


def reference(native):
    return None
