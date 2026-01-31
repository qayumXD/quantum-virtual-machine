# Project Structure & Architecture

This document provides a high-level overview of the Quantum Virtual Machine (QVM) file structure and the architectural decisions behind it.

## 1. Directory Tree

```
C:\Users\qayum\Desktop\UniDocs\fyp\
├── .gitignore               # Git configuration
├── requirements.txt         # Python dependencies
├── src/                     # Source Code Root
│   ├── examples/            # Example Scripts & Generators
│   │   ├── generate_bv.py   # Bernstein-Vazirani Generator
│   │   ├── generate_grover.py # Grover's Search Generator
│   │   └── *.json           # Generated Circuit Files
│   └── qvm/                 # Core QVM Package
│       ├── __init__.py
│       ├── cli.py           # Command Line Interface (Entry Point)
│       ├── ir.py            # Intermediate Representation (QuantumCircuit)
│       ├── parser.py        # JSON -> IR Parser
│       ├── simulator.py     # Vectorized Statevector Engine
│       ├── architecture.py  # Hardware Topology Definitions
│       ├── transpiler.py    # Routing & SWAP Insertion Logic
│       ├── decomposer.py    # Gate Decomposition (Toffoli -> Native)
│       ├── visual.py        # Visualization (Matplotlib)
│       └── util/
│           └── export.py    # OpenQASM Export Utility
├── tests/                   # Automated Tests
│   ├── test_ir.py
│   ├── test_parser.py
│   ├── test_simulator.py
│   ├── test_transpiler.py
│   └── test_visual.py
└── docs/                    # Documentation
    ├── algorithms/          # Math & Theory of implemented algos
    ├── guides/              # User Guides
    ├── reports/             # Status & Performance Reports
    ├── steps/               # Planning & Progress Logs
    └── technical_reference/ # (This directory) Deep technical docs
```

## 2. Architectural Layers

The system follows a strict **Pipeline Architecture**, where data flows linearly through distinct stages. Each stage transforms the data format.

```mermaid
graph LR
    User[User Input (JSON)] --> Parser
    Parser --> IR[Intermediate Representation]
    IR --> Decomposer
    Decomposer --> Transpiler
    Transpiler --> Simulator
    Simulator --> Results[Probabilities]
    Results --> Visualizer
```

### Layer 1: Input & Parsing
*   **Goal:** abstract the input format from the internal logic.
*   **File:** `src/qvm/parser.py`
*   **Logic:** Converts a Python dictionary (loaded from JSON) into the strict `QuantumCircuit` object. Validation happens here.

### Layer 2: Intermediate Representation (IR)
*   **Goal:** A hardware-agnostic container for the circuit.
*   **File:** `src/qvm/ir.py`
*   **Logic:** The `QuantumCircuit` class acts as the "Source of Truth". It holds the list of operations, qubit count, and parameters. It is mutable (Transpilers modify it).

### Layer 3: Transformation (Decomposer & Transpiler)
*   **Goal:** Adapt the ideal circuit to physical constraints.
*   **Files:** `src/qvm/decomposer.py`, `src/qvm/transpiler.py`
*   **Logic:**
    *   **Decomposer:** `Toffoli` -> `H, CNOT, T` (Native Gates).
    *   **Transpiler:** Checks if connected qubits are adjacent. If not, finds a path and inserts `SWAP` gates to move logical qubits to physical adjacency.

### Layer 4: Execution (Simulator)
*   **Goal:** Calculate the mathematical result.
*   **File:** `src/qvm/simulator.py`
*   **Logic:**
    *   Initialize Statevector $\psi = [1, 0, ... 0]$.
    *   Apply Gate Matrices $U$ via Linear Algebra: $\psi_{new} = U \cdot \psi$.
    *   Uses **NumPy Vectorization** for speed.

### Layer 5: Output & Visualization
*   **Goal:** Present results to the human.
*   **File:** `src/qvm/visual.py`
*   **Logic:** Uses `matplotlib` to render the probability distribution and the circuit diagram.

## 3. Library Choices

| Library | Usage | Justification |
| :--- | :--- | :--- |
| **Python 3.10+** | Core Language | Readable, huge scientific ecosystem. |
| **NumPy** | Math Engine | Essential for efficient Linear Algebra (Matrix Multiplication, Tensor Products). Python loops are too slow for Quantum Simulators. |
| **Matplotlib** | Visualization | Industry standard for plotting in Python. Flexible enough for custom circuit drawings. |
| **Pytest** | Testing | Simple, powerful testing framework with excellent fixture support. |
| **Argparse** | CLI | Built-in standard library for robust command-line parsing. |

```