# Basic Qiskit Examples

This folder contains small, self-contained examples using Qiskit and the
Statevector simulator so they run without qiskit-aer.

Files:
- `superposition.py` — single-qubit Hadamard (H) to create a superposition.
- `bell_state.py` — 2-qubit Bell pair using H + CNOT.
- `ghz_state.py` — 3-qubit GHZ state using H + two CNOTs.

Each script prints the circuit and the probability distribution, and will
attempt to save a histogram PNG if `matplotlib` is installed or display it
when an interactive backend is available.

Run an example:

```bash
python3 superposition.py
python3 bell_state.py
python3 ghz_state.py
```

To get plotting, install matplotlib:

```bash
pip install matplotlib
```
