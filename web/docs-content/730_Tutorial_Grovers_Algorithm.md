---
tags: [tutorial, grover, quantum-search, oracle, diffusion-operator, openqasm3]
---

# Tutorial 3: Grover's Search Algorithm

Grover's algorithm searches an unsorted database of $N = 2^n$ elements in $O(\sqrt{N})$ query steps, providing a provable quadratic speedup over the best possible classical algorithm ($O(N)$ queries).

In this tutorial, you will construct, execute, and verify a 3-qubit Grover search circuit targeting the specific marked element $|101\rangle$ ($5$ in decimal) using OpenQASM 3.0 and the Quantum Virtual Machine (QVM).

---

## 🎯 Learning Objectives

1. Understand the geometry of Grover's algorithm: state space rotation via reflections.
2. Implement a phase oracle $U_\omega$ that selectively flips the phase of $|101\rangle$.
3. Construct the Grover diffusion operator $D$ (inversion about the average).
4. Calculate the optimal iteration count $R \approx \left\lfloor \frac{\pi}{4}\sqrt{N} \right\rfloor$.
5. Validate QVM's simulated amplitudes against exact analytical formulas.

---

## 🔬 Mathematical Theory

### 1. Geometric Intuition
The search space of $N = 8$ items is initialized into an equal superposition:

$$|s\rangle = \frac{1}{\sqrt{N}} \sum_{x=0}^{N-1} |x\rangle = H^{\otimes 3}|000\rangle$$

Let $|\omega\rangle = |101\rangle$ be the marked target state, and $|s'\rangle = \frac{1}{\sqrt{N-1}} \sum_{x \neq \omega} |x\rangle$ be the superposition of all non-target states. In the 2D plane spanned by $\{|s'\rangle, |\omega\rangle\}$, the initial state makes an angle $\theta/2$ with $|s'\rangle$ where:

$$\sin\left(\frac{\theta}{2}\right) = \frac{1}{\sqrt{N}} = \frac{1}{\sqrt{8}} \approx 0.3536$$

### 2. The Phase Oracle ($U_\omega$)
The oracle evaluates the boolean predicate $f(x) \in \{0, 1\}$ and flips the sign of the target item:

$$U_\omega |x\rangle = (-1)^{f(x)} |x\rangle = \begin{cases} -|x\rangle & \text{if } x = |101\rangle \\ +|x\rangle & \text{if } x \neq |101\rangle \end{cases}$$

For the target $|101\rangle = |q_2 q_1 q_0\rangle$ (where $q_0=1, q_1=0, q_2=1$):
*   Qubit 1 is flipped with an $X$ gate so all controls become $1$ when the state is $|101\rangle$.
*   A controlled phase flip is enacted using a Toffoli gate ($CCX$) flanked by Hadamards on the target.
*   Qubit 1 is flipped back with an $X$ gate.

```qasm
// Oracle for |101>
x q[1];
h q[1];
ccx q[0], q[2], q[1];
h q[1];
x q[1];
```

### 3. The Diffusion Operator ($D$)
The diffusion operator inverts probability amplitudes about their mean:

$$D = 2|s\rangle\langle s| - I = H^{\otimes n} \left( 2|0\rangle^{\otimes n}\langle 0|^{\otimes n} - I \right) H^{\otimes n}$$

In circuit form for 3 qubits:
1. Apply $H$ on all qubits.
2. Apply $X$ on all qubits.
3. Apply a multi-controlled-$Z$ (realized as $H$ on $q[2]$, $CCX(q[0], q[1], q[2])$, followed by $H$ on $q[2]$).
4. Apply $X$ on all qubits.
5. Apply $H$ on all qubits.

```qasm
// Diffusion Operator
h q[0]; h q[1]; h q[2];
x q[0]; x q[1]; x q[2];
h q[2];
ccx q[0], q[1], q[2];
h q[2];
x q[0]; x q[1]; x q[2];
h q[0]; h q[1]; h q[2];
```

### 4. Optimal Iteration Count
For $N = 8$:

$$R = \left\lfloor \frac{\pi}{4}\sqrt{8} \right\rfloor = \lfloor 2.221 \rfloor = 2 \text{ iterations}$$

After $2$ iterations, the probability of measuring the target $|101\rangle$ reaches:

$$P(|101\rangle) \approx 94.5\%$$

---

## 💻 Verified Python Implementation

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

N_ITER = int(math.floor(math.pi / 4 * math.sqrt(8)))  # 2 iterations

# Construct the complete OpenQASM 3.0 program
qasm_source = f"""OPENQASM 3.0;
include "stdgates.inc";
qubit[3] q;

// Equal superposition
h q[0];
h q[1];
h q[2];

// Grover Iterations
{(ORACLE + DIFFUSER) * N_ITER}
"""

grover_circuit = OpenQASM3Parser().parse(qasm_source)
state, _ = Simulator().simulate(grover_circuit)
probs = np.abs(state) ** 2

print("Significant measurement probabilities (P > 0.02):")
for idx, p in enumerate(probs):
    if p > 0.02:
        print(f"|{format(idx, '03b')}>: {p:.4f} ({p*100:.1f}%)")

# Compare against exact analytical Grover formula
amps = np.full(8, 1.0 / math.sqrt(8))
for _ in range(N_ITER):
    amps[5] *= -1                   # Target index 5 is |101>
    amps = 2 * np.mean(amps) - amps # Inversion about mean

expected_probs = np.abs(amps) ** 2
assert np.allclose(probs, expected_probs, atol=1e-7), "Simulation diverged from theory!"
print("\nSuccess: QVM simulation matches the analytical Grover amplification exactly!")
```

### Verified Execution Output
```text
Significant measurement probabilities (P > 0.02):
|101>: 0.9453 (94.5%)

Success: QVM simulation matches the analytical Grover amplification exactly!
```

---

## 🌐 Running via QVM CLI & REST API

### Running via CLI
Save the generated QASM to `grover.qasm`:
```bash
qvm grover.qasm --shots 1000 --seed 123
```

### Running via REST API (`POST /run`)
```bash
curl -X POST "http://127.0.0.1:8000/run" \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "qasm",
    "qasm": "OPENQASM 3.0;\ninclude \"stdgates.inc\";\nqubit[3] q;\nh q[0]; h q[1]; h q[2];\nx q[1]; h q[1]; ccx q[0], q[2], q[1]; h q[1]; x q[1];\nh q[0]; h q[1]; h q[2]; x q[0]; x q[1]; x q[2]; h q[2]; ccx q[0], q[1], q[2]; h q[2]; x q[0]; x q[1]; x q[2]; h q[0]; h q[1]; h q[2];\nx q[1]; h q[1]; ccx q[0], q[2], q[1]; h q[1]; x q[1];\nh q[0]; h q[1]; h q[2]; x q[0]; x q[1]; x q[2]; h q[2]; ccx q[0], q[1], q[2]; h q[2]; x q[0]; x q[1]; x q[2]; h q[0]; h q[1]; h q[2];",
    "shots": 2000,
    "seed": 42
  }'
```

In the response:
*   `counts["101"]` will be approximately `1890` out of `2000` (~$94.5\%$).
*   The `histogram_plot` will clearly show one dominant bar at index `5` ($|101\rangle$).

Next tutorial: [Tutorial 4: Quantum Teleportation](/docs/740_Tutorial_Quantum_Teleportation).
