# benchmarks/harness.py
"""Unified audit harness.

Each algorithm module (benchmarks/algos/*.py) exposes:
    NAME, FRAMEWORK, CATEGORY          : metadata
    build()   -> (native, qc, extra)   : native-framework circuit, QVM IR, misc
    run_pipeline(qc, extra) -> (result, meta)   : result is probability vector
                                                 OR counts dict (shots mode)
    validate(result, qc, extra)        : algorithm-specific assertions
    reference(native) -> probs         : optional; defaults to native simulator
    MATCH_NATIVE                       : set False for shot-based algorithms
"""
import time
import numpy as np

try:
    import qiskit
    from qiskit.quantum_info import Statevector as QKStatevector
except ImportError:
    qiskit = None
try:
    import cirq
except ImportError:
    cirq = None

from qvm.ir import QuantumCircuit
from qvm.simulator import Simulator


def native_probs(circ):
    """Reference probabilities (little-endian, q0 = LSB) from the framework
    the circuit was authored in."""
    if isinstance(circ, QuantumCircuit):
        state, _ = Simulator().simulate(circ)
        return np.abs(state) ** 2
    if qiskit is not None and isinstance(circ, qiskit.QuantumCircuit):
        return np.asarray(QKStatevector.from_instruction(circ).probabilities(), float)
    if cirq is not None and isinstance(circ, cirq.Circuit):
        n = len(circ.all_qubits())
        vec = cirq.Simulator(dtype=np.complex128).simulate(
            circ, qubit_order=cirq.LineQubit.range(n)).final_state_vector
        probs = np.abs(vec) ** 2
        idx = np.arange(probs.size)
        rev = np.zeros(idx.size, dtype=int)
        for q in range(n):
            rev |= ((idx >> q) & 1) << (n - 1 - q)
        return probs[rev]
    raise TypeError(f"unknown circuit type {type(circ)}")


def marginal(probs, keep, n):
    """Marginal distribution over `keep` qubit indices (little-endian)."""
    keep = sorted(keep)
    out = np.zeros(1 << len(keep))
    for i in range(len(probs)):
        key = 0
        for k, q in enumerate(keep):
            key |= ((i >> q) & 1) << k
        out[key] += probs[i]
    return out


def default_reference(native):
    return native_probs(native)


def sv_pipeline(qc: QuantumCircuit, _extra=None):
    """Default pipeline stage: QVM dense statevector → probabilities."""
    state, _mem = Simulator().simulate(qc)
    return np.abs(state) ** 2, "statevector"


def shots_pipeline_factory(shots=2048, seed=None):
    """Pipeline stage for measurement algorithms: returns counts."""
    def run(qc: QuantumCircuit, _extra=None):
        counts = Simulator().sample(qc, shots=shots, seed=seed)
        return counts, f"shots={shots}"
    return run


def run_case(mod):
    """Execute one audit case through all pipeline stages."""
    res = {"id": mod.NAME, "framework": mod.FRAMEWORK, "category": mod.CATEGORY,
           "import": "-", "simulate": "-", "match": "-",
           "validate": "-", "time_s": 0.0}
    t0 = time.time()
    try:
        native, qc, extra = mod.build()
        if not isinstance(qc, QuantumCircuit):
            raise AssertionError("build() did not return a QVM QuantumCircuit")
        res["import"] = "OK"
    except Exception as e:
        res["import"] = f"FAIL {type(e).__name__}: {str(e)[:80]}"
        res["time_s"] = time.time() - t0
        return res

    try:
        result, meta = mod.run_pipeline(qc, extra)
        res["simulate"] = f"OK ({meta})"
    except Exception as e:
        res["simulate"] = f"FAIL {type(e).__name__}: {str(e)[:80]}"
        res["time_s"] = time.time() - t0
        return res

    if getattr(mod, "MATCH_NATIVE", True):
        try:
            ref = getattr(mod, "reference", default_reference)(native)
            if ref is None:
                res["match"] = "SKIP"
            else:
                got = np.asarray(result, dtype=float)
                md = float(np.max(np.abs(got - ref))) if got.shape == ref.shape else float("inf")
                res["match"] = "OK" if md < getattr(mod, "TOL", 1e-7) else f"MISMATCH maxdiff={md:.2e}"
        except Exception as e:
            res["match"] = f"ERR {type(e).__name__}: {str(e)[:60]}"

    try:
        mod.validate(result, qc, extra)
        res["validate"] = "PASS"
    except Exception as e:
        res["validate"] = f"FAIL {type(e).__name__}: {str(e)[:80]}"

    res["time_s"] = time.time() - t0
    return res
