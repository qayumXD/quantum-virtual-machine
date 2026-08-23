# src/qvm/decomposer.py

"""
Decomposes complex quantum gates into a sequence of simpler, native gates.
Updated to preserve OpenQASM 3.0 classical metadata and control flow.
"""

from qvm.ir import QuantumCircuit
from qvm.exceptions import UnsupportedGateError
from qvm import synthesis

# Multi-controlled macros lowered via qvm.synthesis
_MACROS = {"mcx", "mcz", "mcp", "mcry", "mcrz", "mcrx"}

class Decomposer:
    """
    A simple decomposer that can break down specific complex gates.
    """
    def __init__(self, native_gates: set):
        self.native_gates = native_gates

    def decompose_operation(self, op: dict) -> list:
        """
        Decomposes a single gate operation if it's not in the native gate set.
        Returns a list of simpler operations.
        """
        gate_name = op["name"]
        
        # If it's a non-gate op (classical, label, etc.), it's considered native
        if gate_name in ["classical_op", "label", "jump", "delay", "measure", "barrier"]:
            return [op]

        if gate_name in _MACROS:
            from qvm.parameter import resolve_param
            params = [float(resolve_param(p)) for p in (op.get("params") or [])]
            return [dict(sub, condition=op.get("condition"), target_bit=op.get("target_bit"))
                    for sub in synthesis.lower_macro(gate_name, op["qubits"], params)]

        if gate_name in self.native_gates:
            return [op]

        if gate_name == "toffoli" or gate_name == "ccx":
            return self._decompose_toffoli(op)
        
        raise UnsupportedGateError(f"No decomposition rule available for gate: {gate_name}")

    def _decompose_toffoli(self, op: dict) -> list:
        qubits = op["qubits"]
        if len(qubits) != 3:
            raise ValueError("Toffoli gate must act on 3 qubits.")
        c1, c2, t = qubits[0], qubits[1], qubits[2]
        
        import numpy as np
        pi_4 = np.pi / 4

        # Preserve condition if the CCX was conditional
        cond = op.get("condition")

        decomposition = [
            {"name": "h", "qubits": [t], "params": [], "condition": cond},
            {"name": "cx", "qubits": [c2, t], "params": [], "condition": cond},
            {"name": "rz", "qubits": [t], "params": [-pi_4], "condition": cond},
            {"name": "cx", "qubits": [c1, t], "params": [], "condition": cond},
            {"name": "rz", "qubits": [t], "params": [pi_4], "condition": cond},
            {"name": "cx", "qubits": [c2, t], "params": [], "condition": cond},
            {"name": "rz", "qubits": [t], "params": [-pi_4], "condition": cond},
            {"name": "cx", "qubits": [c1, t], "params": [], "condition": cond},
            {"name": "rz", "qubits": [c2], "params": [pi_4], "condition": cond},
            {"name": "rz", "qubits": [t], "params": [pi_4], "condition": cond},
            {"name": "h", "qubits": [t], "params": [], "condition": cond},
            {"name": "cx", "qubits": [c1, c2], "params": [], "condition": cond},
            {"name": "rz", "qubits": [c1], "params": [pi_4], "condition": cond},
            {"name": "rz", "qubits": [c2], "params": [-pi_4], "condition": cond},
            {"name": "cx", "qubits": [c1, c2], "params": [], "condition": cond},
        ]
        return decomposition

    def decompose_circuit(self, circuit: QuantumCircuit) -> QuantumCircuit:
        """
        Decomposes all non-native gates in a circuit.
        """
        decomposed_circuit = QuantumCircuit(circuit.num_qubits)
        decomposed_circuit.classical_registers = circuit.classical_registers.copy()
        
        for op in circuit.operations:
            decomposed_ops = self.decompose_operation(op)
            for new_op in decomposed_ops:
                decomposed_circuit.add_operation(
                    new_op["name"], 
                    new_op.get("qubits", []), 
                    params=new_op.get("params", []),
                    condition=new_op.get("condition"),
                    target_bit=new_op.get("target_bit"),
                    duration=new_op.get("duration"),
                    label=new_op.get("label"),
                    jump_to=new_op.get("jump_to"),
                    classical_op=new_op.get("classical_op")
                )
        return decomposed_circuit
