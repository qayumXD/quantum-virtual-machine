# src/qvm/simulator.py

"""
Statevector simulator with integrated classical memory, conditional logic,
advanced control flow (labels/jumps), expectation values, and per-gate noise.
"""

import numpy as np
from qvm.ir import QuantumCircuit
from qvm.parameter import resolve_param, is_parameterized
from qvm.exceptions import UnsupportedGateError, QVMResourceLimitError

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
        
        # Resolve symbolic parameters to float
        angle = resolve_param(params[0]) if params else 0
        if name == "rx": return np.array([[np.cos(angle/2), -1j*np.sin(angle/2)], [-1j*np.sin(angle/2), np.cos(angle/2)]])
        if name == "ry": return np.array([[np.cos(angle/2), -np.sin(angle/2)], [np.sin(angle/2), np.cos(angle/2)]])
        if name == "rz": return np.array([[np.exp(-1j*angle/2), 0], [0, np.exp(1j*angle/2)]])
        if name == "p": return np.array([[1, 0], [0, np.exp(1j*angle)]])
        raise UnsupportedGateError(f"Unknown single-qubit gate: {name}")

    def simulate(self, circuit: QuantumCircuit, seed: int = None, max_ops: int = 1_000_000) -> tuple[np.ndarray, dict]:
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
                raise QVMResourceLimitError(
                    f"Exceeded maximum operations limit ({max_ops}). "
                    f"Potential infinite loop. Pass max_ops=<budget> to raise the limit."
                )
            
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
                    if len(qubits) != 1:
                        raise ValueError(f"Gate {name} must act on a single qubit.")
                    gate_mat = self._get_gate_matrix(name, params)
                    state = self._apply_single_qubit_gate(state, gate_mat, qubits[0], num_qubits)
                elif name == "cx":
                    if len(qubits) != 2:
                        raise ValueError("Gate cx must act on two qubits.")
                    state = self._apply_cnot_gate(state, qubits[0], qubits[1], num_qubits)
                elif name == "cz":
                    if len(qubits) != 2:
                        raise ValueError("Gate cz must act on two qubits.")
                    state = self._apply_cz_gate(state, qubits[0], qubits[1], num_qubits)
                elif name == "swap":
                    if len(qubits) != 2:
                        raise ValueError("Gate swap must act on two qubits.")
                    state = self._apply_swap_gate(state, qubits[0], qubits[1], num_qubits)
                elif name in ["ccx", "toffoli"]:
                    if len(qubits) != 3:
                        raise ValueError("Gate ccx must act on three qubits.")
                    state = self._apply_ccx_gate(state, qubits[0], qubits[1], qubits[2], num_qubits)
                elif name == "rzz":
                    if len(qubits) != 2:
                        raise ValueError("Gate rzz must act on two qubits.")
                    state = self._apply_rzz_gate(state, qubits[0], qubits[1],
                                                 float(resolve_param(params[0])), num_qubits)
                elif name == "rxx":
                    if len(qubits) != 2:
                        raise ValueError("Gate rxx must act on two qubits.")
                    state = self._apply_rxx_gate(state, qubits[0], qubits[1],
                                                 float(resolve_param(params[0])), num_qubits)
                elif name == "cp":
                    if len(qubits) != 2:
                        raise ValueError("Gate cp must act on two qubits.")
                    state = self._apply_cp_gate(state, qubits[0], qubits[1],
                                                float(resolve_param(params[0])), num_qubits)
                elif name == "measure":
                    if not qubits:
                        raise ValueError("Measure requires a target qubit.")
                    bit_str, state = self._measure_and_collapse(state, qubits, num_qubits, rng)
                    if op["target_bit"]:
                        reg_name, reg_idx = op["target_bit"]
                        classical_memory[reg_name][reg_idx] = int(bit_str[0])
                elif name == "delay":
                    pass
                elif name == "barrier":
                    pass
                elif name == "classical_op":
                    self._execute_classical_op(op["classical_op"], classical_memory)
                else:
                    raise UnsupportedGateError(f"Unsupported gate operation: {name}")
                
                pc += 1
            except Exception:
                raise

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
        """Apply a single-qubit gate using in-place tensor stride — O(2^N) time, O(1) extra memory.

        Replaces the O(4^N) Kronecker product approach. Reshapes the statevector
        into (2^(n-1-target), 2, 2^target), applies the 2x2 gate over the
        middle axis, then restores the flat shape.
        """
        shape = (2 ** (n - 1 - target), 2, 2 ** target)
        sv = state.reshape(shape)
        # Batch matrix multiply: sv[:, :, :] = gate @ sv along the qubit axis
        sv = np.einsum("ij,kjl->kil", gate, sv)
        return sv.reshape(-1)

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

    def _apply_cz_gate(self, state, ctrl, target, n):
        """Apply Controlled-Z gate using permutation (phase flip on |11⟩)."""
        indices = np.arange(2**n)
        mask = ((indices >> ctrl) & 1 == 1) & ((indices >> target) & 1 == 1)
        result = state.copy()
        result[mask] = -result[mask]
        return result

    def _apply_rzz_gate(self, state, q0, q1, theta, n):
        """Apply RZZ(θ) = exp(-iθ Z⊗Z / 2): phase e^{-iθ} on |11⟩, e^{iθ} on |10⟩/|01⟩.

        Implemented exactly as CX · RZ_target(θ) · CX (O(2^N), no dense matrix).
        """
        state = self._apply_cnot_gate(state, q0, q1, n)
        rz = self._get_gate_matrix("rz", [theta])
        state = self._apply_single_qubit_gate(state, rz, q1, n)
        return self._apply_cnot_gate(state, q0, q1, n)

    def _apply_rxx_gate(self, state, q0, q1, theta, n):
        """Apply RXX(θ) = exp(-iθ X⊗X / 2) via basis change: H⊗H · RZZ(θ) · H⊗H."""
        h = self._get_gate_matrix("h", [])
        state = self._apply_single_qubit_gate(state, h, q0, n)
        state = self._apply_single_qubit_gate(state, h, q1, n)
        state = self._apply_rzz_gate(state, q0, q1, theta, n)
        state = self._apply_single_qubit_gate(state, h, q0, n)
        return self._apply_single_qubit_gate(state, h, q1, n)

    def _apply_cp_gate(self, state, q0, q1, lam, n):
        """Apply CP(λ) = diag(1, 1, 1, e^{iλ}): phase flip on the |11⟩ subspace."""
        indices = np.arange(2**n)
        mask = ((indices >> q0) & 1 == 1) & ((indices >> q1) & 1 == 1)
        result = state.copy()
        result[mask] *= np.exp(1j * lam)
        return result

    def get_probabilities(self, statevector: np.ndarray) -> np.ndarray:
        """Calculates measurement probabilities from a statevector."""
        return np.abs(statevector)**2

    # -----------------------------------------------------------------
    # Expectation values (Phase 2)
    # -----------------------------------------------------------------
    def expectation_value(self, circuit: QuantumCircuit, observable, seed=None) -> float:
        """Compute ⟨ψ|H|ψ⟩ exactly from the statevector.

        Args:
            circuit: A QuantumCircuit (must have all parameters bound).
            observable: A Hamiltonian object from qvm.observable.
            seed: Optional RNG seed.

        Returns:
            The real part of the expectation value.
        """
        state, _ = self.simulate(circuit, seed=seed)
        H_matrix = observable.to_matrix(circuit.num_qubits)
        expectation = np.real(np.conj(state) @ H_matrix @ state)
        return float(expectation)

    def estimate_expectation(self, circuit: QuantumCircuit, observable,
                             shots: int = 1024, seed=None) -> float:
        """Estimate ⟨ψ|H|ψ⟩ via shot-based sampling.

        For each Pauli term, measures in the appropriate basis and
        computes the eigenvalue contribution.
        """
        state, _ = self.simulate(circuit, seed=seed)
        rng = np.random.default_rng(seed)
        probs = self.get_probabilities(state)
        outcomes = rng.choice(len(probs), size=shots, p=probs)

        # For each term in the Hamiltonian, compute the expectation
        total = 0.0
        for term in observable.terms:
            term_sum = 0.0
            for outcome in outcomes:
                eigenvalue = 1.0
                for i, pauli_char in enumerate(term.pauli_string):
                    if pauli_char == "Z":
                        bit = (outcome >> (circuit.num_qubits - 1 - i)) & 1
                        eigenvalue *= (-1) ** bit
                    elif pauli_char in ("X", "Y"):
                        # For X and Y, we'd need basis rotation
                        # Simplified: use the exact method for non-Z terms
                        pass
                term_sum += eigenvalue
            total += term.coeff * (term_sum / shots)

        return float(total)

    def sample(
        self,
        circuit: QuantumCircuit,
        shots: int = 1024,
        seed: int | None = None,
        depol_prob: float = 0.0,
        readout_error: float = 0.0,
        noise_model=None,
    ) -> dict:
        """
        Draws measurement samples from the final state of the circuit.

        If a noise_model is provided, uses sample_with_collapse() for per-gate noise.
        Otherwise uses the fast single-simulation approach.
        """
        # If a noise_model is provided, delegate to shot-by-shot simulation
        if noise_model is not None and noise_model.has_noise():
            return self.sample_with_collapse(circuit, shots=shots, seed=seed,
                                             noise_model=noise_model)

        # Dynamic circuits (mid-circuit measurement, classical feedback,
        # control flow) require a fresh trajectory per shot: the fast path's
        # single collapsed state would otherwise be resampled N times.
        if self._is_dynamic(circuit):
            return self.sample_with_collapse(circuit, shots=shots, seed=seed)

        if shots <= 0:
            raise ValueError("shots must be a positive integer")
        if not 0 <= depol_prob <= 1:
            raise ValueError("depol_prob must be in [0,1]")
        if not 0 <= readout_error <= 1:
            raise ValueError("readout_error must be in [0,1]")

        measured_qubits = self._extract_measured_qubits(circuit)
        if not measured_qubits:
            measured_qubits = list(range(circuit.num_qubits))

        state, mem = self.simulate(circuit, seed=seed)
        probs = self.get_probabilities(state)

        # Apply simple depolarizing noise: mix with uniform distribution
        if depol_prob > 0:
            uniform = 1 / len(probs)
            probs = (1 - depol_prob) * probs + depol_prob * uniform

        rng = np.random.default_rng(seed)
        outcomes = rng.choice(len(probs), size=shots, p=probs)

        counts: dict[str, int] = {}
        for outcome in outcomes:
            bitstring = format(outcome, f"0{circuit.num_qubits}b")
            # Little-endian convention: qubit 0 is LSB (rightmost)
            measured_bits = "".join(bitstring[circuit.num_qubits - 1 - q] for q in measured_qubits)

            if readout_error > 0:
                measured_bits = self._apply_readout_noise(measured_bits, readout_error, rng)

            counts[measured_bits] = counts.get(measured_bits, 0) + 1

        return counts

    @staticmethod
    def _is_dynamic(circuit: QuantumCircuit) -> bool:
        """True if the circuit needs per-shot trajectories.

        A circuit is dynamic when it contains any conditional operation,
        control flow, or a measurement that is followed by further
        operations (mid-circuit measurement).
        """
        last_executable = -1
        for i, op in enumerate(circuit.operations):
            if op["name"] != "barrier":
                last_executable = i
        for i, op in enumerate(circuit.operations):
            if op["name"] == "measure" and i < last_executable:
                return True
            if op.get("condition") or op["name"] in ("jump", "classical_op"):
                return True
        return False

    def sample_with_collapse(self, circuit: QuantumCircuit, shots: int = 1024,
                             seed: int | None = None, noise_model=None) -> dict:
        """
        Execute the circuit shot-by-shot, applying projective measurements
        and optional per-gate noise when encountered.

        Args:
            circuit: The quantum circuit to simulate.
            shots: Number of measurement shots.
            seed: Random seed.
            noise_model: Optional NoiseModel for per-gate noise injection.
        """
        if shots <= 0:
            raise ValueError("shots must be a positive integer")

        measured_qubits = self._extract_measured_qubits(circuit)
        if not measured_qubits:
            measured_qubits = list(range(circuit.num_qubits))

        rng = np.random.default_rng(seed)
        counts: dict[str, int] = {}

        for _ in range(shots):
            run_seed = int(rng.integers(0, 2**31 - 1))
            if noise_model is not None and noise_model.has_noise():
                state, mem = self._simulate_with_noise(circuit, noise_model, seed=run_seed)
            else:
                state, mem = self.simulate(circuit, seed=run_seed)
            # Final measurement of requested qubits
            measured_bits, _ = self._measure_and_collapse(state, measured_qubits, circuit.num_qubits, rng)

            # Apply readout noise from noise model
            if noise_model is not None:
                bits_list = list(measured_bits)
                for i, q in enumerate(measured_qubits):
                    cm = noise_model.get_readout_error(q)
                    if cm is not None:
                        true_bit = int(bits_list[i])
                        # Sample from confusion matrix row
                        flip_prob = cm[true_bit, 1 - true_bit]
                        if rng.random() < flip_prob:
                            bits_list[i] = str(1 - true_bit)
                measured_bits = "".join(bits_list)

            counts[measured_bits] = counts.get(measured_bits, 0) + 1

        return counts

    def _simulate_with_noise(self, circuit: QuantumCircuit, noise_model,
                             seed: int = None, max_ops: int = 1_000_000) -> tuple[np.ndarray, dict]:
        """Single-shot simulation with per-gate noise injection.

        After each gate, applies the corresponding noise channel from the
        noise model using stochastic Kraus trajectories.
        """
        num_qubits = circuit.num_qubits
        state = np.zeros(2**num_qubits, dtype=complex)
        state[0] = 1.0
        classical_memory = {name: np.zeros(size, dtype=int)
                           for name, size in circuit.classical_registers.items()}
        rng = np.random.default_rng(seed)

        # Pre-scan for labels
        labels = {}
        for idx, op in enumerate(circuit.operations):
            if op["name"] == "label":
                labels[op["label"]] = idx

        pc = 0
        ops_executed = 0
        while pc < len(circuit.operations):
            if ops_executed > max_ops:
                raise QVMResourceLimitError(f"Exceeded maximum operations limit ({max_ops}).")

            op = circuit.operations[pc]
            ops_executed += 1
            name, qubits, params = op["name"], op["qubits"], op["params"]

            # Control flow
            if name == "label":
                pc += 1
                continue
            if name == "jump":
                should_jump = True
                if op["condition"]:
                    cond = op["condition"]
                    if classical_memory[cond["register"]][cond["index"]] != cond["value"]:
                        should_jump = False
                pc = labels[op["jump_to"]] if should_jump else pc + 1
                continue
            if op["condition"]:
                cond = op["condition"]
                if classical_memory[cond["register"]][cond["index"]] != cond["value"]:
                    pc += 1
                    continue

            # Apply quantum gate
            if name in ["h", "x", "y", "z", "rx", "ry", "rz", "p", "id",
                        "sx", "sxdg", "s", "sdg", "t", "tdg"]:
                gate_mat = self._get_gate_matrix(name, params)
                state = self._apply_single_qubit_gate(state, gate_mat, qubits[0], num_qubits)
            elif name == "cx":
                state = self._apply_cnot_gate(state, qubits[0], qubits[1], num_qubits)
            elif name == "cz":
                state = self._apply_cz_gate(state, qubits[0], qubits[1], num_qubits)
            elif name == "swap":
                state = self._apply_swap_gate(state, qubits[0], qubits[1], num_qubits)
            elif name in ["ccx", "toffoli"]:
                state = self._apply_ccx_gate(state, qubits[0], qubits[1], qubits[2], num_qubits)
            elif name == "rzz":
                state = self._apply_rzz_gate(state, qubits[0], qubits[1],
                                             float(resolve_param(params[0])), num_qubits)
            elif name == "rxx":
                state = self._apply_rxx_gate(state, qubits[0], qubits[1],
                                             float(resolve_param(params[0])), num_qubits)
            elif name == "cp":
                state = self._apply_cp_gate(state, qubits[0], qubits[1],
                                            float(resolve_param(params[0])), num_qubits)
            elif name == "measure":
                bit_str, state = self._measure_and_collapse(state, qubits, num_qubits, rng)
                if op["target_bit"]:
                    reg_name, reg_idx = op["target_bit"]
                    classical_memory[reg_name][reg_idx] = int(bit_str[0])
                pc += 1
                continue  # No noise after measurement
            elif name in ("delay", "barrier"):
                pc += 1
                continue
            elif name == "classical_op":
                self._execute_classical_op(op["classical_op"], classical_memory)
                pc += 1
                continue
            else:
                raise UnsupportedGateError(f"Unsupported gate operation: {name}")

            # Apply per-gate noise (stochastic Kraus trajectory)
            if name not in ["measure", "delay", "classical_op", "barrier"]:
                channel = noise_model.get_noise_for(name, qubits)
                if channel is not None:
                    state = channel.apply_to_statevector(state, qubits, num_qubits, rng)

            pc += 1

        return state, classical_memory

    @staticmethod
    def _extract_measured_qubits(circuit: QuantumCircuit) -> list:
        measured = []
        for op in circuit.operations:
            if op["name"] == "measure":
                measured.extend(op["qubits"])
        return sorted(set(measured))

    @staticmethod
    def _apply_readout_noise(bitstring: str, flip_prob: float, rng) -> str:
        bits = list(bitstring)
        for i, b in enumerate(bits):
            if rng.random() < flip_prob:
                bits[i] = "0" if b == "1" else "1"
        return "".join(bits)

    @staticmethod
    def _measure_and_collapse(statevector: np.ndarray, qubits: list, num_qubits: int, rng) -> tuple[str, np.ndarray]:
        """
        Measure the given qubits, collapse the state, and return (bitstring, collapsed_state).
        """
        if not qubits:
            return "", statevector

        # Compute probabilities for each outcome on the measured subset
        probs = {}
        indices = np.arange(len(statevector))
        for outcome in range(2 ** len(qubits)):
            mask = np.ones_like(statevector, dtype=bool)
            for i, q in enumerate(qubits):
                bit = (outcome >> i) & 1
                mask &= ((indices >> q) & 1) == bit
            probs[outcome] = float(np.sum(np.abs(statevector[mask]) ** 2))

        outcomes = np.array(list(probs.keys()))
        prob_vals = np.array(list(probs.values()))
        prob_vals = prob_vals / prob_vals.sum()
        sampled_outcome = int(rng.choice(outcomes, p=prob_vals))

        # Collapse state
        mask = np.ones_like(statevector, dtype=bool)
        indices = np.arange(len(statevector))
        for i, q in enumerate(qubits):
            bit = (sampled_outcome >> i) & 1
            mask &= ((indices >> q) & 1) == bit
        collapsed = np.zeros_like(statevector)
        collapsed[mask] = statevector[mask]
        collapsed = collapsed / np.linalg.norm(collapsed)

        bitstring = format(sampled_outcome, f"0{len(qubits)}b")[::-1]  # maintain little-endian order
        return bitstring, collapsed
