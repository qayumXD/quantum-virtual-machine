# src/qvm/vqe.py

"""
Variational Quantum Eigensolver (VQE) implementation.

VQE is a hybrid quantum-classical algorithm that finds the ground state energy
of a Hamiltonian using a parameterized quantum circuit (ansatz) and a classical
optimizer.
"""

from __future__ import annotations
import numpy as np
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, TYPE_CHECKING

from src.qvm.parameter import Parameter
from src.qvm.observable import Hamiltonian
from src.qvm.simulator import Simulator
from src.qvm.gradient import parameter_shift_gradient

if TYPE_CHECKING:
    from src.qvm.ir import QuantumCircuit
    from src.qvm.noise import NoiseModel


@dataclass
class VQEResult:
    """Results from a VQE optimization run."""
    optimal_energy: float
    optimal_params: np.ndarray
    convergence_history: List[float] = field(default_factory=list)
    num_circuit_evaluations: int = 0
    num_iterations: int = 0
    success: bool = False


class VQE:
    """Variational Quantum Eigensolver.

    Usage:
        from src.qvm.parameter import Parameter
        from src.qvm.observable import Hamiltonian
        from src.qvm.ir import QuantumCircuit

        # Define ansatz
        theta = Parameter("theta")
        def ansatz(params):
            qc = QuantumCircuit(2)
            qc.add_operation("ry", [0], params=[params[theta]])
            qc.add_operation("cx", [0, 1])
            return qc

        # Define Hamiltonian
        H = Hamiltonian.from_dict({"ZZ": -1.0, "XI": 0.5, "IX": 0.5})

        # Run VQE
        vqe = VQE(ansatz_fn=ansatz, hamiltonian=H)
        result = vqe.run(parameters=[theta])
    """

    def __init__(
        self,
        ansatz_fn: Callable[[Dict[Parameter, float]], "QuantumCircuit"],
        hamiltonian: Hamiltonian,
        simulator: Optional[Simulator] = None,
        optimizer: str = "cobyla",
        noise_model: Optional["NoiseModel"] = None,
    ):
        """
        Args:
            ansatz_fn: A callable that takes a dict {Parameter: float} and returns
                       a QuantumCircuit with those parameter values applied.
            hamiltonian: The Hamiltonian whose ground state energy we seek.
            simulator: A Simulator instance (creates one if None).
            optimizer: Scipy optimizer name: 'cobyla', 'nelder-mead', 'powell',
                       'l-bfgs-b', 'bfgs'. Default 'cobyla'.
            noise_model: Optional noise model for noisy VQE simulation.
        """
        self.ansatz_fn = ansatz_fn
        self.hamiltonian = hamiltonian
        self.simulator = simulator or Simulator()
        self.optimizer = optimizer.lower()
        self.noise_model = noise_model
        self._eval_count = 0

    def _cost_function(self, param_values: np.ndarray,
                       parameters: List[Parameter]) -> float:
        """Evaluate the cost function ⟨ψ(θ)|H|ψ(θ)⟩."""
        self._eval_count += 1
        bindings = {p: v for p, v in zip(parameters, param_values)}
        circuit = self.ansatz_fn(bindings)
        energy = self.simulator.expectation_value(circuit, self.hamiltonian)
        self._history.append(float(energy))
        return float(energy)

    def run(
        self,
        parameters: List[Parameter],
        initial_params: Optional[np.ndarray] = None,
        max_iterations: int = 100,
        tol: float = 1e-6,
    ) -> VQEResult:
        """Run the VQE optimization.

        Args:
            parameters: List of Parameter objects used in the ansatz.
            initial_params: Initial parameter values. Random if None.
            max_iterations: Maximum optimizer iterations.
            tol: Convergence tolerance.

        Returns:
            VQEResult with the optimization outcome.
        """
        try:
            from scipy.optimize import minimize
        except ImportError:
            raise ImportError(
                "scipy is required for VQE. Install it with: pip install scipy"
            )

        n_params = len(parameters)
        if initial_params is None:
            initial_params = np.random.uniform(-np.pi, np.pi, size=n_params)
        else:
            initial_params = np.asarray(initial_params, dtype=float)

        self._eval_count = 0
        self._history = []

        result = minimize(
            fun=self._cost_function,
            x0=initial_params,
            args=(parameters,),
            method=self.optimizer,
            options={"maxiter": max_iterations},
            tol=tol,
        )

        return VQEResult(
            optimal_energy=float(result.fun),
            optimal_params=result.x,
            convergence_history=list(self._history),
            num_circuit_evaluations=self._eval_count,
            num_iterations=result.nit if hasattr(result, 'nit') else len(self._history),
            success=result.success,
        )
