# Tutorial 4: Quantum Teleportation

Quantum teleportation transmits an unknown state $|\psi\rangle$ from Alice to Bob using an entangled EPR pair and two classical bits. It demonstrates **mid-circuit measurement** and **classical feedforward** in dynamic quantum circuits.

---

## Learning Objectives

1. Understand the 3-qubit quantum teleportation protocol.
2. Formulate state evolution across Alice ($q_0, q_1$) and Bob ($q_2$).
3. Implement mid-circuit measurements and conditional branch corrections in OpenQASM 3.0.
4. Verify using QVM's stochastic trajectory sampler that Bob's qubit accurately inherits Alice's arbitrary state.

---

## OpenQASM 3.0 Teleportation Circuit

```qasm
OPENQASM 3.0;
include "stdgates.inc";

qubit[3] q;
bit[2] mid;
bit[1] out;

// 1. Alice prepares unknown state Ry(0.8)|0> on q[0]
ry(0.8) q[0];

// 2. Entangled Bell pair on q[1] & q[2]
h q[1];
cx q[1], q[2];

// 3. Bell-basis measurement by Alice
cx q[0], q[1];
h q[0];
mid[0] = measure q[0];
mid[1] = measure q[1];

// 4. Bob applies conditional Pauli corrections
if (mid[1] == 1) {
    x q[2];
}
if (mid[0] == 1) {
    z q[2];
}

// 5. Measure Bob's qubit
out[0] = measure q[2];
```

---

## Python Verification

```python
import math
from qvm.qasm3_parser import OpenQASM3Parser
from qvm.simulator import Simulator

THETA = 0.8
SHOTS = 5000

qasm = f"""OPENQASM 3.0;
include "stdgates.inc";
qubit[3] q;
bit[2] mid;
bit[1] out;
ry({THETA}) q[0];
h q[1];
cx q[1], q[2];
cx q[0], q[1];
h q[0];
mid[0] = measure q[0];
mid[1] = measure q[1];
if (mid[1] == 1) {{ x q[2]; }}
if (mid[0] == 1) {{ z q[2]; }}
out[0] = measure q[2];
"""

teleport = OpenQASM3Parser().parse(qasm)
counts = Simulator().sample(teleport, shots=SHOTS, seed=42)

p_one = sum(c for bits, c in counts.items() if bits[2] == "1") / SHOTS
theory_p_one = math.sin(THETA / 2) ** 2

print(f"P(q[2] = 1) observed: {p_one:.4f}, theoretical: {theory_p_one:.4f}")
assert abs(p_one - theory_p_one) < 0.02
print("Quantum teleportation protocol verified!")
```

Next tutorial: [Tutorial 5: Variational Quantum Eigensolver](05_variational_quantum_eigensolver.md).
