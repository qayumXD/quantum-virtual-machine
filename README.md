# Quantum Virtual Machine (QVM)

A lightweight, educational Quantum Virtual Machine (QVM) implemented in Python. This project demonstrates the full lifecycle of a quantum program: from high-level circuit definition and hardware-agnostic intermediate representation (IR) to hardware-specific transpilation and hybrid simulation (Statevector/MPS).

## 🚀 Overview (v0.2)

The QVM follows a **write once, run anywhere (WORA)** philosophy, providing an abstraction layer that allows quantum algorithms to be defined once and then adapted for different hardware architectures.

### Key Features:
- **OpenQASM 3.0 Support:** Full AST-based parsing for modern quantum assembly, including control flow (`if`, `for`, `while`) and timing.
- **Framework Interoperability:** Bidirectional conversions and simulator execution support for **Qiskit**, **Cirq**, **JSON**, and **OpenQASM 3.0**.
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

---

## 🎨 Visual Overview

<div style="display:flex;gap:16px;flex-wrap:wrap;align-items:flex-start">
    <div style="flex:1;min-width:300px;max-width:520px;padding:12px;background:#0f172a;color:#e6f0ff;border-radius:8px"> 
        <h3 style="margin-top:0;color:#bfe3ff">Feature Maturity</h3>
        <svg viewBox="0 0 300 120" width="100%" height="120" role="img" aria-label="feature maturity bar chart">
            <rect x="10" y="20" width="80" height="20" fill="#60a5fa" />
            <text x="100" y="35" font-size="12" fill="#e6f0ff">OpenQASM 3.0 parsing (complete)</text>
            <rect x="10" y="50" width="60" height="20" fill="#34d399" />
            <text x="100" y="65" font-size="12" fill="#e6f0ff">Statevector simulator</text>
            <rect x="10" y="80" width="50" height="20" fill="#f59e0b" />
            <text x="100" y="95" font-size="12" fill="#e6f0ff">MPS simulator</text>
        </svg>
    </div>

    <div style="flex:1;min-width:300px;max-width:520px;padding:12px;background:#081029;color:#f0fff4;border-radius:8px">
        <h3 style="margin-top:0;color:#c7f9d4">Simulator Scaling (example)</h3>
        <svg viewBox="0 0 320 140" width="100%" height="140" role="img" aria-label="simulator scaling line chart">
            <polyline fill="none" stroke="#60a5fa" stroke-width="2" points="20,120 70,100 120,85 170,70 220,60 270,58" />
            <text x="22" y="128" font-size="10" fill="#c7f9d4">2</text>
            <text x="72" y="128" font-size="10" fill="#c7f9d4">4</text>
            <text x="122" y="128" font-size="10" fill="#c7f9d4">8</text>
            <text x="172" y="128" font-size="10" fill="#c7f9d4">12</text>
            <text x="222" y="128" font-size="10" fill="#c7f9d4">16</text>
            <text x="272" y="128" font-size="10" fill="#c7f9d4">20</text>
            <text x="10" y="12" font-size="11" fill="#c7f9d4">Memory / compute (rel.)</text>
        </svg>
    </div>
</div>

---

## 🧾 Example QASM Outputs (Qiskit & Cirq)

Below are short example logs to show how QASM from different frontends looks when fed to the QVM pipeline.

**Qiskit-style QASM (trimmed):**

```qasm
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0];
cx q[0],q[1];
measure q -> c;
```

**Cirq-style (pseudo-output / converted):**

```qasm
// Cirq circuit converted to OpenQASM (example)
OPENQASM 2.0;
qreg q[3];
h q[0];
cx q[0],q[1];
ry(1.5708) q[2];
```

---

## 🔎 Quick Visual Notes

<div style="background:#fff7ed;border-left:4px solid #f59e0b;padding:10px;border-radius:6px;margin:8px 0">
    <strong style="color:#92400e">Tip:</strong> These inline SVG charts are lightweight and render on GitHub. For interactive charts, we can add a small HTML/JS demo in `web/` and link to it.
</div>

<div style="background:#eef2ff;border-left:4px solid #6366f1;padding:10px;border-radius:6px;margin:8px 0">
    <strong style="color:#1e3a8a">Logs:</strong> If you want live execution logs (e.g., Qiskit/Cirq transpile output), we can add a `docs/logs/` directory with sample runs or auto-generate them during CI.
</div>
