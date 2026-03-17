# Quantum Virtual Machine (QVM)

A lightweight, educational Quantum Virtual Machine (QVM) implemented in Python. This project demonstrates the full lifecycle of a quantum program: from high-level circuit definition and hardware-agnostic intermediate representation (IR) to hardware-specific transpilation and hybrid simulation (Statevector/MPS).

## 🚀 Overview (v0.2)

The QVM follows a **write once, run anywhere (WORA)** philosophy, providing an abstraction layer that allows quantum algorithms to be defined once and then adapted for different hardware architectures.

### Key Features:
- **OpenQASM 3.0 Support:** Full AST-based parsing for modern quantum assembly, including control flow (`if`, `for`, `while`) and timing.
- **Hybrid Simulation Engine:**
    - **Statevector:** Exact simulation for small-scale circuits ($N \le 12$).
    - **MPS (Matrix Product States):** Efficient, compressible simulation for low-entanglement circuits, scaling to 20+ qubits.
- **Active Feedback Loop:** Real-time synchronization between classical registers and quantum state (Classical Shadowing).
- **Advanced Transpiler:** Automatically maps logical circuits to physical hardware, supporting Greedy and SABRE routing.
- **Interactive Web UI:** Modern FastAPI-powered dashboard for composing and executing quantum programs.

---

## 🏗️ Project Architecture

The system follows a strict **Pipeline Architecture**:

1.  **Input:** OpenQASM 3.0, 2.0, or JSON gate lists.
2.  **Parser (Lark):** Generates an AST and maps it to the internal `QuantumCircuit` IR.
3.  **Decomposer:** Normalizes high-level gates into a target-compatible native set.
4.  **Transpiler:** Routes qubits according to the target hardware topology.
5.  **Simulators:** 
    - `Simulator`: Exact statevector evolution.
    - `MPSSimulator`: Tensor network contraction with SVD-based truncation.
6.  **Output:** Probabilities, classical memory states, and visual plots.

---

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.10+
- `pip` (Python package manager)

### Installation
1.  **Clone the repository:**
    ```bash
    git clone https://github.com/qayum/quantum-virtual-machine.git
    cd quantum-virtual-machine
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

---

## 💻 Usage

### 1. Web Interface (GUI) - Recommended
The easiest way to explore the QVM features is through the web dashboard.

**Start the server:**
```bash
python -m src.qvm.server --host 127.0.0.1 --port 8000
```
Access the GUI at: `http://127.0.0.1:8000`

### 2. Command Line Interface (CLI)
**Run an OpenQASM 3.0 file:**
```bash
python -m src.qvm.cli test_shadow.qasm
```

**Run with Transpilation & Sabre Routing:**
```bash
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --transpile --routing sabre
```

---

## 📂 Directory Structure

- `src/qvm/`: Core logic (IR, Parsers, Simulators, Transpiler).
- `api/`: FastAPI backend implementation.
- `web/`: Frontend static dashboard.
- `docs/`: Technical design docs, implementation logs, and research.
- `tests/`: Automated test suite (Pytest).

---

## 📄 License
[Insert License Information Here]
