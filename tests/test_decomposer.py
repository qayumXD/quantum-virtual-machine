# tests/test_decomposer.py

import pytest
from qvm.ir import QuantumCircuit
from qvm.decomposer import Decomposer

def test_decompose_native_gate():
    """Tests that a native gate is not decomposed."""
    native_gates = {"h", "cx"}
    decomposer = Decomposer(native_gates)
    
    op = {"name": "h", "qubits": [0], "params": []}
    decomposed_ops = decomposer.decompose_operation(op)
    
    assert decomposed_ops == [op] # Should return the original operation

def test_decompose_toffoli():
    """Tests the decomposition of a Toffoli gate."""
    native_gates = {"h", "cx", "rz"}
    decomposer = Decomposer(native_gates)
    
    op = {"name": "toffoli", "qubits": [0, 1, 2], "params": []}
    decomposed_ops = decomposer.decompose_operation(op)
    
    # Check that it was decomposed into multiple operations
    assert isinstance(decomposed_ops, list)
    assert len(decomposed_ops) > 1
    
    # Check that all decomposed gates are native
    for new_op in decomposed_ops:
        assert new_op["name"] in native_gates

    # Check the number of gates (specific to our decomposition)
    assert len(decomposed_ops) == 15

def test_decompose_unsupported_gate():
    """Tests that an error is raised for a gate with no decomposition rule."""
    native_gates = {"h"}
    decomposer = Decomposer(native_gates)
    
    op = {"name": "fredkin", "qubits": [0, 1, 2], "params": []}
    with pytest.raises(ValueError, match="No decomposition rule available"):
        decomposer.decompose_operation(op)

def test_full_circuit_decomposition():
    """Tests decomposition of a full circuit."""
    qc = QuantumCircuit(3)
    qc.add_operation("h", [0])
    qc.add_operation("toffoli", [0, 1, 2])
    
    native_gates = {"h", "cx", "rz"}
    decomposer = Decomposer(native_gates)
    
    decomposed_qc = decomposer.decompose_circuit(qc)
    
    # Original circuit had 2 ops, decomposed should have 1 (H) + 15 (Toffoli) = 16 ops
    assert len(decomposed_qc.operations) == 16
    
    # Check that 'toffoli' is no longer in the circuit
    op_names = {op["name"] for op in decomposed_qc.operations}
    assert "toffoli" not in op_names
    assert "h" in op_names
    assert "cx" in op_names
    assert "rz" in op_names
