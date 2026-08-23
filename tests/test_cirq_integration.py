# tests/test_cirq_integration.py
import pytest

try:
    import cirq
except ImportError:  # pragma: no cover
    cirq = None

from qvm.ir import QuantumCircuit

@pytest.fixture
def sample_circuit():
    qc = QuantumCircuit(2)
    qc.add_classical_register('c', 2)
    qc.add_operation('h', [0])
    qc.add_operation('cx', [0, 1])
    qc.add_operation('measure', [0], target_bit=('c', 0))
    qc.add_operation('measure', [1], target_bit=('c', 1))
    return qc

def test_cirq_conversion_and_simulation(sample_circuit):
    if cirq is None:
        pytest.skip("Cirq not installed")
    # Convert to Cirq circuit
    cirq_circ = sample_circuit.to_cirq()
    assert cirq_circ is not None
    # Run simulator
    counts = sample_circuit.run_cirq_simulator(repetitions=1024)
    total = sum(counts.values())
    assert total == 1024
    # Verify outcomes include both possible measurement results
    assert any(key in counts for key in ["00", "10"])
