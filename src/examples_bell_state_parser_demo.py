"""
Bell State Parser Demo

This script demonstrates how to:
1. Create a Bell state circuit using Qiskit
2. Parse it with QiskitParser into IR format
3. Display the IR structure
4. Simulate the circuit and show results

What is a Bell State?
- A maximally entangled quantum state of two qubits
- After measurement, both qubits will always have the same value
- The result is random: 50% |00⟩, 50% |11⟩
- This demonstrates quantum entanglement!
"""

try:
    from qiskit import QuantumCircuit, execute, Aer
    from qiskit.visualization import plot_histogram
    import matplotlib.pyplot as plt
    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False
    print("Error: Qiskit not installed. Install with: pip install qiskit qiskit-aer")
    exit(1)

import sys
sys.path.append('..')
from src.parser import QiskitParser
from src.ir import QuantumCircuitIR
import json


def create_bell_state():
    """
    Create a Bell state quantum circuit.
    
    Circuit: |00⟩ -> H(0) -> CNOT(0,1) -> (|00⟩ + |11⟩)/√2
    """
    print("Creating Bell State Circuit...")
    print("=" * 50)
    
    # Create circuit with 2 qubits and 2 classical bits
    qc = QuantumCircuit(2, 2)
    
    # Step 1: Apply Hadamard gate to qubit 0
    # This creates superposition: |0⟩ -> (|0⟩ + |1⟩)/√2
    qc.h(0)
    print("✓ Applied Hadamard (H) gate to qubit 0")
    print("  Effect: Creates superposition |0⟩ -> (|0⟩ + |1⟩)/√2")
    
    # Step 2: Apply CNOT gate with control=0, target=1
    # This creates entanglement: (|00⟩ + |10⟩)/√2 -> (|00⟩ + |11⟩)/√2
    qc.cx(0, 1)
    print("✓ Applied CNOT (CX) gate: control=0, target=1")
    print("  Effect: Creates entanglement (|00⟩ + |11⟩)/√2")
    
    # Step 3: Measure both qubits
    qc.measure([0, 1], [0, 1])
    print("✓ Added measurements on both qubits")
    print("\n")
    
    return qc


def parse_circuit(qc):
    """Parse Qiskit circuit into IR format."""
    print("Parsing Circuit with QiskitParser...")
    print("=" * 50)
    
    parser = QiskitParser()
    ir = parser.parse(qc)
    
    print(f"✓ Parsed successfully!")
    print(f"  Number of qubits: {ir.num_qubits}")
    print(f"  Number of gates: {len(ir.gates)}")
    print(f"  Number of measurements: {len(ir.measurements)}")
    print("\n")
    
    return ir


def display_ir(ir):
    """Display the IR structure in detail."""
    print("IR Structure (Intermediate Representation)...")
    print("=" * 50)
    
    # Convert to dictionary for pretty printing
    ir_dict = ir.to_dict()
    print(json.dumps(ir_dict, indent=2))
    print("\n")


def simulate_circuit(qc):
    """Simulate the circuit and show measurement results."""
    print("Simulating Circuit...")
    print("=" * 50)
    
    # Use Aer's qasm_simulator
    simulator = Aer.get_backend('qasm_simulator')
    
    # Execute the circuit 1000 times
    job = execute(qc, simulator, shots=1000)
    result = job.result()
    
    # Get measurement counts
    counts = result.get_counts(qc)
    
    print("Measurement Results (1000 shots):")
    for state, count in sorted(counts.items()):
        percentage = (count / 1000) * 100
        print(f"  |{state}⟩: {count} times ({percentage:.1f}%)")
    
    print("\nExpected: ~50% |00⟩ and ~50% |11⟩")
    print("Note: Never |01⟩ or |10⟩ due to entanglement!")
    print("\n")
    
    return counts


def main():
    """Main demo function."""
    print("\n" + "*" * 50)
    print("  BELL STATE PARSER DEMO")
    print("*" * 50 + "\n")
    
    # Step 1: Create Bell state circuit
    qc = create_bell_state()
    
    # Step 2: Parse to IR
    ir = parse_circuit(qc)
    
    # Step 3: Display IR
    display_ir(ir)
    
    # Step 4: Simulate
    counts = simulate_circuit(qc)
    
    print("Demo complete! 🎉")
    print("\nWhat you learned:")
    print("  1. How to create a Bell state (quantum entanglement)")
    print("  2. How the parser extracts gates from Qiskit circuits")
    print("  3. What the IR data structure looks like")
    print("  4. How to verify the circuit with simulation")


if __name__ == '__main__':
    if QISKIT_AVAILABLE:
        main()