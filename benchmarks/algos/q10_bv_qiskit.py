# benchmarks/algos/q10_bv_qiskit.py
"""Bernstein-Vazirani with secret s=1101, authored in Qiskit.
Shot-based: the measurement must reveal the secret with certainty."""
from qiskit import QuantumCircuit as QK

from qvm.ir import QuantumCircuit
from benchmarks.harness import shots_pipeline_factory

NAME = "bernstein_vazirani_qiskit"
FRAMEWORK = "qiskit"
CATEGORY = "textbook"
MATCH_NATIVE = False
SECRET = [1, 1, 0, 1]          # s[0..3], cx from q_i when bit set
SHOTS = 2048


def build():
    qc = QK(5, 4)
    qc.x(4)
    qc.h(4)
    qc.h(range(4))
    for i, bit in enumerate(SECRET):
        if bit:
            qc.cx(i, 4)
    qc.h(range(4))
    qc.measure(range(4), range(4))
    return qc, QuantumCircuit.from_qiskit(qc), None


def build_qvm(native):
    from qvm.ir import QuantumCircuit
    return QuantumCircuit.from_qiskit(native)


def run_pipeline(qc, extra):
    return shots_pipeline_factory(SHOTS, seed=11)(qc, extra)


def reference(native):
    return None


def validate(counts, qc, extra):
    expected = "".join(str(b) for b in SECRET)
    assert counts, "no counts produced"
    top_key, top_count = max(counts.items(), key=lambda kv: kv[1])
    assert top_key == expected, f"dominant outcome {top_key!r} != secret {expected!r}"
    assert top_count >= 0.98 * SHOTS, f"secret leaked: {top_count}/{SHOTS}"
