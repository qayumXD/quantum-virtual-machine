"""
Intermediate Representation (IR) module for hardware-agnostic quantum circuits.

This module defines data structures to represent quantum circuits in a way
that is independent of any specific quantum hardware or framework.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class QuantumGate:
    """
    Represents a single quantum gate in the IR.
    
    Attributes:
        gate_type: Type of gate (e.g., 'H', 'CX', 'RZ')
        qubits: List of qubit indices this gate acts on
        params: Optional parameters for parametric gates (e.g., rotation angles)
    
    Example:
        >>> # Hadamard gate on qubit 0
        >>> h_gate = QuantumGate(gate_type='H', qubits=[0], params=[])
        >>> 
        >>> # CNOT gate with control=0, target=1
        >>> cx_gate = QuantumGate(gate_type='CX', qubits=[0, 1], params=[])
        >>> 
        >>> # RZ rotation by pi/4 on qubit 0
        >>> import math
        >>> rz_gate = QuantumGate(gate_type='RZ', qubits=[0], params=[math.pi/4])
    """
    gate_type: str
    qubits: List[int]
    params: List[float] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert gate to dictionary representation."""
        return {
            'type': self.gate_type,
            'qubits': self.qubits,
            'params': self.params
        }


class QuantumCircuitIR:
    """
    Hardware-agnostic intermediate representation of a quantum circuit.
    
    This class stores a quantum circuit as a sequence of gates and measurements,
    independent of the original framework (Qiskit, Cirq, etc.) or target hardware.
    
    Attributes:
        num_qubits: Number of qubits in the circuit
        gates: List of quantum gates in order of application
        measurements: List of measurement operations (qubit -> classical bit mapping)
    
    Example:
        >>> # Create IR for a Bell state circuit
        >>> ir = QuantumCircuitIR(num_qubits=2)
        >>> ir.add_gate(QuantumGate('H', [0], []))
        >>> ir.add_gate(QuantumGate('CX', [0, 1], []))
        >>> ir.add_measurement(0, 0)
        >>> ir.add_measurement(1, 1)
        >>> print(ir.num_qubits)  # Output: 2
        >>> print(len(ir.gates))  # Output: 2
    """
    
    def __init__(self, num_qubits: int):
        """
        Initialize a quantum circuit IR.
        
        Args:
            num_qubits: Number of qubits in the circuit
        """
        self.num_qubits = num_qubits
        self.gates: List[QuantumGate] = []
        self.measurements: List[Dict[str, int]] = []
    
    def add_gate(self, gate: QuantumGate) -> None:
        """
        Add a quantum gate to the circuit.
        
        Args:
            gate: QuantumGate object to add
        """
        self.gates.append(gate)
    
    def add_measurement(self, qubit: int, classical_bit: int) -> None:
        """
        Add a measurement operation.
        
        Args:
            qubit: Index of qubit to measure
            classical_bit: Index of classical bit to store result
        """
        self.measurements.append({
            'qubit': qubit,
            'classical_bit': classical_bit
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the IR to a dictionary representation.
        
        Returns:
            Dictionary containing the full circuit specification
        """
        return {
            'num_qubits': self.num_qubits,
            'gates': [gate.to_dict() for gate in self.gates],
            'measurements': self.measurements
        }
    
    def __repr__(self) -> str:
        """String representation of the IR."""
        return f"QuantumCircuitIR(qubits={self.num_qubits}, gates={len(self.gates)}, measurements={len(self.measurements)})"