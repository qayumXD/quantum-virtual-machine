# Tutorial 5: Variational Quantum Eigensolver (VQE)

The **Variational Quantum Eigensolver (VQE)** is a leading hybrid quantum-classical algorithm that computes the ground-state energy of quantum systems by combining shallow parameterized quantum circuits with classical optimizers.

---

## Learning Objectives

1. Understand the Rayleigh-Ritz variational principle: $\langle H \rangle_{\vec{\theta}} \ge E_0$.
2. Formulate molecular Hamiltonians using Pauli operators.
3. Design a hardware-efficient parameterized quantum ansatz $U(\vec{\theta})$.
4. Evaluate expectation values $\langle H \rangle_{\vec{\theta}}$ using QVM's `Hamiltonian` and `Simulator`.
5. Optimize variational parameters to find the molecular hydrogen ground-state energy.

---

## Molecular Hydrogen ($\text{H}_2$) STO-3G Ground State

In the STO-3G minimal basis at $R = 0.735\text{ \AA}$, the $\text{H}_2$ Hamiltonian is:

$$H = c_0 I + c_1 Z_0 + c_2 Z_1 + c_3 Z_0 Z_1 + c_4 X_0 X_1$$

Where:
*   $c_0 = -1.052373$ (nuclear repulsion & constant offset)
*   $c_1 = -0.397937$, $c_2 = 0.397937$, $c_3 = -0.011280$, $c_4 = 0.180931$
*   Target ground state energy: $E_0 = -1.137306\text{ Ha}$

---

## Python Implementation

```python
import numpy as np
from scipy.optimize import minimize
from qvm.ir import QuantumCircuit
from qvm.simulator import Simulator
from qvm.observable import Hamiltonian

OFFSET = -1.052373245772859
H = Hamiltonian.from_dict({
    "ZI": -0.39793742484318045,
    "IZ":  0.39793742484318045,
    "ZZ": -0.01128010425623538,
    "XX":  0.18093119978423156,
})

def ansatz(p):
    a, b, c, d = p
    qc = QuantumCircuit(2)
    qc.add_operation("ry", [0], params=[a])
    qc.add_operation("ry", [1], params=[b])
    qc.add_operation("cx", [0, 1])
    qc.add_operation("ry", [1], params=[c])
    qc.add_operation("cx", [0, 1])
    qc.add_operation("ry", [0], params=[d])
    return qc

sim = Simulator()

def energy(p):
    return OFFSET + sim.expectation_value(ansatz(p), H)

# Optimize with Nelder-Mead
best = min(
    minimize(energy, s, method="Nelder-Mead", options={"maxiter": 400, "fatol": 1e-8}).fun
    for s in np.random.default_rng(42).uniform(-np.pi, np.pi, (5, 4))
)

exact = float(np.linalg.eigvalsh(H.to_matrix(2) + OFFSET * np.eye(4))[0])
print(f"VQE Computed : {best:.6f} Ha")
print(f"Exact Energy : {exact:.6f} Ha")
assert abs(best - exact) < 1e-4, "VQE error exceeded tolerance!"
print("VQE optimization successfully found the ground state of H2!")
```

Reference: [API Reference](../guides/API_REFERENCE.md).
