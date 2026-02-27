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
*   `--routing {greedy,sabre}`: Routing strategy when `--transpile` is used. `sabre` uses a lookahead heuristic to reduce swaps.
*   `--no-restore-mapping`: When set with `--transpile`, do not swap back to the original logical/physical mapping (fewer swaps, but final labeling follows physical qubits).
*   `--visualize`: (Optional) Display popup windows with the circuit diagram and probability histogram.
*   `--export <path>`: (Optional) Save the executed circuit as an OpenQASM 2.0 file.
*   `--shots <N>`: (Optional) Draw N samples (shot-based execution). If omitted, only probabilities are printed.
*   `--seed <int>`: RNG seed for reproducible sampling.
*   `--noise-depol <p>`: Depolarizing probability (mixes distribution with uniform).
*   `--noise-readout <p>`: Per-bit readout flip probability.

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

### 4. Shot-based sampling with noise
```bash
python -m src.qvm.cli examples/bell_state.json --nqubits 2 --shots 2000 --noise-depol 0.05 --noise-readout 0.01
```

## Algorithm Examples

The project includes helper scripts to generate circuits for standard quantum algorithms.

*   **Bernstein-Vazirani:** Finds a hidden bitstring in one shot.
    *   [Documentation](../algorithms/Bernstein_Vazirani.md)
    *   `python examples/generate_bv.py --secret 101`
*   **Grover's Search:** Finds a marked item in an unsorted list.
    *   [Documentation](../algorithms/Grover.md)
    *   `python examples/generate_grover.py --target 101`

## Cirq → QVM example

If you use Cirq, see `examples/cirq_to_ir_demo.py` for parsing a Cirq circuit into the lightweight IR and exporting a JSON gate list for the CLI.
