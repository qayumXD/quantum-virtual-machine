# 🔬 Quantum Virtual Machine - Code Examples & Explanations

**Last Updated:** April 28, 2026  
**Purpose:** Detailed code examples in JSON and OpenQASM 3.0 with explanations

---

## 📋 Table of Contents

1. [Bell State (Entanglement)](#bell-state-entanglement)
2. [Bernstein-Vazirani Algorithm](#bernstein-vazirani-algorithm)
3. [Grover's Search Algorithm](#grovers-search-algorithm)
4. [Advanced Examples](#advanced-examples)
5. [API Request Examples](#api-request-examples)

---

## 🔔 Bell State (Entanglement)

### What is a Bell State?

A Bell state is a maximally entangled state of two qubits. It demonstrates quantum entanglement where measuring one qubit instantly determines the state of the other, regardless of distance.

### The Bell State |Φ+⟩

**Mathematical Definition:**
```
|Φ+⟩ = (|00⟩ + |11⟩) / √2
```

This means:
- 50% probability of measuring both qubits as 0 (|00⟩)
- 50% probability of measuring both qubits as 1 (|11⟩)
- 0% probability of measuring |01⟩ or |10⟩

### JSON Format

```json
[
    {"name": "h", "qubits": [0]},
    {"name": "cx", "qubits": [0, 1]}
]
```

**Explanation:**
1. **H gate on qubit 0**: Hadamard gate creates superposition
   - Input: |0⟩
   - Output: (|0⟩ + |1⟩) / √2
   - Effect: Equal superposition of 0 and 1

2. **CNOT gate (qubits 0→1)**: Controlled-NOT gate
   - Control qubit: 0
   - Target qubit: 1
   - Effect: If qubit 0 is 1, flip qubit 1
   - Result: Entangles the two qubits

### OpenQASM 3.0 Format

```qasm
OPENQASM 3.0;
qubit[2] q;

// Create superposition on qubit 0
h q[0];

// Entangle qubit 1 with qubit 0
cx q[0], q[1];
```

**Line-by-line:**
- `OPENQASM 3.0;` - Specify OpenQASM version 3.0
- `qubit[2] q;` - Declare 2 qubits named 'q'
- `h q[0];` - Apply Hadamard to qubit 0
- `cx q[0], q[1];` - Apply CNOT with control=0, target=1

### Run It

```bash
# Using CLI
python -m src.qvm.cli examples/bell_state.json --nqubits 2

# With sampling (1000 shots)
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --shots 1000

# With visualization
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --visualize

# With transpilation
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --transpile --routing sabre
```

### Expected Output

**Probabilities:**
```
Probabilities: [0.5, 0.0, 0.0, 0.5]
```
- |00⟩: 50%
- |01⟩: 0%
- |10⟩: 0%
- |11⟩: 50%

**Counts (with 1000 shots):**
```json
{
  "00": 512,
  "11": 488
}
```

### Why This Matters

- **Quantum Entanglement**: Demonstrates non-local correlations
- **Quantum Teleportation**: Bell states are used in quantum teleportation protocols
- **Quantum Cryptography**: Foundation for quantum key distribution
- **Quantum Computing**: Building block for many quantum algorithms

---

## 🔍 Bernstein-Vazirani Algorithm

### What is Bernstein-Vazirani?

The Bernstein-Vazirani algorithm finds a hidden bitstring using only **one quantum query**, while a classical computer would need **2^n queries** in the worst case.

### The Problem

Given a function f(x) = a·x (mod 2), where:
- x is an n-bit input
- a is a hidden n-bit string
- · is bitwise AND
- (mod 2) is XOR

Find the hidden string 'a' with minimum queries.

### The Solution: Secret = "101"

**Mathematical Concept:**
```
The algorithm uses quantum phase kickback to encode the secret
into the phase of the quantum state, then extracts it with Hadamard.
```

### JSON Format

```json
[
    {"name": "h", "qubits": [0]},
    {"name": "h", "qubits": [1]},
    {"name": "h", "qubits": [2]},
    {"name": "x", "qubits": [3]},
    {"name": "h", "qubits": [3]},
    {"name": "cx", "qubits": [0, 3]},
    {"name": "cx", "qubits": [2, 3]},
    {"name": "h", "qubits": [0]},
    {"name": "h", "qubits": [1]},
    {"name": "h", "qubits": [2]}
]
```

**Step-by-step Explanation:**

1. **Initialize input qubits (0, 1, 2) to superposition:**
   ```json
   {"name": "h", "qubits": [0]},
   {"name": "h", "qubits": [1]},
   {"name": "h", "qubits": [2]}
   ```
   - Creates: (|0⟩ + |1⟩)^⊗3 / √8
   - All 8 basis states in superposition

2. **Initialize ancilla qubit (3) to |−⟩ state:**
   ```json
   {"name": "x", "qubits": [3]},
   {"name": "h", "qubits": [3]}
   ```
   - X gate: |0⟩ → |1⟩
   - H gate: |1⟩ → (|0⟩ - |1⟩) / √2 = |−⟩

3. **Apply Oracle (encodes secret "101"):**
   ```json
   {"name": "cx", "qubits": [0, 3]},
   {"name": "cx", "qubits": [2, 3]}
   ```
   - CNOT from qubit 0 to ancilla (secret bit 1)
   - CNOT from qubit 2 to ancilla (secret bit 1)
   - Qubit 1 has no CNOT (secret bit 0)
   - Effect: Encodes "101" into phase

4. **Apply Hadamard basis change:**
   ```json
   {"name": "h", "qubits": [0]},
   {"name": "h", "qubits": [1]},
   {"name": "h", "qubits": [2]}
   ```
   - Converts phase information to measurable amplitudes
   - Result: Measurement yields "101" with high probability

### OpenQASM 3.0 Format

```qasm
OPENQASM 3.0;
qubit[4] q;

// Step 1: Initialize input qubits to superposition
h q[0];
h q[1];
h q[2];

// Step 2: Initialize ancilla to |−⟩
x q[3];
h q[3];

// Step 3: Oracle for secret "101"
// Apply CNOT for each '1' bit in secret
cx q[0], q[3];  // Secret bit 0 is 1
cx q[2], q[3];  // Secret bit 2 is 1
// No CNOT for q[1] because secret bit 1 is 0

// Step 4: Hadamard basis change
h q[0];
h q[1];
h q[2];
```

### Run It

```bash
# Using CLI
python -m src.qvm.cli examples/bv_101.json --nqubits 4

# With sampling
python -m src.qvm.cli examples/bv_101.json --nqubits 4 --shots 1000

# With transpilation
python -m src.qvm.cli examples/bv_101.json --nqubits 4 --transpile --routing sabre

# Generate custom secret
python examples/generate_bv.py --secret 110 --output examples/bv_110.json
python -m src.qvm.cli examples/bv_110.json --nqubits 4 --shots 1000
```

### Expected Output

**Probabilities:**
```
Probabilities: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
```
- Index 5 (binary 0101 = "101" for input qubits): 50%
- All others: 0%
- Ancilla qubit remains in superposition

**Counts (with 1000 shots):**
```json
{
  "0101": 512,
  "1101": 488
}
```
- First 3 bits: "101" (the secret)
- Last bit: ancilla in superposition (0 or 1)

### Why This Matters

- **Exponential Speedup**: 1 query vs 2^n queries
- **Quantum Advantage**: First algorithm showing quantum speedup
- **Phase Kickback**: Demonstrates quantum phase encoding
- **Foundation**: Basis for many quantum algorithms

---

## 🔎 Grover's Search Algorithm

### What is Grover's Algorithm?

Grover's algorithm searches an unsorted database of N items for a marked item with **√N queries**, compared to N/2 queries classically. This is a quadratic speedup.

### The Problem

Given N items and a function that marks one item as "correct", find the marked item.

Example: Search 8 items (3 qubits) for item "101"

### The Solution: Searching for "101"

**Key Concept:**
```
Grover amplifies the amplitude of the marked state while
suppressing amplitudes of unmarked states through repeated
oracle + diffusion operations.
```

### JSON Format (Simplified - 2 iterations)

```json
[
    {"name": "h", "qubits": [0]},
    {"name": "h", "qubits": [1]},
    {"name": "h", "qubits": [2]},
    {"name": "x", "qubits": [1]},
    {"name": "h", "qubits": [2]},
    {"name": "toffoli", "qubits": [0, 1, 2]},
    {"name": "h", "qubits": [2]},
    {"name": "x", "qubits": [1]},
    {"name": "h", "qubits": [0]},
    {"name": "h", "qubits": [1]},
    {"name": "h", "qubits": [2]},
    {"name": "x", "qubits": [0]},
    {"name": "x", "qubits": [1]},
    {"name": "x", "qubits": [2]},
    {"name": "h", "qubits": [2]},
    {"name": "toffoli", "qubits": [0, 1, 2]},
    {"name": "h", "qubits": [2]},
    {"name": "x", "qubits": [0]},
    {"name": "x", "qubits": [1]},
    {"name": "x", "qubits": [2]},
    {"name": "h", "qubits": [0]},
    {"name": "h", "qubits": [1]},
    {"name": "h", "qubits": [2]}
]
```

**Step-by-step Explanation:**

1. **Initialize to uniform superposition:**
   ```json
   {"name": "h", "qubits": [0]},
   {"name": "h", "qubits": [1]},
   {"name": "h", "qubits": [2]}
   ```
   - Creates: (|000⟩ + |001⟩ + ... + |111⟩) / √8
   - Equal amplitude for all 8 states

2. **First Grover Iteration:**

   a) **Oracle (marks |101⟩):**
   ```json
   {"name": "x", "qubits": [1]},
   {"name": "h", "qubits": [2]},
   {"name": "toffoli", "qubits": [0, 1, 2]},
   {"name": "h", "qubits": [2]},
   {"name": "x", "qubits": [1]}
   ```
   - X gates: Flip qubits to check for |101⟩
   - Toffoli: Multi-controlled gate (CCX)
   - Effect: Applies -1 phase to |101⟩

   b) **Diffusion operator (amplifies marked state):**
   ```json
   {"name": "h", "qubits": [0]},
   {"name": "h", "qubits": [1]},
   {"name": "h", "qubits": [2]},
   {"name": "x", "qubits": [0]},
   {"name": "x", "qubits": [1]},
   {"name": "x", "qubits": [2]},
   {"name": "h", "qubits": [2]},
   {"name": "toffoli", "qubits": [0, 1, 2]},
   {"name": "h", "qubits": [2]},
   {"name": "x", "qubits": [0]},
   {"name": "x", "qubits": [1]},
   {"name": "x", "qubits": [2]}
   ```
   - Hadamard: Change basis
   - X gates: Flip all qubits
   - Toffoli: Multi-controlled phase
   - Effect: Amplifies marked state, suppresses others

3. **Second Grover Iteration:**
   - Repeat oracle + diffusion
   - Further amplifies |101⟩

4. **Final Hadamard:**
   ```json
   {"name": "h", "qubits": [0]},
   {"name": "h", "qubits": [1]},
   {"name": "h", "qubits": [2]}
   ```
   - Measurement now yields |101⟩ with ~94% probability

### OpenQASM 3.0 Format

```qasm
OPENQASM 3.0;
qubit[3] q;

// Initialize to uniform superposition
h q[0];
h q[1];
h q[2];

// Grover iteration 1
// Oracle: mark |101⟩
x q[1];
h q[2];
toffoli q[0], q[1], q[2];
h q[2];
x q[1];

// Diffusion operator
h q[0];
h q[1];
h q[2];
x q[0];
x q[1];
x q[2];
h q[2];
toffoli q[0], q[1], q[2];
h q[2];
x q[0];
x q[1];
x q[2];

// Grover iteration 2 (repeat oracle + diffusion)
x q[1];
h q[2];
toffoli q[0], q[1], q[2];
h q[2];
x q[1];

h q[0];
h q[1];
h q[2];
x q[0];
x q[1];
x q[2];
h q[2];
toffoli q[0], q[1], q[2];
h q[2];
x q[0];
x q[1];
x q[2];

// Final measurement basis
h q[0];
h q[1];
h q[2];
```

### Run It

```bash
# Using CLI
python -m src.qvm.cli examples/grover_101.json --nqubits 3

# With sampling
python -m src.qvm.cli examples/grover_101.json --nqubits 3 --shots 1000

# With transpilation
python -m src.qvm.cli examples/grover_101.json --nqubits 3 --transpile --routing sabre

# Generate custom target
python examples/generate_grover.py --target 110 --output examples/grover_110.json
python -m src.qvm.cli examples/grover_110.json --nqubits 3 --shots 1000
```

### Expected Output

**Probabilities:**
```
Probabilities: [0.0, 0.0, 0.0, 0.0, 0.0, 0.94, 0.0, 0.0]
```
- Index 5 (binary 101): 94%
- Others: ~1% each

**Counts (with 1000 shots):**
```json
{
  "101": 940,
  "001": 15,
  "011": 20,
  "111": 25
}
```
- "101" (target): 940 counts
- Others: ~20 counts each (noise/error)

### Why This Matters

- **Quadratic Speedup**: √N vs N
- **Database Search**: Practical application for searching
- **Amplitude Amplification**: Core technique in quantum algorithms
- **Quantum Advantage**: Demonstrates quantum speedup for search

---

## 🚀 Advanced Examples

### Example 1: Quantum Fourier Transform (QFT)

```json
[
    {"name": "h", "qubits": [0]},
    {"name": "rz", "qubits": [0], "params": [1.5708]},
    {"name": "h", "qubits": [1]},
    {"name": "rz", "qubits": [1], "params": [0.7854]},
    {"name": "h", "qubits": [2]}
]
```

**OpenQASM 3.0:**
```qasm
OPENQASM 3.0;
qubit[3] q;

// QFT on 3 qubits (simplified)
h q[0];
rz(π/2) q[0];

h q[1];
rz(π/4) q[1];

h q[2];
```

**What it does:**
- Transforms quantum state to frequency domain
- Used in Shor's algorithm for factoring
- Basis for phase estimation

### Example 2: Quantum Phase Estimation

```json
[
    {"name": "h", "qubits": [0]},
    {"name": "h", "qubits": [1]},
    {"name": "h", "qubits": [2]},
    {"name": "rz", "qubits": [3], "params": [0.5]},
    {"name": "rz", "qubits": [3], "params": [1.0]},
    {"name": "rz", "qubits": [3], "params": [2.0]}
]
```

**What it does:**
- Estimates eigenvalues of unitary operators
- Foundation for many quantum algorithms
- Used in variational quantum algorithms

### Example 3: Quantum Amplitude Amplification

```json
[
    {"name": "h", "qubits": [0]},
    {"name": "h", "qubits": [1]},
    {"name": "x", "qubits": [0]},
    {"name": "h", "qubits": [1]},
    {"name": "cx", "qubits": [0, 1]},
    {"name": "h", "qubits": [1]},
    {"name": "x", "qubits": [0]},
    {"name": "h", "qubits": [0]},
    {"name": "h", "qubits": [1]}
]
```

**What it does:**
- Generalizes Grover's algorithm
- Amplifies any quantum state
- Used in quantum machine learning

---

## 📡 API Request Examples

### Example 1: Bell State via API

```bash
curl -X POST http://127.0.0.1:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "json",
    "circuit": [
      {"name": "h", "qubits": [0]},
      {"name": "cx", "qubits": [0, 1]}
    ],
    "nqubits": 2,
    "shots": 1000,
    "seed": 42
  }'
```

**Response:**
```json
{
  "probabilities": [0.5, 0.0, 0.0, 0.5],
  "counts": {
    "00": 512,
    "11": 488
  },
  "transpiled_operations": [
    {"name": "h", "qubits": [0]},
    {"name": "cx", "qubits": [0, 1]}
  ],
  "nqubits": 2,
  "openqasm2": "OPENQASM 2.0;\ninclude \"qelib1.inc\";\nqreg q[2];\nh q[0];\ncx q[0],q[1];"
}
```

### Example 2: Bernstein-Vazirani via API

```bash
curl -X POST http://127.0.0.1:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "json",
    "circuit": [
      {"name": "h", "qubits": [0]},
      {"name": "h", "qubits": [1]},
      {"name": "h", "qubits": [2]},
      {"name": "x", "qubits": [3]},
      {"name": "h", "qubits": [3]},
      {"name": "cx", "qubits": [0, 3]},
      {"name": "cx", "qubits": [2, 3]},
      {"name": "h", "qubits": [0]},
      {"name": "h", "qubits": [1]},
      {"name": "h", "qubits": [2]}
    ],
    "nqubits": 4,
    "shots": 1000,
    "transpile": true,
    "routing": "sabre"
  }'
```

### Example 3: QASM Input via API

```bash
curl -X POST http://127.0.0.1:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "qasm",
    "qasm": "OPENQASM 2.0;\ninclude \"qelib1.inc\";\nqreg q[2];\nh q[0];\ncx q[0],q[1];",
    "shots": 1000,
    "noise_depol": 0.01,
    "noise_readout": 0.01
  }'
```

### Example 4: With Noise Simulation

```bash
curl -X POST http://127.0.0.1:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "json",
    "circuit": [
      {"name": "h", "qubits": [0]},
      {"name": "cx", "qubits": [0, 1]}
    ],
    "nqubits": 2,
    "shots": 1000,
    "noise_depol": 0.05,
    "noise_readout": 0.02,
    "seed": 42
  }'
```

**Response with noise:**
```json
{
  "probabilities": [0.48, 0.02, 0.02, 0.48],
  "counts": {
    "00": 480,
    "01": 20,
    "10": 25,
    "11": 475
  },
  "nqubits": 2
}
```

### Example 5: Full Options

```bash
curl -X POST http://127.0.0.1:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "json",
    "circuit": [
      {"name": "h", "qubits": [0]},
      {"name": "cx", "qubits": [0, 1]}
    ],
    "nqubits": 2,
    "transpile": true,
    "routing": "sabre",
    "restore_mapping": true,
    "shots": 2000,
    "seed": 123,
    "noise_depol": 0.01,
    "noise_readout": 0.01,
    "collapse": false
  }'
```

---

## 🎯 Summary Table

| Algorithm | Qubits | Gates | Speedup | Use Case |
|-----------|--------|-------|---------|----------|
| Bell State | 2 | 2 | N/A | Entanglement demo |
| Bernstein-Vazirani | 4 | 10 | Exponential | Hidden string finding |
| Grover's Search | 3 | 23 | Quadratic | Database search |
| QFT | 3+ | O(n²) | Exponential | Phase estimation |
| Phase Estimation | 3+ | Variable | Exponential | Eigenvalue finding |

---

**Happy quantum computing! 🎉**

