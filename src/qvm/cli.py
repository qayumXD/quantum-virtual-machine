import argparse
import json
import sys
import matplotlib.pyplot as plt
import numpy as np
from src.qvm.parser import QASMParser, OpenQASM2Parser
from src.qvm.qasm3_parser import OpenQASM3Parser
from src.qvm.simulator import Simulator
from src.qvm.transpiler import Transpiler
from src.qvm.decomposer import Decomposer
from src.qvm.architecture import get_linear_architecture
from src.qvm.visual import plot_histogram, plot_circuit

def main():
    parser = argparse.ArgumentParser(description="Quantum Virtual Machine (QVM) CLI")
    parser.add_argument("input_file", help="Path to the input JSON or QASM circuit file")
    parser.add_argument("--nqubits", type=int, help="Number of qubits (optional if QASM file)")
    parser.add_argument("--transpile", action="store_true", help="Enable transpilation for linear topology")
    parser.add_argument("--routing", choices=["greedy", "sabre"], default="greedy", help="Routing strategy when --transpile is set")
    parser.add_argument("--no-restore-mapping", dest="restore_mapping", action="store_false",
                        help="Do not swap back to restore logical->physical identity after routing (saves swaps).")
    parser.set_defaults(restore_mapping=True)
    parser.add_argument("--visualize", action="store_true", help="Show circuit and probability plots")
    parser.add_argument("--shots", type=int, default=0, help="If >0, draw this many measurement samples (legacy)")
    parser.add_argument("--seed", type=int, default=None, help="Optional RNG seed for simulation")
    
    args = parser.parse_args()
    
    # 1. Load Circuit
    try:
        if args.input_file.lower().endswith(".qasm"):
            with open(args.input_file, 'r') as f:
                content = f.read()
            
            if "OPENQASM 3.0" in content:
                print(f"Detected OpenQASM 3.0 in {args.input_file}...")
                parser3 = OpenQASM3Parser()
                qc = parser3.parse(content)
                args.nqubits = qc.num_qubits
            else:
                print(f"Loading OpenQASM 2.0 from {args.input_file}...")
                qc = OpenQASM2Parser.parse(content)
                args.nqubits = qc.num_qubits
        else:
            with open(args.input_file, 'r') as f:
                circuit_data = json.load(f)
            if not args.nqubits:
                print("Error: --nqubits is required for JSON input files.")
                sys.exit(1)
            print(f"Loading circuit from {args.input_file}...")
            qc = QASMParser.parse(circuit_data, args.nqubits)
    except Exception as e:
        print(f"Error reading/parsing input file: {e}")
        sys.exit(1)
    
    # 2. Decompose (for legacy gates, etc.)
    # Note: Our new simulator natively handles many gates, but we still decompose 
    # if anything non-supported is left.
    native_gates = {'h', 'x', 'y', 'z', 'rx', 'ry', 'rz', 'cx', 'swap', 'id', 'measure', 'ccx', 'toffoli', 'sx', 'sxdg', 's', 'sdg', 't', 'tdg', 'p', 'delay', 'label', 'jump', 'classical_op'}
    decomposer = Decomposer(native_gates)
    try:
        qc = decomposer.decompose_circuit(qc)
    except Exception as e:
        print(f"Error during decomposition: {e}")
        sys.exit(1)

    # 3. Transpile (Optional)
    if args.transpile:
        print("Transpiling for Linear Architecture...")
        try:
            arch = get_linear_architecture(args.nqubits)
            transpiler = Transpiler(arch, strategy=args.routing, restore_mapping=args.restore_mapping)
            qc = transpiler.transpile(qc)
            print("Transpilation complete.")
        except Exception as e:
            print(f"Error during transpilation: {e}")
            sys.exit(1)

    # 4. Simulate
    print("Simulating...")
    try:
        sim = Simulator()
        state, mem = sim.simulate(qc, seed=args.seed)
        probs = np.abs(state)**2
        print("Simulation complete.")
    except Exception as e:
        print(f"Error during simulation: {e}")
        sys.exit(1)
    
    # Output Results
    print("\nResults (Statevector Probabilities):")
    for i, prob in enumerate(probs):
        if prob > 1e-6:
            bin_str = format(i, f'0{args.nqubits}b')
            print(f"|{bin_str}>: {prob:.4f}")

    if mem:
        print("\nClassical Memory:")
        for name, values in mem.items():
            print(f"{name}: {values}")

    # 5. Visualize (Optional)
    if args.visualize:
        print("\nDisplaying visualizations...")
        try:
            plot_circuit(qc, title="Quantum Circuit")
            plot_histogram(probs, title="Statevector Probabilities")
            plt.show()
        except Exception as e:
            print(f"Error visualizing: {e}")

if __name__ == "__main__":
    main()
