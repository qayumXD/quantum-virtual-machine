# tests/test_backend_cross_conversion.py
import pytest

try:
    import qiskit
except ImportError:  # pragma: no cover
    qiskit = None

try:
    import cirq
except ImportError:  # pragma: no cover
    cirq = None

from src.qvm.ir import QuantumCircuit

@pytest.fixture
def sample_circuit():
    qc = QuantumCircuit(2)
    qc.add_classical_register("c", 2)
    qc.add_operation("h", [0])
    qc.add_operation("cx", [0, 1])
    qc.add_operation("measure", [0], target_bit=("c", 0))
    qc.add_operation("measure", [1], target_bit=("c", 1))
    return qc

def test_qiskit_to_cirq_conversion(sample_circuit):
    if qiskit is None or cirq is None:
        pytest.skip("Qiskit or Cirq not installed")
    
    q_circ = sample_circuit.to_qiskit()
    c_circ = QuantumCircuit.qiskit_to_cirq(q_circ)
    
    assert c_circ is not None
    assert len(list(c_circ.all_operations())) == 4

def test_cirq_to_qiskit_conversion(sample_circuit):
    if qiskit is None or cirq is None:
        pytest.skip("Qiskit or Cirq not installed")
    
    c_circ = sample_circuit.to_cirq()
    q_circ = QuantumCircuit.cirq_to_qiskit(c_circ)
    
    assert q_circ is not None
    assert len(q_circ.data) == 4
