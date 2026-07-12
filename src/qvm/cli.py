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
from src.qvm.noise import NoiseChannel, NoiseModel, DeviceBackend
from src.qvm.observable import Hamiltonian

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
    parser.add_argument("--shots", type=int, default=0, help="If >0, draw this many measurement samples")
    parser.add_argument("--seed", type=int, default=None, help="Optional RNG seed for simulation")
    # Noise model options
    parser.add_argument("--noise-depol", type=float, default=0.0, help="Depolarizing noise probability [0,1]")
    parser.add_argument("--noise-amp-damp", type=float, default=0.0, help="Amplitude damping (T1) gamma [0,1]")
    parser.add_argument("--noise-phase-damp", type=float, default=0.0, help="Phase damping (T2) gamma [0,1]")
    parser.add_argument("--device", choices=["fake_5q", "fake_7q", "ideal"], default=None,
                        help="Use a predefined device noise profile")
    # Observable / expectation value
    parser.add_argument("--expectation", type=str, default=None,
                        help="Compute expectation value of a Pauli string (e.g. 'ZZ' or 'ZZ:-1.0,XI:0.5')")
    
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
    native_gates = {'h', 'x', 'y', 'z', 'rx', 'ry', 'rz', 'cx', 'cz', 'swap', 'id', 'measure', 'ccx', 'toffoli', 'sx', 'sxdg', 's', 'sdg', 't', 'tdg', 'p', 'delay', 'label', 'jump', 'classical_op'}
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

    # 5. Build noise model (if requested)
    noise_model = None
    if args.device:
        device_map = {
            "fake_5q": DeviceBackend.fake_5q_device,
            "fake_7q": DeviceBackend.fake_7q_device,
            "ideal": lambda: DeviceBackend.ideal(args.nqubits),
        }
        device = device_map[args.device]()
        noise_model = device.to_noise_model()
        print(f"\nUsing device backend: {device}")
        print(noise_model.summary())
    elif args.noise_amp_damp > 0 or args.noise_phase_damp > 0 or args.noise_depol > 0:
        noise_model = NoiseModel()
        all_1q_gates = ["h", "x", "y", "z", "rx", "ry", "rz", "p", "sx", "s", "t", "id"]
        if args.noise_depol > 0:
            noise_model.add_all_qubit_quantum_error(
                NoiseChannel.depolarizing(args.noise_depol), all_1q_gates)
        if args.noise_amp_damp > 0:
            noise_model.add_all_qubit_quantum_error(
                NoiseChannel.amplitude_damping(args.noise_amp_damp), all_1q_gates)
        if args.noise_phase_damp > 0:
            noise_model.add_all_qubit_quantum_error(
                NoiseChannel.phase_damping(args.noise_phase_damp), all_1q_gates)
        print(f"\nNoise model active:")
        print(noise_model.summary())

    # 6. Shot-based sampling (with noise if configured)
    if args.shots > 0:
        print(f"\nSampling {args.shots} shots...")
        if noise_model is not None:
            counts = sim.sample(qc, shots=args.shots, seed=args.seed, noise_model=noise_model)
        else:
            counts = sim.sample(qc, shots=args.shots, seed=args.seed, depol_prob=args.noise_depol)
        print("Measurement counts:")
        for bitstring, count in sorted(counts.items()):
            print(f"  |{bitstring}>: {count}")

    # 7. Expectation value (if requested)
    if args.expectation:
        try:
            # Parse expectation string: 'ZZ' or 'ZZ:-1.0,XI:0.5'
            if ':' in args.expectation:
                pauli_dict = {}
                for term in args.expectation.split(','):
                    ps, coeff = term.split(':')
                    pauli_dict[ps.strip()] = float(coeff.strip())
                obs = Hamiltonian.from_dict(pauli_dict)
            else:
                obs = Hamiltonian.from_dict({args.expectation: 1.0})
            ev = sim.expectation_value(qc, obs, seed=args.seed)
            print(f"\nExpectation value <{args.expectation}>: {ev:.6f}")
        except Exception as e:
            print(f"Error computing expectation value: {e}")

    # 8. Visualize (Optional)
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
