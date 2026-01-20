"""
Parser module for converting Qiskit and Cirq circuits to IR.

This module provides parsers that extract quantum circuit information
from framework-specific representations (Qiskit, Cirq) and convert them
to a hardware-agnostic intermediate representation (IR).
"""

from typing import Dict, List, Any

try:
    from qiskit import QuantumCircuit
    from qiskit.circuit import Instruction
    QISKIT_AVAILABLE = True
except ImportError:
    QuantumCircuit = None
    Instruction = None
    QISKIT_AVAILABLE = False

from .ir import QuantumCircuitIR, QuantumGate


class QiskitParser:
    """
    Parser for Qiskit quantum circuits.
    
    Converts Qiskit QuantumCircuit objects into the QVM's intermediate
    representation format. Supports common single and multi-qubit gates.
    
    Example:
        >>> from qiskit import QuantumCircuit
        >>> qc = QuantumCircuit(2)
        >>> qc.h(0)  # Hadamard gate
        >>> qc.cx(0, 1)  # CNOT gate
        >>> 
        >>> parser = QiskitParser()
        >>> ir = parser.parse(qc)
        >>> print(ir.num_qubits)  # Output: 2
    """
    
    def __init__(self):
        """Initialize the Qiskit parser."""
        self.supported_gates = {
            'h', 'x', 'y', 'z',  # Single-qubit Pauli and Hadamard
            'cx', 'cnot',         # Two-qubit CNOT
            'cz',                 # Two-qubit CZ
            'rx', 'ry', 'rz',     # Parametric rotation gates
            'measure'             # Measurement
        }
    
    def parse(self, circuit) -> QuantumCircuitIR:
        """
        Parse a Qiskit QuantumCircuit into IR format.
        
        Args:
            circuit: Qiskit QuantumCircuit object to parse
            
        Returns:
            QuantumCircuitIR object containing the parsed circuit
            
        Raises:
            ValueError: If circuit contains unsupported gates
            ImportError: If Qiskit is not installed
        """
        if not QISKIT_AVAILABLE:
            raise ImportError("Qiskit is not installed. Install with: pip install qiskit")
        
        ir = QuantumCircuitIR(num_qubits=circuit.num_qubits)
        
        # Iterate through all operations in the circuit
        for instruction, qubits, clbits in circuit.data:
            gate_name = instruction.name.lower()
            
            # Handle measurement separately
            if gate_name == 'measure':
                qubit_idx = circuit.qubits.index(qubits[0])
                clbit_idx = circuit.clbits.index(clbits[0])
                ir.add_measurement(qubit_idx, clbit_idx)
                continue
            
            # Check if gate is supported
            if gate_name not in self.supported_gates:
                raise ValueError(f"Unsupported gate: {gate_name}")
            
            # Extract qubit indices
            qubit_indices = [circuit.qubits.index(q) for q in qubits]
            
            # Extract parameters (for rotation gates)
            params = list(instruction.params) if instruction.params else []
            
            # Create gate and add to IR
            gate = QuantumGate(
                gate_type=self._normalize_gate_name(gate_name),
                qubits=qubit_indices,
                params=params
            )
            ir.add_gate(gate)
        
        return ir
    
    def _normalize_gate_name(self, gate_name: str) -> str:
        """
        Normalize gate names to standard format.
        
        Maps Qiskit-specific gate names to our standard IR names.
        For example, 'cnot' -> 'CX', 'h' -> 'H'
        
        What each gate does:
        - H (Hadamard): Creates superposition |0⟩ → (|0⟩ + |1⟩)/√2
        - X (Pauli-X): Quantum NOT gate, flips |0⟩ ↔ |1⟩
        - Y (Pauli-Y): Rotation around Y-axis + phase flip
        - Z (Pauli-Z): Phase flip on |1⟩ state
        - CX (CNOT): Controlled-NOT, creates entanglement
        - CZ: Controlled-Z gate
        - RX/RY/RZ: Parametric rotation gates (angle θ)
        """
        name_mapping = {
            'h': 'H',      # Hadamard: Creates superposition
            'x': 'X',      # Pauli-X: Quantum NOT gate
            'y': 'Y',      # Pauli-Y: Rotation + phase flip
            'z': 'Z',      # Pauli-Z: Phase flip
            'cx': 'CX',    # CNOT: Controlled-NOT (entanglement!)
            'cnot': 'CX',  # Alternative name for CNOT
            'cz': 'CZ',    # Controlled-Z
            'rx': 'RX',    # Rotation around X-axis
            'ry': 'RY',    # Rotation around Y-axis
            'rz': 'RZ',    # Rotation around Z-axis
        }
        return name_mapping.get(gate_name, gate_name.upper())


class CirqParser:
    """
    Parser for Cirq quantum circuits.
    
    TODO: Implement Cirq circuit parsing in Phase 1.
    """
    
    def __init__(self):
        """Initialize the Cirq parser."""
        pass
    
    def parse(self, circuit):
        """
        Parse a Cirq circuit into IR format.
        
        Args:
            circuit: Cirq Circuit object to parse
            
        Returns:
            QuantumCircuitIR object containing the parsed circuit
        """
        raise NotImplementedError("CirqParser will be implemented in Phase 1")