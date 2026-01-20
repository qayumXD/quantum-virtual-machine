"""
Unit tests for the parser module.

Tests QiskitParser and CirqParser functionality with various quantum circuits.
"""

import pytest
import math

try:
    from qiskit import QuantumCircuit
    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False

from src.parser import QiskitParser
from src.ir import QuantumCircuitIR, QuantumGate


@pytest.mark.skipif(not QISKIT_AVAILABLE, reason="Qiskit not installed")
class TestQiskitParser:
    """Test cases for QiskitParser."""
    
    def test_bell_state_parsing(self):
        """Test parsing a Bell state circuit."""
        # Create Bell state: H(0), CNOT(0,1)
        qc = QuantumCircuit(2, 2)
        qc.h(0)
        qc.cx(0, 1)
        qc.measure([0, 1], [0, 1])
        
        # Parse the circuit
        parser = QiskitParser()
        ir = parser.parse(qc)
        
        # Verify IR structure
        assert ir.num_qubits == 2
        assert len(ir.gates) == 2
        assert len(ir.measurements) == 2
        
        # Verify gates
        assert ir.gates[0].gate_type == 'H'
        assert ir.gates[0].qubits == [0]
        
        assert ir.gates[1].gate_type == 'CX'
        assert ir.gates[1].qubits == [0, 1]
        
        # Verify measurements
        assert ir.measurements[0] == {'qubit': 0, 'classical_bit': 0}
        assert ir.measurements[1] == {'qubit': 1, 'classical_bit': 1}
    
    def test_single_qubit_gates(self):
        """Test parsing single-qubit Pauli gates."""
        qc = QuantumCircuit(1)
        qc.x(0)  # X gate
        qc.y(0)  # Y gate
        qc.z(0)  # Z gate
        
        parser = QiskitParser()
        ir = parser.parse(qc)
        
        assert len(ir.gates) == 3
        assert ir.gates[0].gate_type == 'X'
        assert ir.gates[1].gate_type == 'Y'
        assert ir.gates[2].gate_type == 'Z'
    
    def test_parametric_gates(self):
        """Test parsing parametric rotation gates."""
        angle = math.pi / 4
        qc = QuantumCircuit(1)
        qc.rz(angle, 0)
        
        parser = QiskitParser()
        ir = parser.parse(qc)
        
        assert len(ir.gates) == 1
        assert ir.gates[0].gate_type == 'RZ'
        assert ir.gates[0].qubits == [0]
        assert len(ir.gates[0].params) == 1
        assert abs(ir.gates[0].params[0] - angle) < 1e-10
    
    def test_empty_circuit(self):
        """Test parsing an empty circuit."""
        qc = QuantumCircuit(3)
        
        parser = QiskitParser()
        ir = parser.parse(qc)
        
        assert ir.num_qubits == 3
        assert len(ir.gates) == 0
        assert len(ir.measurements) == 0
    
    def test_unsupported_gate(self):
        """Test that unsupported gates raise ValueError."""
        # Create a circuit with a multi-controlled gate (not yet supported)
        qc = QuantumCircuit(3)
        qc.h(0)
        qc.ccx(0, 1, 2)  # Toffoli gate - not in supported_gates
        
        parser = QiskitParser()
        
        # Should raise ValueError for unsupported gate
        with pytest.raises(ValueError, match="Unsupported gate"):
            ir = parser.parse(qc)
    
    def test_ir_to_dict(self):
        """Test IR serialization to dictionary."""
        qc = QuantumCircuit(2, 2)
        qc.h(0)
        qc.cx(0, 1)
        qc.measure([0, 1], [0, 1])
        
        parser = QiskitParser()
        ir = parser.parse(qc)
        
        ir_dict = ir.to_dict()
        
        assert ir_dict['num_qubits'] == 2
        assert len(ir_dict['gates']) == 2
        assert len(ir_dict['measurements']) == 2
        assert ir_dict['gates'][0]['type'] == 'H'
        assert ir_dict['gates'][1]['type'] == 'CX'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])