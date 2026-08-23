# benchmarks/algos/q33_vqc_classifier.py
"""Variational quantum classifier — a miniature of quantum-ML pipelines.
1D toy dataset (angle encoding), 2 qubits, 3 parameters trained with
finite-difference gradient descent directly against the QVM simulator."""
import math
import numpy as np

from qvm.ir import QuantumCircuit
from qvm.simulator import Simulator

NAME = "vqc_classifier_qvm"
FRAMEWORK = "qvm-native"
CATEGORY = "real-world"
MATCH_NATIVE = False

DATA = [
    (0.35, 0), (0.70, 0), (1.05, 0), (1.40, 0),
    (2.10, 1), (2.50, 1), (2.85, 1), (3.20, 1),
]


def model(f, w):
    """⟨Z0⟩ for input feature f and weights w — prediction s>0 ⇒ class 0."""
    qc = QuantumCircuit(2)
    qc.add_operation("rx", [0], params=[f])
    qc.add_operation("ry", [0], params=[w[0]])
    qc.add_operation("cx", [0, 1])
    qc.add_operation("ry", [1], params=[w[1]])
    qc.add_operation("cx", [0, 1])
    qc.add_operation("ry", [0], params=[w[2]])
    state, _ = Simulator().simulate(qc)
    probs = np.abs(state) ** 2
    z0 = sum(p * (1 - 2 * ((idx >> 0) & 1)) for idx, p in enumerate(probs))
    return z0


def loss(w):
    L = 0.0
    for f, y in DATA:
        s = model(f, w)
        target = 1.0 if y == 0 else -1.0
        L += (s - target) ** 2 / len(DATA)
    return L


def build():
    return None, QuantumCircuit(2), {}


def run_pipeline(_qc, extra):
    w = np.array([0.2, -0.1, 0.3])
    lr, eps = 1.2, 1e-4
    for epoch in range(160):
        grads = np.zeros_like(w)
        for i in range(len(w)):
            wp, wm = w.copy(), w.copy()
            wp[i] += eps; wm[i] -= eps
            grads[i] = (loss(wp) - loss(wm)) / (2 * eps)
        w -= lr * grads
        if epoch % 40 == 0:
            pass
    acc = sum(
        (model(f, w) > 0) == (y == 0) for f, y in DATA
    )
    extra["weights"], extra["acc"] = w.tolist(), int(acc)
    return np.array([float(loss(w)), float(acc)]), f"final loss={loss(w):.4f}, train acc={acc}/8"


def validate(sentinel, qc, extra):
    assert sentinel[1] >= 7, f"train accuracy only {int(sentinel[1])}/8"


def reference(native):
    return None
