# benchmarks/algos/n0x_negative.py
"""Negative audit cases: unsupported constructs must fail LOUDLY with a
helpful error, never silently produce a wrong circuit."""
import numpy as np
import pytest

from qvm.exceptions import UnsupportedGateError, QVMParseError, QVMConversionError

NAME = "negative_expectations"
FRAMEWORK = "mixed"
CATEGORY = "negative"
MATCH_NATIVE = False


def build():
    from qvm.ir import QuantumCircuit as QC
    return None, QC(1), {}


def run_pipeline(_qc, _extra):
    results = {}

    # n01: Qiskit library composite gate → clean rejection naming the gate
    try:
        from qiskit import QuantumCircuit as QK
        from qiskit.circuit.library import StatePreparation
        qk = QK(1)
        qk.append(StatePreparation([1 / np.sqrt(2), 1 / np.sqrt(2)]), [0])
        from qvm.ir import QuantumCircuit
        try:
            QuantumCircuit.from_qiskit(qk)
            results["n01_library_gate"] = ("FAIL", "imported silently!")
        except UnsupportedGateError as e:
            results["n01_library_gate"] = ("PASS", str(e)[:70])
    except ImportError:
        results["n01_library_gate"] = ("SKIP", "qiskit missing")

    # n02: OpenQASM 2 full-register measure `measure q -> c;`
    from qvm.parser import OpenQASM2Parser
    qasm2 = """OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0];
cx q[0],q[1];
measure q -> c;
"""
    try:
        qc = OpenQASM2Parser.parse(qasm2)
        measures = [o for o in qc.operations if o["name"] == "measure"]
        if len(measures) == 2:
            results["n02_qasm2_register_measure"] = ("INFO", "parser expands register measure")
        elif len(measures) == 0:
            results["n02_qasm2_register_measure"] = ("FAIL", "register measure silently dropped")
        else:
            results["n02_qasm2_register_measure"] = ("INFO", f"{len(measures)} measures parsed")
    except Exception as e:
        results["n02_qasm2_register_measure"] = ("FAIL", f"raised {type(e).__name__}: {str(e)[:50]}")

    # n03 (promoted to positive): multi-controlled gates now import via exact
    # lowering — verify semantics survive the round trip into QVM.
    try:
        from qiskit import QuantumCircuit as QK
        from qiskit.quantum_info import Statevector as QKSv
        import numpy as _np
        qk = QK(5)
        qk.h(0); qk.mcx([0, 1, 2, 3], 4)
        from qvm.ir import QuantumCircuit
        qc = QuantumCircuit.from_qiskit(qk)
        st, _ = __import__("qvm.simulator", fromlist=["Simulator"]).Simulator().simulate(qc)
        got = _np.abs(st) ** 2
        ref = _np.asarray(QKSv.from_instruction(qk).probabilities(), float)
        ok = _np.allclose(got, ref, atol=1e-9)
        results["n03_mcx_lowering"] = ("PASS" if ok else "FAIL",
                                       "5-qubit mcx matches qiskit" if ok else "probability mismatch")
    except ImportError:
        results["n03_mcx_lowering"] = ("SKIP", "qiskit missing")

    # n04: malformed arity rejected at construction (not at simulation)
    from qvm.ir import QuantumCircuit as QC
    try:
        QC(2).add_operation("cx", [0])
        results["n04_arity_failfast"] = ("FAIL", "bad arity accepted")
    except Exception as e:
        ok = isinstance(e, Exception) and "acts on 2 qubit" in str(e)
        results["n04_arity_failfast"] = ("PASS" if ok else "FAIL", str(e)[:60])

    return results, "static"


def validate(results, _qc, _extra):
    bad = {k: v for k, v in results.items() if v[0] == "FAIL"}
    assert not bad, f"negative-case failures: {bad}"
