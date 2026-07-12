# src/qvm/noise.py

"""
Advanced noise model system using Kraus operators.

Provides:
  - NoiseChannel: individual noise channels (depolarizing, amplitude/phase damping, thermal relaxation)
  - NoiseModel: composable per-gate noise configuration
  - DeviceBackend: predefined hardware-like noise profiles

Noise is applied via stochastic trajectories (Monte Carlo) within the
statevector framework — no density matrix conversion needed.
"""

from __future__ import annotations
import numpy as np
from typing import Dict, List, Optional, Tuple


class NoiseChannel:
    """A quantum noise channel defined by Kraus operators {Kᵢ}: ρ → Σ Kᵢ ρ Kᵢ†

    For statevector (stochastic trajectory) simulation:
      1. Compute pᵢ = ‖Kᵢ|ψ⟩‖²
      2. Sample Kᵢ with probability pᵢ
      3. Apply |ψ⟩ → Kᵢ|ψ⟩ / √pᵢ
    """

    def __init__(self, name: str, kraus_ops: List[np.ndarray]):
        if not kraus_ops:
            raise ValueError("At least one Kraus operator is required.")
        self.name = name
        self.kraus_ops = [np.asarray(k, dtype=complex) for k in kraus_ops]
        self.num_qubits = int(np.log2(self.kraus_ops[0].shape[0]))

    def validate(self, atol: float = 1e-8) -> bool:
        """Check completeness relation: Σ Kᵢ†Kᵢ = I."""
        dim = self.kraus_ops[0].shape[0]
        total = np.zeros((dim, dim), dtype=complex)
        for k in self.kraus_ops:
            total += k.conj().T @ k
        return np.allclose(total, np.eye(dim), atol=atol)

    def apply_to_statevector(self, state: np.ndarray, target_qubits: List[int],
                             num_qubits: int, rng: np.random.Generator) -> np.ndarray:
        """Apply this noise channel stochastically to a statevector.

        For single-qubit channels, builds the full operator via Kronecker product
        and applies it. Uses the stochastic trajectory method.

        If the channel is single-qubit but the gate acts on multiple qubits,
        the channel is applied independently to each target qubit.
        """
        # Handle dimension mismatch: single-qubit channel on multi-qubit gate
        if self.num_qubits == 1 and len(target_qubits) > 1:
            for q in target_qubits:
                state = self.apply_to_statevector(state, [q], num_qubits, rng)
            return state

        # Build full Kraus operators for the target qubits
        full_kraus = []
        for k in self.kraus_ops:
            full_k = self._embed_operator(k, target_qubits, num_qubits)
            full_kraus.append(full_k)

        # Compute probabilities for each Kraus operator
        probs = []
        new_states = []
        for fk in full_kraus:
            new_state = fk @ state
            p = float(np.real(np.vdot(new_state, new_state)))
            probs.append(p)
            new_states.append(new_state)

        probs = np.array(probs)
        # Normalize probabilities (should sum to 1, but numerical issues)
        probs = probs / probs.sum()

        # Sample one Kraus operator
        idx = rng.choice(len(probs), p=probs)
        result = new_states[idx]
        norm = np.linalg.norm(result)
        if norm > 0:
            result = result / norm
        return result

    @staticmethod
    def _embed_operator(op: np.ndarray, target_qubits: List[int],
                        num_qubits: int) -> np.ndarray:
        """Embed a local operator into the full Hilbert space via Kronecker product.

        Uses the convention where qubit 0 is the most significant bit (leftmost in kron).
        Note: The simulator uses a different convention internally (qubit 0 = LSB),
        so we reverse the target position to match.
        """
        n = num_qubits
        if len(target_qubits) == 1:
            q = target_qubits[0]
            eye = np.eye(2, dtype=complex)
            mats = [eye] * n
            mats[n - 1 - q] = op  # Match simulator's qubit ordering
            result = mats[0]
            for m in mats[1:]:
                result = np.kron(result, m)
            return result
        elif len(target_qubits) == 2:
            # For 2-qubit operators, construct the full permutation
            # This is a simplified version that works for our use case
            q0, q1 = target_qubits
            dim = 2 ** n
            full_op = np.eye(dim, dtype=complex)
            for i in range(dim):
                for j in range(dim):
                    # Extract the bits for target qubits
                    bi0 = (i >> q0) & 1
                    bi1 = (i >> q1) & 1
                    bj0 = (j >> q0) & 1
                    bj1 = (j >> q1) & 1
                    # Check that all other bits match
                    other_mask = ~((1 << q0) | (1 << q1)) & ((1 << n) - 1)
                    if (i & other_mask) != (j & other_mask):
                        continue
                    # Map to local operator indices
                    local_i = bi0 * 2 + bi1
                    local_j = bj0 * 2 + bj1
                    full_op[i, j] = op[local_i, local_j]
            return full_op
        else:
            raise ValueError("Only 1-qubit and 2-qubit noise channels are supported.")

    # ---- Built-in noise channels ----

    @classmethod
    def depolarizing(cls, p: float) -> NoiseChannel:
        """Single-qubit depolarizing channel.

        With probability p, replaces the qubit state with the maximally mixed state.
        Kraus operators: {√(1-3p/4) I, √(p/4) X, √(p/4) Y, √(p/4) Z}
        """
        if not 0 <= p <= 1:
            raise ValueError(f"Depolarizing probability must be in [0,1], got {p}")
        I = np.eye(2, dtype=complex)
        X = np.array([[0, 1], [1, 0]], dtype=complex)
        Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
        Z = np.array([[1, 0], [0, -1]], dtype=complex)
        return cls("depolarizing", [
            np.sqrt(1 - 3 * p / 4) * I,
            np.sqrt(p / 4) * X,
            np.sqrt(p / 4) * Y,
            np.sqrt(p / 4) * Z,
        ])

    @classmethod
    def amplitude_damping(cls, gamma: float) -> NoiseChannel:
        """Amplitude damping channel (T1 relaxation / energy decay).

        Models spontaneous emission: |1⟩ → |0⟩ with probability γ.

        Kraus operators:
            K₀ = [[1, 0], [0, √(1-γ)]]
            K₁ = [[0, √γ], [0, 0]]
        """
        if not 0 <= gamma <= 1:
            raise ValueError(f"Gamma must be in [0,1], got {gamma}")
        K0 = np.array([[1, 0], [0, np.sqrt(1 - gamma)]], dtype=complex)
        K1 = np.array([[0, np.sqrt(gamma)], [0, 0]], dtype=complex)
        return cls("amplitude_damping", [K0, K1])

    @classmethod
    def phase_damping(cls, gamma: float) -> NoiseChannel:
        """Phase damping channel (T2 dephasing / decoherence).

        Destroys off-diagonal elements of the density matrix without energy loss.

        Kraus operators:
            K₀ = [[1, 0], [0, √(1-γ)]]
            K₁ = [[0, 0], [0, √γ]]
        """
        if not 0 <= gamma <= 1:
            raise ValueError(f"Gamma must be in [0,1], got {gamma}")
        K0 = np.array([[1, 0], [0, np.sqrt(1 - gamma)]], dtype=complex)
        K1 = np.array([[0, 0], [0, np.sqrt(gamma)]], dtype=complex)
        return cls("phase_damping", [K0, K1])

    @classmethod
    def thermal_relaxation(cls, t1: float, t2: float, gate_time: float) -> NoiseChannel:
        """Combined T1 + T2 thermal relaxation channel.

        Converts physical relaxation times into Kraus operators.

        Args:
            t1: T1 relaxation time (energy decay) in nanoseconds.
            t2: T2 dephasing time in nanoseconds. Must satisfy t2 <= 2*t1.
            gate_time: Duration of the gate in nanoseconds.
        """
        if t2 > 2 * t1:
            raise ValueError(f"T2 ({t2}) must be <= 2*T1 ({2*t1})")
        if gate_time <= 0:
            raise ValueError("Gate time must be positive")

        # Compute damping probabilities
        p_amplitude = 1 - np.exp(-gate_time / t1) if t1 > 0 else 1.0
        p_phase = 1 - np.exp(-gate_time / t2) if t2 > 0 else 1.0

        # If T2 << T1, the dominant effect is pure dephasing
        # We decompose into amplitude damping followed by phase damping
        # p_phase_residual accounts for dephasing beyond what amplitude damping provides
        if t1 > 0 and t2 > 0:
            p_phase_residual = max(0, 1 - (1 - p_phase) / np.sqrt(1 - p_amplitude))
        else:
            p_phase_residual = p_phase

        # Build composite channel: apply amplitude damping then phase damping
        # For simplicity we use the amplitude damping channel with the combined effect
        gamma_ad = p_amplitude
        gamma_pd = min(p_phase_residual, 1.0)

        # Combine into effective Kraus operators
        K0_ad = np.array([[1, 0], [0, np.sqrt(1 - gamma_ad)]], dtype=complex)
        K1_ad = np.array([[0, np.sqrt(gamma_ad)], [0, 0]], dtype=complex)
        K0_pd = np.array([[1, 0], [0, np.sqrt(1 - gamma_pd)]], dtype=complex)
        K1_pd = np.array([[0, 0], [0, np.sqrt(gamma_pd)]], dtype=complex)

        # Combined Kraus: {K0_pd @ K0_ad, K0_pd @ K1_ad, K1_pd @ K0_ad, K1_pd @ K1_ad}
        combined = []
        for kp in [K0_pd, K1_pd]:
            for ka in [K0_ad, K1_ad]:
                k = kp @ ka
                if np.linalg.norm(k) > 1e-15:
                    combined.append(k)

        return cls("thermal_relaxation", combined)

    @classmethod
    def depolarizing_2q(cls, p: float) -> NoiseChannel:
        """Two-qubit depolarizing channel.

        With probability p, replaces the 2-qubit state with the maximally mixed state.
        """
        if not 0 <= p <= 1:
            raise ValueError(f"Depolarizing probability must be in [0,1], got {p}")

        I = np.eye(2, dtype=complex)
        X = np.array([[0, 1], [1, 0]], dtype=complex)
        Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
        Z = np.array([[1, 0], [0, -1]], dtype=complex)

        paulis_1q = [I, X, Y, Z]
        kraus = []
        for p1 in paulis_1q:
            for p2 in paulis_1q:
                kraus.append(np.kron(p1, p2))

        # Scale: K_0 = √(1-15p/16) * II, rest = √(p/16) * PiPj
        scaled = [np.sqrt(1 - 15 * p / 16) * kraus[0]]
        for k in kraus[1:]:
            scaled.append(np.sqrt(p / 16) * k)

        return cls("depolarizing_2q", scaled)

    def __repr__(self):
        return f"NoiseChannel('{self.name}', num_kraus={len(self.kraus_ops)})"


