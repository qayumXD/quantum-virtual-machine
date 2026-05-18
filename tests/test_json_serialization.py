# tests/test_json_serialization.py
import json
import pytest

from src.qvm.ir import QuantumCircuit

@pytest.fixture
def sample_circuit():
    qc = QuantumCircuit(2)
    qc.add_classical_register('c', 2)
    qc.add_operation('h', [0])
    qc.add_operation('cx', [0, 1])
    qc.add_operation('measure', [0], target_bit=('c', 0))
    qc.add_operation('measure', [1], target_bit=('c', 1))
    return qc

def test_json_roundtrip(sample_circuit):
    data = sample_circuit.to_json()
    # Ensure data is serializable
    json_str = json.dumps(data)
    loaded = json.loads(json_str)
    recovered = QuantumCircuit.from_json(loaded)
    assert str(sample_circuit) == str(recovered)
