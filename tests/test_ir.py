# tests/test_ir.py

import pytest
from src.qvm.ir import QuantumCircuit

def test_qc_creation():
    """Tests valid and invalid QuantumCircuit creation."""
    qc = QuantumCircuit(2)
    assert qc.num_qubits == 2
    assert qc.operations == []

    with pytest.raises(ValueError, match="Number of qubits must be a positive integer"):
        QuantumCircuit(0)
    with pytest.raises(ValueError, match="Number of qubits must be a positive integer"):
        QuantumCircuit(-1)
    with pytest.raises(ValueError):
        QuantumCircuit("a")

def test_add_valid_operation():
    """Tests adding valid operations to a circuit."""
    qc = QuantumCircuit(3)
    qc.add_operation("h", [0])
    assert len(qc.operations) == 1
    assert qc.operations[0] == {"name": "h", "qubits": [0], "params": []}

    qc.add_operation("cx", [0, 1])
    assert len(qc.operations) == 2
    assert qc.operations[1] == {"name": "cx", "qubits": [0, 1], "params": []}
    
    qc.add_operation("rz", [2], [0.5])
    assert len(qc.operations) == 3
    assert qc.operations[2] == {"name": "rz", "qubits": [2], "params": [0.5]}

def test_add_invalid_operation():
    """Tests adding invalid operations to a circuit."""
    qc = QuantumCircuit(2)
    
    # Invalid gate name
    with pytest.raises(ValueError, match="Gate name must be a non-empty string"):
        qc.add_operation("", [0])
    with pytest.raises(ValueError):
        qc.add_operation(123, [0])

    # Invalid qubit index
    with pytest.raises(ValueError, match="Qubits must be a list of integers"):
        qc.add_operation("h", [2]) # Qubit 2 in a 2-qubit circuit
    with pytest.raises(ValueError, match="Qubits must be a list of integers"):
        qc.add_operation("h", [-1])
    with pytest.raises(ValueError, match="Qubits must be a list of integers"):
        qc.add_operation("h", [0, "a"])

    # Invalid params
    with pytest.raises(ValueError, match="Parameters must be a list or None"):
        qc.add_operation("rz", [0], 0.5)