class NoiseModel:
    """Composable noise model: maps gate names and qubit indices to noise channels.

    Usage:
        model = NoiseModel()
        model.add_all_qubit_quantum_error(NoiseChannel.depolarizing(0.01), ["h", "x"])
        model.add_quantum_error(NoiseChannel.depolarizing(0.05), ["cx"], [0, 1])
        model.add_readout_error(np.array([[0.95, 0.05], [0.05, 0.95]]), [0])
    """

    def __init__(self):
        # gate_name → list of (qubits_or_None, NoiseChannel)
        self._gate_errors: Dict[str, List[Tuple[Optional[Tuple[int, ...]], NoiseChannel]]] = {}
        # qubit → 2x2 confusion matrix
        self._readout_errors: Dict[int, np.ndarray] = {}

    def add_all_qubit_quantum_error(self, channel: NoiseChannel, gate_names: List[str]):
        """Apply a noise channel after the given gates on ALL qubits."""
        for gate in gate_names:
            if gate not in self._gate_errors:
                self._gate_errors[gate] = []
            self._gate_errors[gate].append((None, channel))

    def add_quantum_error(self, channel: NoiseChannel, gate_names: List[str],
                          qubits: List[int]):
        """Apply a noise channel after the given gates on SPECIFIC qubits only."""
        qubits_key = tuple(sorted(qubits))
        for gate in gate_names:
            if gate not in self._gate_errors:
                self._gate_errors[gate] = []
            self._gate_errors[gate].append((qubits_key, channel))

    def add_readout_error(self, confusion_matrix: np.ndarray, qubits: List[int]):
        """Set a readout error confusion matrix for specific qubits.

        confusion_matrix[i][j] = P(measure j | true state is i)
        E.g. [[0.95, 0.05], [0.03, 0.97]] means:
          - P(measure 0 | state 0) = 0.95
          - P(measure 1 | state 0) = 0.05
          - P(measure 0 | state 1) = 0.03
          - P(measure 1 | state 1) = 0.97
        """
        cm = np.asarray(confusion_matrix, dtype=float)
        if cm.shape != (2, 2):
            raise ValueError("Confusion matrix must be 2x2")
        for q in qubits:
            self._readout_errors[q] = cm

    def get_noise_for(self, gate_name: str, qubits: List[int]) -> Optional[NoiseChannel]:
        """Look up the noise channel for a specific gate + qubit combination.

        Returns the first matching channel (specific qubits take priority over all-qubit).
        """
        if gate_name not in self._gate_errors:
            return None

        qubits_key = tuple(sorted(qubits))
        # First check qubit-specific errors
        for target_qubits, channel in self._gate_errors[gate_name]:
            if target_qubits is not None and target_qubits == qubits_key:
                return channel
        # Then check all-qubit errors
        for target_qubits, channel in self._gate_errors[gate_name]:
            if target_qubits is None:
                return channel
        return None

    def get_readout_error(self, qubit: int) -> Optional[np.ndarray]:
        """Get the readout confusion matrix for a qubit, or None."""
        return self._readout_errors.get(qubit, None)

    def has_noise(self) -> bool:
        """True if any noise is configured."""
        return bool(self._gate_errors) or bool(self._readout_errors)

    def summary(self) -> str:
        """Human-readable summary of the noise model."""
        lines = ["NoiseModel:"]
        if not self.has_noise():
            lines.append("  (ideal, no noise)")
            return "\n".join(lines)
        for gate, entries in self._gate_errors.items():
            for qubits, channel in entries:
                q_str = f"qubits={list(qubits)}" if qubits else "all qubits"
                lines.append(f"  {gate}: {channel.name} on {q_str}")
        for q, cm in self._readout_errors.items():
            lines.append(f"  readout q{q}: P(0|0)={cm[0,0]:.3f}, P(1|1)={cm[1,1]:.3f}")
        return "\n".join(lines)

    def __repr__(self):
        return self.summary()


