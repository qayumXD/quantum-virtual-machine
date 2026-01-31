# QVM CLI Usage Guide

The Quantum Virtual Machine (QVM) provides a Command Line Interface (CLI) to easily run quantum simulations from your terminal.

## Basic Usage

Run the CLI using Python:

```bash
python -m src.qvm.cli <input_file> --nqubits <N> [options]
```

### Arguments

*   `input_file`: Path to a JSON file containing the circuit description.
*   `--nqubits <N>`: (Required) Total number of qubits in the circuit.
*   `--transpile`: (Optional) Enable automatic transpilation for a linear qubit topology. Use this if your circuit uses gates on non-adjacent qubits.
*   `--visualize`: (Optional) Display popup windows with the circuit diagram and probability histogram.
*   `--export <path>`: (Optional) Save the executed circuit as an OpenQASM 2.0 file.

## Input File Format

The input file must be a JSON array of gate objects. Each object has:
*   `name`: Gate name (e.g., "h", "cx", "rz", "x", "y", "z").
*   `qubits`: List of qubit indices (e.g., `[0]` or `[0, 1]`).
*   `params`: (Optional) List of parameters for rotation gates (e.g., `[3.14]`).

**Example `circuit.json`:**
```json
[
    {"name": "h", "qubits": [0]},
    {"name": "cx", "qubits": [0, 1]}
]
```

## Examples

### 1. Run a Simple Simulation
Simulate a Bell State circuit (2 qubits) and print results to console.

```bash
python -m src.qvm.cli examples/bell_state.json --nqubits 2
```

### 2. Visualize Results
Simulate and show plots.

```bash
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --visualize
```

### 3. Transpile and Export
Simulate a circuit that needs transpilation (e.g., CNOT between 0 and 2 on a linear chain), and save the transpiled QASM.

```bash
python -m src.qvm.cli examples/my_circuit.json --nqubits 3 --transpile --export output.qasm
```
