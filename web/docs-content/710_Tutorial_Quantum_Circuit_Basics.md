---
tags: [tutorial, quantum-basics, beginner, openqasm, circuit-execution]
---

# Tutorial 1: Quantum Circuit Basics

Welcome to the foundational tutorial for the **Quantum Virtual Machine (QVM)**. This tutorial introduces the core concepts of quantum computation—qubits, quantum logic gates, measurement, and circuit execution—grounded in QVM's actual execution pipeline.

---

## 🎯 Learning Objectives

By completing this tutorial, you will:
1. Understand the state representation of a single qubit ($|0\rangle$, $|1\rangle$, and superpositions).
2. Apply fundamental quantum gates ($X$, $H$, and $R_y$).
3. Construct and run your first quantum circuit using **Python IR**, **OpenQASM**, and the **REST API**.
4. Read and interpret statevector probability amplitudes versus shot-based sampling counts.

---

## 🔬 Core Theory: Qubits and Quantum Gates

### 1. The Qubit State
A classical bit can only be in state $0$ or $1$. A quantum bit (qubit) lives in a 2-dimensional complex Hilbert space:

$$|\psi\rangle = \alpha |0\rangle + \beta |1\rangle = \alpha \begin{pmatrix} 1 \\ 0 \end{pmatrix} + \beta \begin{pmatrix} 0 \\ 1 \end{pmatrix}$$

where $\alpha, \beta \in \mathbb{C}$ are complex probability amplitudes satisfying the normalization constraint:

$$|\alpha|^2 + |\beta|^2 = 1$$

When measured in the computational basis ($Z$-basis), the probability of finding the qubit in state $|0\rangle$ is $P(0) = |\alpha|^2$, and in state $|1\rangle$ is $P(1) = |\beta|^2$.

### 2. Quantum Gates
Quantum operations are represented by unitary matrices ($U^\dagger U = I$). Key single-qubit gates supported natively by QVM include:

*   **Pauli-X (Bit-flip gate)**:
    $$X = \begin{pmatrix} 0 & 1 \\ 1 & 0 \end{pmatrix}, \quad X|0\rangle = |1\rangle, \quad X|1\rangle = |0\rangle$$

*   **Hadamard Gate ($H$)**: Creates an equal superposition:
    $$H = \frac{1}{\sqrt{2}}\begin{pmatrix} 1 & 1 \\ 1 & -1 \end{pmatrix}, \quad H|0\rangle = \frac{|0\rangle + |1\rangle}{\sqrt{2}} \equiv |+\rangle$$

*   **Rotation-Y Gate ($R_y(\theta)$)**:
    $$R_y(\theta) = \exp\left(-i\frac{\theta}{2}Y\right) = \begin{pmatrix} \cos(\theta/2) & -\sin(\theta/2) \\ \sin(\theta/2) & \cos(\theta/2) \end{pmatrix}$$

---

## 💻 Method 1: Python API Execution

You can build and simulate circuits directly in Python using `qvm.ir.QuantumCircuit` and `qvm.simulator.Simulator`.

```python
from qvm.ir import QuantumCircuit
from qvm.simulator import Simulator
import numpy as np

# 1. Instantiate a 1-qubit circuit with 1 classical bit register
qc = QuantumCircuit(1)
qc.add_register("c", 1)

# 2. Apply Hadamard to create superposition (|0> -> (|0> + |1>)/sqrt(2))
qc.add_operation("h", [0])

# 3. Add measurement operation
qc.add_operation("measure", [0], register="c", cbit=0)

# 4. Simulate exact statevector
sim = Simulator()
state, mem = sim.simulate(qc)
probabilities = np.abs(state) ** 2

print("Statevector:", state)
print("Probabilities (|0>, |1>):", probabilities.round(4))

# 5. Perform shot-based sampling (1000 shots)
counts = sim.sample(qc, shots=1000, seed=42)
print("Measurement counts (1000 shots):", counts)
```

### Expected Output
```text
Statevector: [0.70710678+0.j 0.70710678+0.j]
Probabilities (|0>, |1>): [0.5 0.5]
Measurement counts (1000 shots): {'0': 508, '1': 492}
```

---

## 📝 Method 2: OpenQASM 3.0 Program

QVM includes a full OpenQASM 3 parser. You can write your circuit in standard OpenQASM 3.0 text:

```qasm
OPENQASM 3.0;
include "stdgates.inc";

qubit[1] q;
bit[1] c;

// Put qubit 0 into equal superposition
h q[0];

// Measure qubit 0 into classical register c[0]
c[0] = measure q[0];
```

To run this with QVM CLI:
```bash
qvm circuit.qasm --shots 1000 --seed 42
```

---

## 🌐 Method 3: REST API (`/run`)

You can execute the exact same circuit over HTTP via the QVM FastAPI backend.

### Request (`curl`)
```bash
curl -X POST "http://127.0.0.1:8000/run" \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "json",
    "nqubits": 1,
    "circuit": [
      {"name": "h", "qubits": [0]},
      {"name": "measure", "qubits": [0], "register": "c", "cbit": 0}
    ],
    "shots": 1000,
    "seed": 42
  }'
```

### JSON Response
```json
{
  "probabilities": [0.5, 0.5],
  "classical_memory": {"c": [1]},
  "transpiled_operations": [
    {"name": "h", "qubits": [0]},
    {"name": "measure", "qubits": [0], "register": "c", "cbit": 0}
  ],
  "nqubits": 1,
  "circuit_plot": "iVBORw0KGgoAAAANSUhEUg...",
  "histogram_plot": "iVBORw0KGgoAAAANSUhEUg...",
  "counts": {"0": 508, "1": 492},
  "openqasm2": "OPENQASM 2.0;\ninclude \"qelib1.inc\";\nqreg q[1];\ncreg c[1];\nh q[0];\nmeasure q[0] -> c[0];\n",
  "expectation_value": null,
  "noise_summary": null
}
```

---

## 📊 Summary & Key Takeaways

1. **Statevector vs. Sampling**: `probabilities` in QVM yields exact analytical values ($|\psi_i|^2$). When `shots > 0`, QVM simulates real quantum projective measurements returning integer count frequencies.
2. **Canonical IR**: Every circuit regardless of input language is lowered into QVM's internal representation, enabling seamless conversion to Qiskit (`qc.to_qiskit()`) and Cirq (`qc.to_cirq()`).

Next tutorial: [Tutorial 2: Quantum Entanglement & Bell States](/docs/720_Tutorial_Quantum_Entanglement).