class DeviceBackend:
    """Predefined hardware-like noise profiles.

    Encapsulates topology, T1/T2 times, gate error rates, and readout errors
    to generate a realistic NoiseModel.
    """

    def __init__(self, name: str, num_qubits: int,
                 topology: Dict[Tuple[int, int], bool],
                 t1_times: List[float],
                 t2_times: List[float],
                 single_gate_errors: Dict[str, float],
                 two_gate_errors: Dict[str, float],
                 readout_errors: List[float],
                 gate_times: Dict[str, float]):
        self.name = name
        self.num_qubits = num_qubits
        self.topology = topology
        self.t1_times = t1_times
        self.t2_times = t2_times
        self.single_gate_errors = single_gate_errors
        self.two_gate_errors = two_gate_errors
        self.readout_errors = readout_errors
        self.gate_times = gate_times

    def to_noise_model(self) -> NoiseModel:
        """Generate a NoiseModel from this device's calibration data."""
        model = NoiseModel()

        # Single-qubit gate errors as depolarizing noise
        single_gates = ["h", "x", "y", "z", "rx", "ry", "rz", "p",
                        "sx", "sxdg", "s", "sdg", "t", "tdg", "id"]
        for gate in single_gates:
            error_rate = self.single_gate_errors.get(gate,
                         self.single_gate_errors.get("default", 0.0))
            if error_rate > 0:
                channel = NoiseChannel.depolarizing(error_rate)
                model.add_all_qubit_quantum_error(channel, [gate])

        # Two-qubit gate errors
        two_q_gates = ["cx", "cz", "swap"]
        for gate in two_q_gates:
            error_rate = self.two_gate_errors.get(gate,
                         self.two_gate_errors.get("default", 0.0))
            if error_rate > 0:
                channel = NoiseChannel.depolarizing_2q(error_rate)
                model.add_all_qubit_quantum_error(channel, [gate])

        # Readout errors
        for q, error in enumerate(self.readout_errors):
            if error > 0:
                cm = np.array([[1 - error, error], [error, 1 - error]])
                model.add_readout_error(cm, [q])

        return model

    @classmethod
    def fake_5q_device(cls) -> DeviceBackend:
        """A 5-qubit device resembling IBM Manila.

        Topology: linear chain 0—1—2—3—4
        """
        topology = {(i, i+1): True for i in range(4)}
        return cls(
            name="fake_5q",
            num_qubits=5,
            topology=topology,
            t1_times=[100e3, 110e3, 95e3, 105e3, 98e3],      # ~100 μs in ns
            t2_times=[80e3, 85e3, 75e3, 82e3, 78e3],         # ~80 μs in ns
            single_gate_errors={"default": 0.001},             # 0.1% per gate
            two_gate_errors={"default": 0.01},                 # 1% per 2q gate
            readout_errors=[0.02, 0.015, 0.025, 0.02, 0.018], # ~2% readout error
            gate_times={"single": 35, "cx": 300, "measure": 1000},  # nanoseconds
        )

    @classmethod
    def fake_7q_device(cls) -> DeviceBackend:
        """A 7-qubit device resembling IBM Lagos.

        Topology: T-shape
          0—1—2—3
              |
              4—5—6
        """
        topology = {
            (0, 1): True, (1, 2): True, (2, 3): True,
            (1, 4): True, (4, 5): True, (5, 6): True,
        }
        return cls(
            name="fake_7q",
            num_qubits=7,
            topology=topology,
            t1_times=[95e3, 105e3, 100e3, 90e3, 110e3, 98e3, 102e3],
            t2_times=[75e3, 82e3, 78e3, 70e3, 85e3, 76e3, 80e3],
            single_gate_errors={"default": 0.0008},
            two_gate_errors={"default": 0.012},
            readout_errors=[0.022, 0.018, 0.02, 0.025, 0.019, 0.021, 0.023],
            gate_times={"single": 35, "cx": 280, "measure": 950},
        )

    @classmethod
    def ideal(cls, num_qubits: int) -> DeviceBackend:
        """An ideal device with no noise (for baseline comparisons)."""
        topology = {(i, j): True for i in range(num_qubits) for j in range(num_qubits) if i < j}
        return cls(
            name="ideal",
            num_qubits=num_qubits,
            topology=topology,
            t1_times=[float('inf')] * num_qubits,
            t2_times=[float('inf')] * num_qubits,
            single_gate_errors={"default": 0.0},
            two_gate_errors={"default": 0.0},
            readout_errors=[0.0] * num_qubits,
            gate_times={"single": 0, "cx": 0, "measure": 0},
        )

    def __repr__(self):
        return f"DeviceBackend('{self.name}', {self.num_qubits} qubits)"
