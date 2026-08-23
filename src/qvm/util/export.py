# src/qvm/util/export.py

"""
Export functions for converting QuantumCircuit objects to other formats.
"""

from qvm.ir import QuantumCircuit

def to_openqasm2(circuit: QuantumCircuit) -> str:
    """
    Converts a QuantumCircuit object to an OpenQASM 2.0 string.

    Args:
        circuit (QuantumCircuit): The circuit to convert.

    Returns:
        str: The OpenQASM 2.0 representation of the circuit.
    """
    qasm_str = "OPENQASM 2.0;\n"
    qasm_str += 'include "qelib1.inc";\n'
    
    num_qubits = circuit.num_qubits
    qasm_str += f"qreg q[{num_qubits}];\n"
    qasm_str += f"creg c[{num_qubits}];\n\n"

    for op in circuit.operations:
        gate_name = op["name"]
        qubits = op["qubits"]
        params = op["params"]

        if gate_name == "h":
            qasm_str += f"h q[{qubits[0]}];\n"
        elif gate_name == "x":
            qasm_str += f"x q[{qubits[0]}];\n"
        elif gate_name == "y":
            qasm_str += f"y q[{qubits[0]}];\n"
        elif gate_name == "z":
            qasm_str += f"z q[{qubits[0]}];\n"
        elif gate_name == "cx":
            qasm_str += f"cx q[{qubits[0]}],q[{qubits[1]}];\n"
        elif gate_name == "swap":
            # SWAP is not a primitive in qelib1.inc, but can be decomposed
            # into 3 CNOTs. For simplicity, we'll represent it directly if possible,
            # or decompose it. A common way is:
            qasm_str += f"cx q[{qubits[0]}],q[{qubits[1]}];\n"
            qasm_str += f"cx q[{qubits[1]}],q[{qubits[0]}];\n"
            qasm_str += f"cx q[{qubits[0]}],q[{qubits[1]}];\n"
        elif gate_name == "rz":
            qasm_str += f"rz({params[0]}) q[{qubits[0]}];\n"
        elif gate_name == "rx":
            qasm_str += f"rx({params[0]}) q[{qubits[0]}];\n"
        elif gate_name == "ry":
            qasm_str += f"ry({params[0]}) q[{qubits[0]}];\n"
        elif gate_name == "id":
            qasm_str += f"id q[{qubits[0]}];\n"
        elif gate_name == "toffoli" or gate_name == "ccx":
             qasm_str += f"ccx q[{qubits[0]}],q[{qubits[1]}],q[{qubits[2]}];\n"
        elif gate_name == "measure":
            # Assuming measurement of all qubits to corresponding classical bits
            for q_idx in qubits:
                 qasm_str += f"measure q[{q_idx}] -> c[{q_idx}];\n"
        else:
            print(f"Warning: Gate '{gate_name}' not supported for OpenQASM 2.0 export. Skipping.")

    return qasm_str

# Example Usage
if __name__ == "__main__":
    from qvm.ir import QuantumCircuit

    # Create a sample circuit
    qc = QuantumCircuit(3)
    qc.add_operation("h", [0])
    qc.add_operation("cx", [0, 1])
    qc.add_operation("toffoli", [0, 1, 2])
    qc.add_operation("rz", [2], [3.14])
    qc.add_operation("measure", [0, 1, 2])
    
    # Convert to OpenQASM 2.0
    qasm_code = to_openqasm2(qc)
    
    print("Generated OpenQASM 2.0 Code:")
    print(qasm_code)
