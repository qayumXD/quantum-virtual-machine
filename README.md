# Quantum Virtual Machine (QVM)

A lightweight, educational Quantum Virtual Machine (QVM) implemented in Python. This project demonstrates the full lifecycle of a quantum program: from high-level circuit definition and hardware-agnostic intermediate representation (IR) to hardware-specific transpilation and statevector simulation.

## 🚀 Overview

The QVM follows a **write once, run anywhere (WORA)** philosophy, providing an abstraction layer that allows quantum algorithms to be defined once and then adapted for different hardware architectures (e.g., linear chains, fully connected topologies).

### Key Features:
- **Intermediate Representation (IR):** A hardware-agnostic container for quantum circuits.
- **Statevector Simulator:** A high-performance simulation engine using NumPy vectorization.
- **Transpiler:** Automatically maps logical circuits to physical hardware, inserting SWAP gates to satisfy connectivity constraints.
- **Decomposer:** Breaks down complex gates (like Toffoli/CCX) into a sequence of supported native gates.
- **Multi-Interface:** Support for Command Line (CLI) and a Web-based GUI (FastAPI).
- **OpenQASM 2.0 Support:** Parse and export standard quantum assembly language.
- **Noise Modeling:** Educational models for depolarizing noise and readout errors.

---

## 🏗️ Project Architecture

The system follows a strict **Pipeline Architecture**, where data flows through distinct transformation stages:

1.  **Input:** JSON gate lists or OpenQASM 2.0 files.
2.  **Parser:** Converts input into the internal `QuantumCircuit` IR.
3.  **Decomposer:** Normalizes high-level gates into a target-compatible native set.
4.  **Transpiler:** Routes qubits according to the target hardware topology (e.g., Linear, Grid).
5.  **Simulator:** Executes the circuit using linear algebra (Statevector evolution).
6.  **Output:** Probabilities, shot-based counts, and visual plots (Circuit Diagrams, Histograms).

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

### 1. Command Line Interface (CLI)
The CLI is the primary way to run simulations locally.

**Basic Run:**
```bash
python -m src.qvm.cli examples/bell_state.json --nqubits 2
```

**With Visualization:**
```bash
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --visualize
```

**Transpilation for Linear Architecture:**
```bash
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --transpile --routing sabre
```

**Shot-based Sampling with Noise:**
```bash
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --shots 1024 --noise-depol 0.01 --noise-readout 0.02
```

### 2. Web Interface (GUI)
The project includes a FastAPI-based web server and a static frontend.

**Start the server:**
```bash
python -m src.qvm.server --host 127.0.0.1 --port 8000
```
Access the GUI at: `http://127.0.0.1:8000`

---

## 📂 Directory Structure

- `src/qvm/`: Core logic (IR, Simulator, Transpiler, etc.)
- `api/`: FastAPI backend implementation.
- `web/`: Frontend static files (HTML/JS/CSS).
- `examples/`: Sample circuits and algorithm generators (Bernstein-Vazirani, Grover).
- `docs/`: Extensive documentation on theory, algorithms, and technical deep-dives.
- `tests/`: Automated test suite for all components.

---

## 🧪 Examples & Algorithms

The repository includes scripts to generate standard quantum algorithms:
- **Bernstein-Vazirani:** `python examples/generate_bv.py --secret 101`
- **Grover's Search:** `python examples/generate_grover.py --target 101`

You can then run the generated `.json` files using the CLI or upload them to the Web GUI.

---

## 📄 License
[Insert License Information Here]
