import json
import argparse
import random

def generate_bv_circuit(num_qubits: int, secret_string: str) -> list:
    """
    Generates a Bernstein-Vazirani circuit for a given secret bitstring.
    
    Args:
        num_qubits (int): Total number of qubits available (must be at least len(secret_string) + 1).
        secret_string (str): The hidden bitstring to find (e.g., "101").
        
    Returns:
        list: A JSON-serializable list of gate dictionaries.
    """
    n = len(secret_string)
    if num_qubits < n + 1:
        raise ValueError(f"Not enough qubits. Need at least {n+1} for string of length {n}.")
    
    circuit = []
    
    # Indices
    input_qubits = list(range(n))
    ancilla_qubit = n
    
    # 1. Initialization
    # Put input qubits into |+> state
    for q in input_qubits:
        circuit.append({"name": "h", "qubits": [q]})
        
    # Put ancilla qubit into |-> state (X then H)
    circuit.append({"name": "x", "qubits": [ancilla_qubit]})
    circuit.append({"name": "h", "qubits": [ancilla_qubit]})
    
    # 2. Oracle
    # For every '1' in the secret string, apply CNOT(input_i, ancilla)
    # The string is usually read from left to right corresponding to q0, q1... or vice-versa.
    # We'll map s[0] -> q[0], s[1] -> q[1], etc.
    for i, char in enumerate(secret_string):
        if char == '1':
            circuit.append({"name": "cx", "qubits": [input_qubits[i], ancilla_qubit]})
            
    # 3. Interference (Hadamard on inputs)
    for q in input_qubits:
        circuit.append({"name": "h", "qubits": [q]})
        
    return circuit

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Bernstein-Vazirani Circuit")
    parser.add_argument("--secret", type=str, default="101", help="The secret bitstring to encode (e.g., 101)")
    parser.add_argument("--output", type=str, default="examples/bv_circuit.json", help="Output JSON file path")
    
    args = parser.parse_args()
    
    # We need len(secret) input qubits + 1 ancilla
    n_qubits = len(args.secret) + 1
    
    try:
        circuit = generate_bv_circuit(n_qubits, args.secret)
        with open(args.output, 'w') as f:
            json.dump(circuit, f, indent=4)
        print(f"Generated Bernstein-Vazirani circuit for secret '{args.secret}' with {n_qubits} qubits.")
        print(f"Saved to {args.output}")
        print(f"\nTo run this circuit:")
        print(f"python -m src.qvm.cli {args.output} --nqubits {n_qubits}")
        
    except ValueError as e:
        print(f"Error: {e}")
