# src/qvm/qaoa.py

"""
Quantum Approximate Optimization Algorithm (QAOA) implementation.

QAOA finds approximate solutions to combinatorial optimization problems
using a parameterized quantum circuit with alternating cost and mixer layers.
"""

from __future__ import annotations
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from src.qvm.parameter import Parameter
from src.qvm.observable import Hamiltonian, PauliOp
from src.qvm.simulator import Simulator
from src.qvm.ir import QuantumCircuit

if TYPE_CHECKING:
    from src.qvm.noise import NoiseModel


@dataclass
class QAOAResult:
    """Results from a QAOA optimization run."""
    optimal_cost: float
    optimal_gamma: np.ndarray
    optimal_beta: np.ndarray
    best_bitstring: str
    convergence_history: List[float] = field(default_factory=list)
    num_circuit_evaluations: int = 0
    success: bool = False
    measurement_counts: Optional[Dict[str, int]] = None


class QAOA:
    """Quantum Approximate Optimization Algorithm for combinatorial problems.

    Usage:
        # MaxCut on a triangle graph
        edges = [(0, 1), (1, 2), (0, 2)]
        cost_H = QAOA.maxcut_hamiltonian(edges, num_qubits=3)
        qaoa = QAOA(cost_hamiltonian=cost_H, num_layers=2)
        result = qaoa.run()
    """

    def __init__(
        self,
        cost_hamiltonian: Hamiltonian,
        mixer_hamiltonian: Optional[Hamiltonian] = None,
        num_layers: int = 1,
        simulator: Optional[Simulator] = None,
        noise_model: Optional["NoiseModel"] = None,
    ):
        """
        Args:
            cost_hamiltonian: The problem Hamiltonian (diagonal in Z-basis).
            mixer_hamiltonian: The mixer Hamiltonian. Defaults to Σ Xᵢ.
            num_layers: Number of QAOA layers (p).
            simulator: A Simulator instance.
            noise_model: Optional noise model.
        """
        self.cost_hamiltonian = cost_hamiltonian
        self.num_qubits = cost_hamiltonian.num_qubits
        self.mixer_hamiltonian = mixer_hamiltonian
        self.num_layers = num_layers
        self.simulator = simulator or Simulator()
        self.noise_model = noise_model

        # Create parameters
        self.gamma_params = [Parameter(f"gamma_{i}") for i in range(num_layers)]
        self.beta_params = [Parameter(f"beta_{i}") for i in range(num_layers)]

    def build_circuit(self, gamma: List[float], beta: List[float]) -> QuantumCircuit:
        """Build the QAOA circuit for given parameters.

        The circuit structure is:
        1. Initial state: |+⟩^n (Hadamard on all qubits)
        2. For each layer p:
           a. Cost unitary: e^{-iγ_p C} (implemented via ZZ rotations)
           b. Mixer unitary: e^{-iβ_p B} (implemented via RX rotations)
        """
        qc = QuantumCircuit(self.num_qubits)

        # 1. Initial superposition
        for q in range(self.num_qubits):
            qc.add_operation("h", [q])

        # 2. QAOA layers
        for layer in range(self.num_layers):
            # Cost unitary: for each ZZ term, apply RZZ(2*gamma*coeff)
            # For diagonal Hamiltonians, ZZ interaction → CNOT-RZ-CNOT
            for term in self.cost_hamiltonian.terms:
                self._apply_cost_term(qc, term, gamma[layer])

            # Mixer unitary: RX(2*beta) on each qubit
            for q in range(self.num_qubits):
                qc.add_operation("rx", [q], params=[2 * beta[layer]])

        return qc

    def _apply_cost_term(self, qc: QuantumCircuit, term: PauliOp, gamma: float):
        """Apply e^{-iγ·coeff·P} for a single Pauli term to the circuit.

        For ZZ terms: CNOT - RZ(2γ·coeff) - CNOT
        For Z terms: RZ(2γ·coeff)
        For identity: global phase (ignored)
        """
        # Find non-identity positions
        z_positions = [i for i, c in enumerate(term.pauli_string) if c == "Z"]

        if len(z_positions) == 0:
            # Identity term — just a global phase, skip
            return
        elif len(z_positions) == 1:
            # Single Z: RZ(2*gamma*coeff)
            q = z_positions[0]
            qc.add_operation("rz", [q], params=[2 * gamma * term.coeff])
        elif len(z_positions) == 2:
            # ZZ interaction: CNOT ladder + RZ
            q0, q1 = z_positions
            qc.add_operation("cx", [q0, q1])
            qc.add_operation("rz", [q1], params=[2 * gamma * term.coeff])
            qc.add_operation("cx", [q0, q1])
        else:
            # General multi-Z: CNOT ladder to parity qubit, RZ, undo
            for i in range(len(z_positions) - 1):
                qc.add_operation("cx", [z_positions[i], z_positions[i + 1]])
            qc.add_operation("rz", [z_positions[-1]],
                             params=[2 * gamma * term.coeff])
            for i in range(len(z_positions) - 2, -1, -1):
                qc.add_operation("cx", [z_positions[i], z_positions[i + 1]])

    def run(
        self,
        initial_gamma: Optional[np.ndarray] = None,
        initial_beta: Optional[np.ndarray] = None,
        max_iterations: int = 100,
        shots: int = 1024,
        optimizer: str = "cobyla",
    ) -> QAOAResult:
        """Run the QAOA optimization.

        Args:
            initial_gamma: Initial γ values. Random if None.
            initial_beta: Initial β values. Random if None.
            max_iterations: Maximum optimizer iterations.
            shots: Number of measurement shots for final result.
            optimizer: Scipy optimizer name.

        Returns:
            QAOAResult with optimization outcome and best bitstring.
        """
        try:
            from scipy.optimize import minimize
        except ImportError:
            raise ImportError(
                "scipy is required for QAOA. Install it with: pip install scipy"
            )

        p = self.num_layers
        if initial_gamma is None:
            initial_gamma = np.random.uniform(0, 2 * np.pi, size=p)
        if initial_beta is None:
            initial_beta = np.random.uniform(0, np.pi, size=p)

        x0 = np.concatenate([initial_gamma, initial_beta])
        history = []
        eval_count = [0]

        def cost_fn(x):
            eval_count[0] += 1
            gamma = x[:p]
            beta = x[p:]
            circuit = self.build_circuit(gamma.tolist(), beta.tolist())
            energy = self.simulator.expectation_value(circuit, self.cost_hamiltonian)
            history.append(float(energy))
            return float(energy)

        result = minimize(
            fun=cost_fn,
            x0=x0,
            method=optimizer,
            options={"maxiter": max_iterations},
        )

        opt_gamma = result.x[:p]
        opt_beta = result.x[p:]

        # Final measurement to find the best bitstring
        final_circuit = self.build_circuit(opt_gamma.tolist(), opt_beta.tolist())
        counts = self.simulator.sample(final_circuit, shots=shots)

        # Find the bitstring with highest count
        best_bitstring = max(counts, key=counts.get)

        return QAOAResult(
            optimal_cost=float(result.fun),
            optimal_gamma=opt_gamma,
            optimal_beta=opt_beta,
            best_bitstring=best_bitstring,
            convergence_history=history,
            num_circuit_evaluations=eval_count[0],
            success=result.success,
            measurement_counts=counts,
        )

    # ---- Convenience Hamiltonian constructors ----

    @staticmethod
    def maxcut_hamiltonian(edges: List[Tuple[int, int]], num_qubits: int) -> Hamiltonian:
        """Build the MaxCut cost Hamiltonian for a graph.

        MaxCut: C = Σ_{(i,j) ∈ E} (1 - Z_i Z_j) / 2

        We minimize -C (to find the maximum cut).
        """
        terms = []
        for i, j in edges:
            # (1 - ZiZj)/2 = 0.5*II - 0.5*ZiZj
            # For minimization: -(0.5*II - 0.5*ZiZj) = -0.5*II + 0.5*ZiZj
            chars = ["I"] * num_qubits
            chars[i] = "Z"
            chars[j] = "Z"
            terms.append(PauliOp("".join(chars), coeff=0.5))
            # The constant -0.5*II per edge shifts energy but doesn't affect optimization
            terms.append(PauliOp("I" * num_qubits, coeff=-0.5))

        return Hamiltonian(terms)

    @staticmethod
    def maxcut_cost(bitstring: str, edges: List[Tuple[int, int]]) -> int:
        """Evaluate the MaxCut cost for a given bitstring classically."""
        cost = 0
        for i, j in edges:
            if bitstring[i] != bitstring[j]:
                cost += 1
        return cost
