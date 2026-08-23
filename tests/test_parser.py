# tests/test_parser.py

import pytest
from qvm.ir import QuantumCircuit
from qvm.parser import QASMParser

def test_parse_valid_circuit():
    """Tests parsing a valid circuit description."""
    circuit_desc = [
        {"name": "h", "qubits": [0]},
        {"name": "cx", "qubits": [0, 1]},
        {"name": "rz", "qubits": [2], "params": [0.5]}
    ]
    num_qubits = 3
    qc = QASMParser.parse(circuit_desc, num_qubits)

    assert isinstance(qc, QuantumCircuit)
    assert qc.num_qubits == num_qubits
    assert len(qc.operations) == 3
    assert qc.operations[0]["name"] == "h"
    assert qc.operations[1]["qubits"] == [0, 1]
    assert qc.operations[2]["params"] == [0.5]

def test_parse_empty_circuit():
    """Tests parsing an empty circuit description."""
    circuit_desc = []
    num_qubits = 2
    qc = QASMParser.parse(circuit_desc, num_qubits)
    assert isinstance(qc, QuantumCircuit)
    assert qc.num_qubits == num_qubits
    assert len(qc.operations) == 0

def test_parse_invalid_description():
    """Tests parsing invalid circuit descriptions."""
    # Missing 'name'
    invalid_desc_1 = [{"qubits": [0]}]
    with pytest.raises(ValueError, match="Each operation must have 'name' and 'qubits'"):
        QASMParser.parse(invalid_desc_1, 1)

    # Missing 'qubits'
    invalid_desc_2 = [{"name": "h"}]
    with pytest.raises(ValueError, match="Each operation must have 'name' and 'qubits'"):
        QASMParser.parse(invalid_desc_2, 1)

    # Invalid qubit index in description
    invalid_desc_3 = [{"name": "h", "qubits": [2]}]
    with pytest.raises(ValueError, match="Qubits must be a list of integers"):
        QASMParser.parse(invalid_desc_3, 2)
