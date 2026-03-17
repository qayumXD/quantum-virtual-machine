# src/qvm/ir.py

"""
Intermediate Representation (IR) for Quantum Circuits.
Extends the IR to support OpenQASM 3.0 classical registers and conditional operations.
"""

from typing import List, Dict, Optional, Any

class QuantumCircuit:
    def __init__(self, num_qubits: int):
        if not isinstance(num_qubits, int) or num_qubits <= 0:
            raise ValueError("Number of qubits must be a positive integer.")
        self.num_qubits = num_qubits
        self.operations = []  # List of dictionaries: gate, qubits, params, condition, target_bit
        self.classical_registers: Dict[str, int] = {}  # name -> size

    def add_classical_register(self, name: str, size: int):
        """Declares a classical bit register."""
        if name in self.classical_registers:
            raise ValueError(f"Classical register '{name}' already exists.")
        self.classical_registers[name] = size

    def add_operation(self, gate_name: str, qubits: list, params: list = None, condition: dict = None, target_bit: tuple = None, duration: str = None, label: str = None, jump_to: str = None, classical_op: dict = None):
        """
        Adds a quantum or classical operation to the circuit.

        Args:
            gate_name (str): The name (e.g., "h", "measure", "classical_op").
            qubits (list): Target quantum bits.
            params (list, optional): Gate parameters.
            condition (dict, optional): {"register": str, "index": int, "value": int}
            target_bit (tuple, optional): (register_name, index) for results.
            duration (str, optional): Timing string.
            label (str, optional): Label for jumps.
            jump_to (str, optional): Target label for jumps.
            classical_op (dict, optional): {"op": str, "target": tuple, "args": list}
        """
        if condition:
            reg = condition.get("register")
            if reg not in self.classical_registers:
                raise ValueError(f"Unknown classical register in condition: {reg}")
            if not (0 <= condition.get("index", 0) < self.classical_registers[reg]):
                raise ValueError(f"Index out of bounds for classical register '{reg}'")

        operation = {
            "name": gate_name,
            "qubits": qubits if qubits is not None else [],
            "params": params if params is not None else [],
            "condition": condition,
            "target_bit": target_bit,
            "duration": duration,
            "label": label,
            "jump_to": jump_to,
            "classical_op": classical_op
        }
        self.operations.append(operation)

    def __str__(self):
        s = f"QuantumCircuit(num_qubits={self.num_qubits}, registers={self.classical_registers})\n"
        for op in self.operations:
            if op["name"] == "label":
                s += f"  LABEL {op['label']}:\n"
                continue
            if op["name"] == "jump":
                cond_str = f" IF {op['condition']}" if op['condition'] else ""
                s += f"  JUMP {op['jump_to']}{cond_str}\n"
                continue
            if op["name"] == "classical_op":
                s += f"  CLASSICAL {op['classical_op']['target']} = {op['classical_op']['op']} {op['classical_op']['args']}\n"
                continue
            
            cond_str = f" IF {op['condition']}" if op['condition'] else ""
            target_str = f" -> {op['target_bit']}" if op['target_bit'] else ""
            dur_str = f" [{op['duration']}]" if op['duration'] else ""
            s += f"  {op['name']}{dur_str} {op['qubits']}{cond_str}{target_str}\n"
        return s
