# Quantum Virtual Machine (QVM)

This directory contains a lightweight, educational Quantum Virtual Machine (QVM)
implemented in Python. The QVM is designed to simulate quantum circuits and
demonstrate the process of transpilation, where a logical quantum circuit is
adapted to run on a specific hardware architecture with limited connectivity.

## Core Components

The QVM is composed of several key modules:

- `qvm/ir.py`: Defines the **Intermediate Representation (IR)** for quantum circuits using a `QuantumCircuit` class.
- `qvm/parser.py`: A simple parser to convert a dictionary-based description of a circuit into the IR.
- `qvm/simulator.py`: A statevector simulator that executes quantum circuits and calculates the final statevector and measurement probabilities.
- `qvm/architecture.py`: Defines target hardware architectures with specific qubit connectivity.
- `qvm/transpiler.py`: A basic transpiler that maps a logical circuit to a physical one, inserting SWAP gates to handle connectivity constraints.
- `qvm/decomposer.py`: A tool to decompose complex gates (like Toffoli) into a sequence of simpler, native gates.
- `qvm/util/export.py`: Provides functionality to export circuits to standard formats like OpenQASM 2.0.

## How to Use

An example of how to define, transpile, and simulate a quantum circuit is provided in the `examples/` directory.

### Running an Example

To run the main example, which demonstrates the full pipeline from parsing to simulation:

```bash
python3 -m src.examples.full_pipeline
```

This example will:
1. Define a logical quantum circuit.
2. Define a target hardware architecture (e.g., a linear chain).
3. Transpile the circuit to respect the architecture's constraints.
4. Simulate the final physical circuit.
5. Print the results.
