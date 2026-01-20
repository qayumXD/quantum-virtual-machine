# Quantum Virtual Machine (QVM)

This project is a lightweight, educational Quantum Virtual Machine (QVM) implemented in Python. The QVM is designed to simulate quantum circuits and demonstrate the process of transpilation, where a logical quantum circuit is adapted to run on a specific hardware architecture with limited connectivity.

For detailed information on the QVM's architecture, components, and how to use it, please see the **[QVM Documentation](./src/README.md)**.

---

## Basic Qiskit Examples

This repository also contains small, self-contained examples using Qiskit and the Statevector simulator.

**Files:**
- `superposition.py` — single-qubit Hadamard (H) to create a superposition.
- `bell_state.py` — 2-qubit Bell pair using H + CNOT.
- `ghz_state.py` — 3-qubit GHZ state using H + two CNOTs.

Each script prints the circuit and the probability distribution, and will attempt to save a histogram PNG if `matplotlib` is installed.

**Run an example:**
```bash
python3 superposition.py
```

**To get plotting:**
```bash
pip install matplotlib
```
