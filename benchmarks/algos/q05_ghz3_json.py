# benchmarks/algos/q05_ghz3_json.py
"""GHZ-3 authored as a JSON gate list — covers the JSON ingestion path."""
import numpy as np
from qvm.parser import QASMParser
from benchmarks.harness import sv_pipeline

NAME = "ghz3_json"
FRAMEWORK = "json"
CATEGORY = "small"

DESC = [
    {"name": "h", "qubits": [0]},
    {"name": "cx", "qubits": [0, 1]},
    {"name": "cx", "qubits": [1, 2]},
]
N = 3


def build():
    native = None
    qc = QASMParser.parse(DESC, N)
    return native, qc, None


def run_pipeline(qc, extra):
    return sv_pipeline(qc, extra)


def reference(native):
    p = np.zeros(1 << N)
    p[0] = p[-1] = 0.5
    return p


def validate(probs, qc, extra):
    # JSON round trip must be lossless
    import json as _json
    from qvm.ir import QuantumCircuit
    back = QuantumCircuit.from_json(qc.to_json())
    assert [(o["name"], tuple(o["qubits"])) for o in back.operations] == \
           [(o["name"], tuple(o["qubits"])) for o in qc.operations], "JSON round-trip drifted"
