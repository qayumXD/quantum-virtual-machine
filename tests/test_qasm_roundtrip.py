# tests/test_qasm_roundtrip.py
import pytest
from src.qvm.ir import QuantumCircuit

def test_qasm_roundtrip():
    qc = QuantumCircuit(2)
    qc.add_classical_register("c", 2)
    qc.add_operation("h", [0])
    qc.add_operation("cx", [0, 1])
    qc.add_operation("measure", [0], target_bit=("c", 0))
    qc.add_operation("measure", [1], target_bit=("c", 1))

    qasm_str = qc.to_qasm()
    assert "OPENQASM 3.0" in qasm_str
    assert "qubit[2]" in qasm_str
    assert "h q[0];" in qasm_str

    qc2 = QuantumCircuit.from_qasm(qasm_str)
    assert qc2.num_qubits == 2
    assert "c" in qc2.classical_registers
    
    # We compare string representations or number of ops
    # The parsers might slightly change representation formats but length should match
    assert len(qc2.operations) == len(qc.operations)
