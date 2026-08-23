#!/usr/bin/env python3
"""
VQE Example: Finding the Ground State Energy of H₂
====================================================

This script demonstrates the Variational Quantum Eigensolver (VQE) —
a hybrid quantum-classical algorithm that finds the lowest eigenvalue
(ground state energy) of a molecular Hamiltonian.

We use the H₂ molecule at bond distance 0.735 Å with a pre-computed
qubit Hamiltonian (via the Bravyi-Kitaev transformation):

    H = -1.053 II + 0.395 IZ - 0.395 ZI - 0.011 ZZ + 0.181 XX

The exact ground state energy is ≈ -1.137 Hartree.

Usage:
    python examples/vqe_h2.py
"""

import numpy as np
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qvm.parameter import Parameter
from qvm.observable import Hamiltonian, PauliOp
from qvm.simulator import Simulator
from qvm.vqe import VQE
from qvm.ir import QuantumCircuit


def build_h2_hamiltonian() -> Hamiltonian:
    """Build the H₂ Hamiltonian at equilibrium bond distance (0.735 Å).

    This is the qubit representation obtained via the Bravyi-Kitaev
    transformation of the second-quantized molecular Hamiltonian
    in the STO-3G minimal basis.
    """
    return Hamiltonian([
        PauliOp("II", coeff=-1.0534),
        PauliOp("IZ", coeff=0.3953),
        PauliOp("ZI", coeff=-0.3953),
        PauliOp("ZZ", coeff=-0.0110),
        PauliOp("XX", coeff=0.1811),
    ])


# Define symbolic parameters
theta0 = Parameter("theta0")
theta1 = Parameter("theta1")
theta2 = Parameter("theta2")
theta3 = Parameter("theta3")


def build_ansatz(bindings: dict) -> QuantumCircuit:
    """Build a 2-qubit hardware-efficient ansatz with 4 parameters.

    Circuit:
        |0⟩ ── RY(θ₀) ──●── RY(θ₂) ──
        |0⟩ ── RY(θ₁) ──X── RY(θ₃) ──

    The pre-entanglement rotations set up the right superposition,
    and the post-entanglement rotations fine-tune the state to
    capture correlation effects like the XX term.
    """
    qc = QuantumCircuit(2)
    qc.add_operation("ry", [0], params=[bindings[theta0]])
    qc.add_operation("ry", [1], params=[bindings[theta1]])
    qc.add_operation("cx", [0, 1])
    qc.add_operation("ry", [0], params=[bindings[theta2]])
    qc.add_operation("ry", [1], params=[bindings[theta3]])
    return qc


if __name__ == "__main__":
    print("=" * 60)
    print("  VQE: Ground State Energy of H₂")
    print("=" * 60)
    print()

    # 1. Build the Hamiltonian
    hamiltonian = build_h2_hamiltonian()
    exact_energy = hamiltonian.ground_state_energy(num_qubits=2)
    print(f"  Hamiltonian: H = {hamiltonian}")
    print(f"  Exact ground state energy: {exact_energy:.6f} Hartree")
    print()

    # 2. Set up VQE
    sim = Simulator()
    vqe = VQE(
        ansatz_fn=build_ansatz,
        hamiltonian=hamiltonian,
        simulator=sim,
        optimizer="cobyla",
    )

    # 3. Run the optimization
    print("  Running VQE optimization...")
    print("  " + "-" * 40)
    all_params = [theta0, theta1, theta2, theta3]
    result = vqe.run(
        parameters=all_params,
        initial_params=np.array([0.1, 0.1, 0.1, 0.1]),
        max_iterations=300,
    )

    # 4. Print results
    print()
    print(f"  ✓ VQE converged: {result.success}")
    print(f"  ✓ Optimal energy:  {result.optimal_energy:.6f} Hartree")
    print(f"  ✓ Exact energy:    {exact_energy:.6f} Hartree")
    print(f"  ✓ Error:           {abs(result.optimal_energy - exact_energy):.6f} Hartree")
    for i, p in enumerate(all_params):
        print(f"  ✓ {p.name}:  {result.optimal_params[i]:+.4f}")
    print(f"  ✓ Iterations:      {result.num_iterations}")
    print(f"  ✓ Circuit evals:   {result.num_circuit_evaluations}")
    print()

    # 5. Show convergence
    if result.convergence_history:
        print("  Convergence (last 10 steps):")
        history = result.convergence_history
        start = max(0, len(history) - 10)
        for i, e in enumerate(history[start:], start=start + 1):
            bar = "█" * int(max(0, (e - exact_energy) * 100))
            print(f"    Step {i:3d}: {e:+.6f}  {bar}")

    print()
    print("=" * 60)
    print("  Done! The VQE found an energy close to the exact value.")
    print("=" * 60)
