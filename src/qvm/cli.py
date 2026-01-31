import argparse
import json
import sys
import matplotlib.pyplot as plt
from src.qvm.parser import QASMParser
from src.qvm.simulator import Simulator
from src.qvm.transpiler import Transpiler
from src.qvm.architecture import get_linear_architecture
from src.qvm.visual import plot_histogram, plot_circuit
from src.qvm.util.export import to_openqasm2

def main():
    parser = argparse.ArgumentParser(description="Quantum Virtual Machine (QVM) CLI")
    parser.add_argument("input_file", help="Path to the input JSON circuit file")
    parser.add_argument("--nqubits", type=int, required=True, help="Number of qubits in the circuit")
    parser.add_argument("--transpile", action="store_true", help="Enable transpilation for linear topology")
    parser.add_argument("--visualize", action="store_true", help="Show circuit and probability plots")
    parser.add_argument("--export", help="Path to export OpenQASM code")
    
    args = parser.parse_args()
    
    # 1. Load Circuit
    try:
        with open(args.input_file, 'r') as f:
            circuit_data = json.load(f)
    except Exception as e:
        print(f"Error reading input file: {e}")
        sys.exit(1)
        
    print(f"Loading circuit from {args.input_file}...")
    try:
        qc = QASMParser.parse(circuit_data, args.nqubits)
    except Exception as e:
        print(f"Error parsing circuit: {e}")
        sys.exit(1)
    
    # 2. Transpile (Optional)
    if args.transpile:
        print("Transpiling for Linear Architecture...")
        try:
            arch = get_linear_architecture(args.nqubits)
            transpiler = Transpiler(arch)
            qc = transpiler.transpile(qc)
            print("Transpilation complete.")
        except Exception as e:
            print(f"Error during transpilation: {e}")
            sys.exit(1)

    # 3. Simulate
    print("Simulating...")
    try:
        sim = Simulator()
        state = sim.simulate(qc)
        probs = sim.get_probabilities(state)
        print("Simulation complete.")
    except Exception as e:
        print(f"Error during simulation: {e}")
        sys.exit(1)
    
    # Output Results
    # Identify non-zero states
    print("\nResults:")
    for i, prob in enumerate(probs):
        if prob > 1e-6:
            bin_str = format(i, f'0{args.nqubits}b')
            print(f"|{bin_str}|: {prob:.4f}")

    # 4. Export (Optional)
    if args.export:
        print(f"\nExporting OpenQASM to {args.export}...")
        try:
            qasm_str = to_openqasm2(qc)
            with open(args.export, 'w') as f:
                f.write(qasm_str)
            print("Export complete.")
        except Exception as e:
            print(f"Error exporting QASM: {e}")
            
    # 5. Visualize (Optional)
    if args.visualize:
        print("\nDisplaying visualizations...")
        try:
            plot_circuit(qc, title="Quantum Circuit")
            plot_histogram(probs, title="Simulation Results")
            plt.show()
        except Exception as e:
            print(f"Error visualizing: {e}")

if __name__ == "__main__":
    main()
