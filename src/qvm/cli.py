import argparse
import json
import sys
import matplotlib.pyplot as plt
from src.qvm.parser import QASMParser
from src.qvm.simulator import Simulator
from src.qvm.transpiler import Transpiler
from src.qvm.decomposer import Decomposer
from src.qvm.architecture import get_linear_architecture
from src.qvm.visual import plot_histogram, plot_circuit
from src.qvm.util.export import to_openqasm2

def main():
    parser = argparse.ArgumentParser(description="Quantum Virtual Machine (QVM) CLI")
    parser.add_argument("input_file", help="Path to the input JSON circuit file")
    parser.add_argument("--nqubits", type=int, required=True, help="Number of qubits in the circuit")
    parser.add_argument("--transpile", action="store_true", help="Enable transpilation for linear topology")
    parser.add_argument("--routing", choices=["greedy", "sabre"], default="greedy", help="Routing strategy when --transpile is set")
    parser.add_argument("--no-restore-mapping", dest="restore_mapping", action="store_false",
                        help="Do not swap back to restore logical->physical identity after routing (saves swaps).")
    parser.set_defaults(restore_mapping=True)
    parser.add_argument("--visualize", action="store_true", help="Show circuit and probability plots")
    parser.add_argument("--export", help="Path to export OpenQASM code")
    parser.add_argument("--shots", type=int, default=0, help="If >0, draw this many measurement samples")
    parser.add_argument("--seed", type=int, default=None, help="Optional RNG seed for sampling")
    parser.add_argument("--noise-depol", type=float, default=0.0, help="Depolarizing probability to mix with uniform (0-1)")
    parser.add_argument("--noise-readout", type=float, default=0.0, help="Per-bit readout flip probability (0-1)")
    
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
    
    # 2. Decompose (Always run to ensure simulator compatibility for high-level gates)
    # The simulator natively supports: H, X, Y, Z, Rx, Ry, Rz, CX, SWAP, ID
    print("Decomposing complex gates...")
    native_gates = {'h', 'x', 'y', 'z', 'rx', 'ry', 'rz', 'cx', 'swap', 'id', 'measure'}
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

    # Optional sampling
    counts = None
    if args.shots and args.shots > 0:
        try:
            counts = sim.sample(
                qc,
                shots=args.shots,
                seed=args.seed,
                depol_prob=args.noise_depol,
                readout_error=args.noise_readout,
            )
            print(f"\nSampled counts (shots={args.shots}):")
            for state, ct in sorted(counts.items()):
                print(f"|{state}>: {ct}")
        except Exception as e:
            print(f"Error during sampling: {e}")
    
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
            plot_data = counts if counts is not None else probs
            plot_title = "Sampled Counts" if counts is not None else "Simulation Results"
            plot_histogram(plot_data, title=plot_title)
            plt.show()
        except Exception as e:
            print(f"Error visualizing: {e}")

if __name__ == "__main__":
    main()
