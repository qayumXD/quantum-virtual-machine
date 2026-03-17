# src/qvm/simulator.py

"""
Statevector simulator with integrated classical memory, conditional logic, 
and advanced control flow (labels/jumps).
"""

import numpy as np
from src.qvm.ir import QuantumCircuit

class Simulator:
    def __init__(self):
        # Basis gate matrices
        self.H = (1/np.sqrt(2)) * np.array([[1, 1], [1, -1]], dtype=complex)
        self.X = np.array([[0, 1], [1, 0]], dtype=complex)
        self.Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
        self.Z = np.array([[1, 0], [0, -1]], dtype=complex)
        self.I = np.array([[1, 0], [0, 1]], dtype=complex)
        self.SX = 0.5 * np.array([[1+1j, 1-1j], [1-1j, 1+1j]], dtype=complex)
        self.S = np.array([[1, 0], [0, 1j]], dtype=complex)
        self.T = np.array([[1, 0], [0, np.exp(1j * np.pi / 4)]], dtype=complex)

    def _get_gate_matrix(self, name: str, params: list) -> np.ndarray:
        if name == "h": return self.H
        if name == "x": return self.X
        if name == "y": return self.Y
        if name == "z": return self.Z
        if name == "id": return self.I
        if name == "sx": return self.SX
        if name == "sxdg": return self.SX.conj().T
        if name == "s": return self.S
        if name == "sdg": return self.S.conj().T
        if name == "t": return self.T
        if name == "tdg": return self.T.conj().T
        
        angle = params[0] if params else 0
        if name == "rx": return np.array([[np.cos(angle/2), -1j*np.sin(angle/2)], [-1j*np.sin(angle/2), np.cos(angle/2)]])
        if name == "ry": return np.array([[np.cos(angle/2), -np.sin(angle/2)], [np.sin(angle/2), np.cos(angle/2)]])
        if name == "rz" or name == "p": return np.array([[1, 0], [0, np.exp(1j*angle)]])
        raise ValueError(f"Unknown gate: {name}")

    def simulate(self, circuit: QuantumCircuit, seed: int = None, max_ops: int = 10000) -> tuple[np.ndarray, dict]:
        num_qubits = circuit.num_qubits
        state = np.zeros(2**num_qubits, dtype=complex)
        state[0] = 1.0
        classical_memory = {name: np.zeros(size, dtype=int) for name, size in circuit.classical_registers.items()}
        rng = np.random.default_rng(seed)

        # Pre-scan for labels
        labels = {}
        for idx, op in enumerate(circuit.operations):
            if op["name"] == "label":
                labels[op["label"]] = idx

        # Execution loop with Program Counter (PC)
        pc = 0
        ops_executed = 0
        while pc < len(circuit.operations):
            if ops_executed > max_ops:
                raise RuntimeError(f"Exceeded maximum operations limit ({max_ops}). Potential infinite loop.")
            
            op = circuit.operations[pc]
            ops_executed += 1
            
            try:
                # 1. Handle Control Flow
                if op["name"] == "label":
                    pc += 1
                    continue
                
                if op["name"] == "jump":
                    should_jump = True
                    if op["condition"]:
                        cond = op["condition"]
                        if classical_memory[cond["register"]][cond["index"]] != cond["value"]:
                            should_jump = False
                    
                    if should_jump:
                        pc = labels[op["jump_to"]]
                    else:
                        pc += 1
                    continue

                # 2. Handle Conditional Gates
                if op["condition"]:
                    cond = op["condition"]
                    if classical_memory[cond["register"]][cond["index"]] != cond["value"]:
                        pc += 1
                        continue

                # 3. Handle Quantum Operations
                name, qubits, params = op["name"], op["qubits"], op["params"]
                
                if name in ["h", "x", "y", "z", "rx", "ry", "rz", "p", "id", "sx", "sxdg", "s", "sdg", "t", "tdg"]:
                    if not qubits:
                        raise ValueError(f"Gate {name} requires a target qubit.")
                    gate_mat = self._get_gate_matrix(name, params)
                    state = self._apply_single_qubit_gate(state, gate_mat, qubits[0], num_qubits)
                elif name == "cx":
                    if len(qubits) < 2:
                        raise ValueError("CX gate requires two qubits (control and target).")
                    state = self._apply_cnot_gate(state, qubits[0], qubits[1], num_qubits)
                elif name == "swap":
                    if len(qubits) < 2:
                        raise ValueError("SWAP gate requires two qubits.")
                    state = self._apply_swap_gate(state, qubits[0], qubits[1], num_qubits)
                elif name in ["ccx", "toffoli"]:
                    if len(qubits) < 3:
                        raise ValueError("CCX gate requires three qubits.")
                    state = self._apply_ccx_gate(state, qubits[0], qubits[1], qubits[2], num_qubits)
                elif name == "measure":
                    if not qubits:
                        raise ValueError("Measure requires a target qubit.")
                    bit_str, state = self._measure_and_collapse(state, qubits, num_qubits, rng)
                    if op["target_bit"]:
                        reg_name, reg_idx = op["target_bit"]
                        classical_memory[reg_name][reg_idx] = int(bit_str[0])
                elif name == "delay":
                    pass
                elif name == "classical_op":
                    self._execute_classical_op(op["classical_op"], classical_memory)
                
                pc += 1
            except Exception as e:
                print(f"DEBUG: Error at PC {pc}, Op: {op}")
                raise e

        return state, classical_memory

    def _execute_classical_op(self, cop, mem):
        op = cop["op"]
        target_reg, target_idx = cop["target"]
        args = cop["args"]
        
        vals = []
        for arg in args:
            if isinstance(arg, tuple): # (reg, idx)
                vals.append(mem[arg[0]][arg[1]])
            else: # Literal INT
                vals.append(arg)
        
        if op == "=":   res = vals[0]
        elif op == "&": res = vals[0] & vals[1]
        elif op == "|": res = vals[0] | vals[1]
        elif op == "^": res = vals[0] ^ vals[1]
        elif op == "~": res = ~vals[0] & 1
        else: raise ValueError(f"Unknown classical operator: {op}")
        
        mem[target_reg][target_idx] = res

    def _apply_single_qubit_gate(self, state, gate, target, n):
        op_list = [self.I] * n
        op_list[n - 1 - target] = gate
        full_op = op_list[0]
        for i in range(1, n):
            full_op = np.kron(full_op, op_list[i])
        return full_op @ state

    def _apply_cnot_gate(self, state, ctrl, target, n):
        indices = np.arange(2**n)
        mask = (indices >> ctrl) & 1 == 1
        perm = indices.copy()
        perm[mask] = indices[mask] ^ (1 << target)
        return state[perm]

    def _apply_swap_gate(self, state, q1, q2, n):
        indices = np.arange(2**n)
        diff = ((indices >> q1) & 1) != ((indices >> q2) & 1)
        perm = indices.copy()
        perm[diff] = indices[diff] ^ ((1 << q1) | (1 << q2))
        return state[perm]

    def _apply_ccx_gate(self, state, c1, c2, target, n):
        indices = np.arange(2**n)
        mask = ((indices >> c1) & 1 == 1) & ((indices >> c2) & 1 == 1)
        perm = indices.copy()
        perm[mask] = indices[mask] ^ (1 << target)
        return state[perm]

    def _measure_and_collapse(self, state, qubits, n, rng):
        q = qubits[0]
        indices = np.arange(2**n)
        prob_0 = np.sum(np.abs(state[((indices >> q) & 1) == 0])**2)
        outcome = 0 if rng.random() < prob_0 else 1
        mask = ((indices >> q) & 1) == outcome
        new_state = np.zeros_like(state)
        new_state[mask] = state[mask]
        norm = np.linalg.norm(new_state)
        if norm > 0:
            new_state /= norm
        return str(outcome), new_state
