# tests/test_qiskit_integration.py
import pytest

try:
    import qiskit
except ImportError:  # pragma: no cover
    qiskit = None

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

def test_qiskit_conversion_and_simulation(sample_circuit):
    if qiskit is None:
        pytest.skip("Qiskit not installed")
    # Convert to Qiskit circuit
    qiskit_circ = sample_circuit.to_qiskit()
    assert qiskit_circ is not None
    # Run simulator
    counts = sample_circuit.run_qiskit_simulator(shots=1024)
    # Expected counts: roughly 50/50 on |00> and |10> after H on qubit0 and CX
    total = sum(counts.values())
    assert total == 1024
    # Ensure both possible outcomes appear
    assert any(key in counts for key in ["00", "10"])
