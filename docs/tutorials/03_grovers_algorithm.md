# Tutorial 3: Grover's Search Algorithm

Grover's algorithm searches an unsorted database of $N = 2^n$ elements in $O(\sqrt{N})$ query steps, providing a provable quadratic speedup over the best possible classical algorithm ($O(N)$ queries).

In this tutorial, you will construct, execute, and verify a 3-qubit Grover search circuit targeting the specific marked element $|101\rangle$ ($5$ in decimal) using OpenQASM 3.0 and the Quantum Virtual Machine (QVM).

---

## Learning Objectives

1. Understand the geometry of Grover's algorithm: state space rotation via reflections.
2. Implement a phase oracle $U_\omega$ that selectively flips the phase of $|101\rangle$.
3. Construct the Grover diffusion operator $D$ (inversion about the average).
4. Calculate the optimal iteration count $R \approx \left\lfloor \frac{\pi}{4}\sqrt{N} \right\rfloor$.
5. Validate QVM's simulated amplitudes against exact analytical formulas.

---

## Mathematical Formulation

*   **Initial Superposition**:
    $$|s\rangle = H^{\otimes 3}|000\rangle = \frac{1}{\sqrt{8}}\sum_{x=0}^7 |x\rangle$$

*   **Oracle ($U_\omega$)**:
    $$U_\omega |x\rangle = (-1)^{f(x)} |x\rangle$$
    For target $|101\rangle$:
    ```qasm
    x q[1];
    h q[1];
    ccx q[0], q[2], q[1];
    h q[1];
    x q[1];
    ```

*   **Diffusion Operator ($D$)**:
    $$D = 2|s\rangle\langle s| - I = H^{\otimes 3} (2|000\rangle\langle 000| - I) H^{\otimes 3}$$
    ```qasm
    h q[0]; h q[1]; h q[2];
    x q[0]; x q[1]; x q[2];
    h q[2];
    ccx q[0], q[1], q[2];
    h q[2];
    x q[0]; x q[1]; x q[2];
    h q[0]; h q[1]; h q[2];
    ```

*   **Optimal Iterations**:
    $$R = \lfloor \frac{\pi}{4}\sqrt{8} \rfloor = 2 \text{ iterations} \implies P(|101\rangle) \approx 94.5\%$$

---

## Verified Python Code

```python
import math
import numpy as np
from qvm.qasm3_parser import OpenQASM3Parser
from qvm.simulator import Simulator

ORACLE = "x q[1]; h q[1]; ccx q[0], q[2], q[1]; h q[1]; x q[1];"
DIFFUSER = (
    "h q[0]; h q[1]; h q[2];"
    "x q[0]; x q[1]; x q[2];"
    "h q[2]; ccx q[0], q[1], q[2]; h q[2];"
    "x q[0]; x q[1]; x q[2];"
    "h q[0]; h q[1]; h q[2];"
)

N_ITER = int(math.floor(math.pi / 4 * math.sqrt(8)))  # 2

qasm_src = f"""OPENQASM 3.0;
include "stdgates.inc";
qubit[3] q;
h q[0]; h q[1]; h q[2];
{(ORACLE + DIFFUSER) * N_ITER}
"""

grover = OpenQASM3Parser().parse(qasm_src)
state, _ = Simulator().simulate(grover)
probs = np.abs(state) ** 2

print({format(i, "03b"): round(p, 3) for i, p in enumerate(probs) if p > 0.02})
assert round(probs[5], 3) == 0.945, "Failed Grover amplification!"
print("Grover search successfully amplifies |101> to 94.5% probability!")
```

Next tutorial: [Tutorial 4: Quantum Teleportation](04_quantum_teleportation.md).
