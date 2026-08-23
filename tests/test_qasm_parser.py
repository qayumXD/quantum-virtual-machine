import pytest
from qvm.parser import OpenQASM2Parser
from qvm.ir import QuantumCircuit


def test_parse_simple_qasm():
    qasm = """OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0];
cx q[0],q[1];
measure q[0] -> c[0];
measure q[1] -> c[1];
"""
    qc = OpenQASM2Parser.parse(qasm)
    assert isinstance(qc, QuantumCircuit)
    assert qc.num_qubits == 2
    names = [op["name"] for op in qc.operations]
    assert names == ["h", "cx", "measure", "measure"]
    assert qc.operations[1]["qubits"] == [0, 1]


def test_parse_param_gate():
    qasm = """OPENQASM 2.0;
qreg q[1];
rz(1.57) q[0];
"""
    qc = OpenQASM2Parser.parse(qasm)
    assert qc.operations[0]["name"] == "rz"
    assert pytest.approx(qc.operations[0]["params"][0]) == 1.57


def test_unsupported_gate_errors():
    qasm = """OPENQASM 2.0;
qreg q[1];
u3(1,2,3) q[0];
"""
    with pytest.raises(ValueError):
        OpenQASM2Parser.parse(qasm)
