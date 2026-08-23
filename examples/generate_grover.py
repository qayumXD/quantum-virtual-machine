import json
import argparse

def generate_grover_circuit(target_state: str) -> list:
    """
    Generates a Grover's Search circuit for a specific target state.
    Currently supports 2 and 3 qubit search spaces.
    
    Args:
        target_state (str): The binary string to find (e.g., "11" or "101").
    
    Returns:
        list: Circuit operations.
    """
    n = len(target_state)
    if n not in [2, 3]:
        raise ValueError("This generator currently supports only 2 or 3 qubits.")
        
    circuit = []
    qubits = list(range(n))
    
    # 1. Initialization: |s> = H^n |0>
    for q in qubits:
        circuit.append({"name": "h", "qubits": [q]})
        
    # Grover Iterations
    # optimal iterations ~ (pi/4) * sqrt(2^n)
    # For n=2, sqrt(4)=2, iter ~ 1
    # For n=3, sqrt(8)=2.8, iter ~ 2 (usually 2 is optimal for 3 qubits)
    num_iterations = 1 if n == 2 else 2
    
    for _ in range(num_iterations):
        # --- ORACLE ---
        # Marks the target state with a negative phase.
        # Logic: Flip qubits that are '0' in target_state to '1', apply multi-controlled Z, flip back.
        
        # Pre-flipping X gates
        for i, bit in enumerate(target_state):
            if bit == '0':
                circuit.append({"name": "x", "qubits": [i]})
                
        # Multi-controlled Z (CCZ or CZ)
        # H -> MCX -> H on the last qubit is equivalent to MCZ
        target_qubit = qubits[-1]
        control_qubits = qubits[:-1]
        
        circuit.append({"name": "h", "qubits": [target_qubit]})
        
        if n == 2:
            circuit.append({"name": "cx", "qubits": [control_qubits[0], target_qubit]})
        else: # n == 3
            circuit.append({"name": "toffoli", "qubits": control_qubits + [target_qubit]})
            
        circuit.append({"name": "h", "qubits": [target_qubit]})
        
        # Post-flipping X gates (Uncompute)
        for i, bit in enumerate(target_state):
            if bit == '0':
                circuit.append({"name": "x", "qubits": [i]})
                
        # --- DIFFUSER (Amplification) ---
        # Operations: H^n -> X^n -> MCZ -> X^n -> H^n
        
        # H on all
        for q in qubits:
            circuit.append({"name": "h", "qubits": [q]})
            
        # X on all
        for q in qubits:
            circuit.append({"name": "x", "qubits": [q]})
            
        # MCZ
        circuit.append({"name": "h", "qubits": [target_qubit]})
        if n == 2:
            circuit.append({"name": "cx", "qubits": [control_qubits[0], target_qubit]})
        else:
            circuit.append({"name": "toffoli", "qubits": control_qubits + [target_qubit]})
        circuit.append({"name": "h", "qubits": [target_qubit]})
        
        # X on all
        for q in qubits:
            circuit.append({"name": "x", "qubits": [q]})
            
        # H on all
        for q in qubits:
            circuit.append({"name": "h", "qubits": [q]})

    return circuit

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Grover's Search Circuit")
    parser.add_argument("--target", type=str, required=True, help="Target state to search for (e.g. '11', '101')")
    parser.add_argument("--output", type=str, default="examples/grover_circuit.json", help="Output file path")
    
    args = parser.parse_args()
    
    try:
        circuit = generate_grover_circuit(args.target)
        with open(args.output, 'w') as f:
            json.dump(circuit, f, indent=4)
        
        print(f"Generated Grover circuit for target '{args.target}'.")
        print(f"Saved to {args.output}")
        print(f"\nTo run:")
        print(f"python -m qvm.cli {args.output} --nqubits {len(args.target)}")
        
    except ValueError as e:
        print(f"Error: {e}")
