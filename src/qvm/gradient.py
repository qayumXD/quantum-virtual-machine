# src/qvm/gradient.py

"""
Gradient computation methods for parameterized quantum circuits.

Supports:
  - Parameter Shift Rule (exact analytic gradients)
  - Finite Difference (numerical fallback)
"""

from __future__ import annotations
import numpy as np
from typing import List, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from src.qvm.ir import QuantumCircuit
    from src.qvm.simulator import Simulator
    from src.qvm.observable import Hamiltonian
    from src.qvm.parameter import Parameter


def parameter_shift_gradient(
    simulator: "Simulator",
    circuit: "QuantumCircuit",
    observable: "Hamiltonian",
    parameters: List["Parameter"],
    current_values: Dict["Parameter", float],
    shift: float = np.pi / 2,
) -> np.ndarray:
    """Compute ∂⟨H⟩/∂θᵢ for each parameter using the parameter shift rule.

    For rotation gates Rα(θ), the gradient is:
        ∂⟨H⟩/∂θ = [⟨H(θ+s)⟩ − ⟨H(θ−s)⟩] / (2 sin(s))

    This requires 2 circuit evaluations per parameter.

    Args:
        simulator: A Simulator instance.
        circuit: A parameterized QuantumCircuit.
        observable: The Hamiltonian to compute ⟨H⟩ for.
        parameters: List of Parameters to differentiate with respect to.
        current_values: Current parameter bindings {Parameter: float}.
        shift: The shift amount (default π/2 for standard rotation gates).

    Returns:
        np.ndarray of shape (len(parameters),) with the gradient vector.
    """
    gradient = np.zeros(len(parameters))
    scale = 2 * np.sin(shift)

    for i, param in enumerate(parameters):
        # Forward shift: θᵢ + s
        forward_values = dict(current_values)
        forward_values[param] = current_values[param] + shift
        forward_circuit = circuit.bind_parameters(forward_values)
        e_forward = simulator.expectation_value(forward_circuit, observable)

        # Backward shift: θᵢ - s
        backward_values = dict(current_values)
        backward_values[param] = current_values[param] - shift
        backward_circuit = circuit.bind_parameters(backward_values)
        e_backward = simulator.expectation_value(backward_circuit, observable)

        gradient[i] = (e_forward - e_backward) / scale

    return gradient


def finite_diff_gradient(
    simulator: "Simulator",
    circuit: "QuantumCircuit",
    observable: "Hamiltonian",
    parameters: List["Parameter"],
    current_values: Dict["Parameter", float],
    epsilon: float = 1e-5,
) -> np.ndarray:
    """Compute ∂⟨H⟩/∂θᵢ via central finite differences.

    This is a numerical fallback — less accurate than parameter shift
    but works for any differentiable function.

    Args:
        simulator: A Simulator instance.
        circuit: A parameterized QuantumCircuit.
        observable: The Hamiltonian.
        parameters: Parameters to differentiate.
        current_values: Current parameter bindings.
        epsilon: Step size for finite differences.

    Returns:
        np.ndarray of shape (len(parameters),) with the gradient vector.
    """
    gradient = np.zeros(len(parameters))

    for i, param in enumerate(parameters):
        # f(θ + ε)
        plus_values = dict(current_values)
        plus_values[param] = current_values[param] + epsilon
        plus_circuit = circuit.bind_parameters(plus_values)
        e_plus = simulator.expectation_value(plus_circuit, observable)

        # f(θ - ε)
        minus_values = dict(current_values)
        minus_values[param] = current_values[param] - epsilon
        minus_circuit = circuit.bind_parameters(minus_values)
        e_minus = simulator.expectation_value(minus_circuit, observable)

        gradient[i] = (e_plus - e_minus) / (2 * epsilon)

    return gradient
