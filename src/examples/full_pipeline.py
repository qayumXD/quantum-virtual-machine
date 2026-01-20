# src/examples/full_pipeline.py

"""
An example demonstrating the full QVM pipeline:
1. Parsing a circuit description.
2. Transpiling the circuit for a specific hardware architecture.
3. Simulating the final physical circuit.
4. Printing the results.
"""

import numpy as np
from src.qvm.ir import QuantumCircuit
from src.qvm.parser import QASMParser
from src.qvm.architecture import get_linear_architecture
from src.qvm.transpiler import Transpiler
from src.qvm.simulator import Simulator
from src.qvm.util.export import to_openqasm2

def main():
    print("--- QVM Full Pipeline Example ---")

    # 1. Define a logical circuit that needs transpilation
    # We want to apply CNOT(0, 2) on a 3-qubit system.
    # On a linear chain 0-1-2, this is not possible directly.
    num_qubits = 3
    logical_circuit_desc = [
        {"name": "h", "qubits": [0]},
        {"name": "cx", "qubits": [0, 2]}
    ]
    logical_circuit = QASMParser.parse(logical_circuit_desc, num_qubits)
    print("\n[1] Original Logical Circuit:")
    print(logical_circuit)

    # 2. Define the target hardware architecture
    # A 3-qubit linear chain where qubits are connected as 0-1 and 1-2.
    target_arch = get_linear_architecture(num_qubits)
    print(f"\n[2] Target Architecture: {target_arch.name}")
    print(f"    Connectivity: {target_arch.connectivity}")

    # 3. Transpile the logical circuit to a physical circuit
    transpiler = Transpiler(target_arch)
    physical_circuit = transpiler.transpile(logical_circuit)
    print("\n[3] Transpiled Physical Circuit (with SWAPs):")
    print(physical_circuit)

    # 4. Simulate the final physical circuit
    simulator = Simulator()
    final_statevector = simulator.simulate(physical_circuit)
    probabilities = simulator.get_probabilities(final_statevector)
    
    print("\n[4] Simulation Results:")
    print(f"    Final Statevector (rounded): \n{np.round(final_statevector, 3)}")
    print(f"    Measurement Probabilities: \n{probabilities}")

    # Expected result:
    # The initial state is |000>. After H(0), it's 1/sqrt(2)(|000> + |100>).
    # The CNOT(0, 2) should produce 1/sqrt(2)(|000> + |101>).
    # This has probabilities {0: 0.5, 5: 0.5}.
    # The transpiled circuit should be equivalent.
    # E.g., for CNOT(0,2) on a 0-1-2 line, a common decomposition is:
    # SWAP(1,2), CNOT(0,1), SWAP(1,2). Let's trace it:
    # Start: 1/sqrt(2)(|000> + |100>)
    # SWAP(1,2): 1/sqrt(2)(|000> + |100>) (no change since q1, q2 are |0>)
    # CNOT(0,1): 1/sqrt(2)(|000> + |110>)
    # SWAP(1,2): 1/sqrt(2)(|000> + |101>) -> which is the correct final state.

    # 5. Export to OpenQASM 2.0
    qasm_code = to_openqasm2(physical_circuit)
    print("\n[5] Exported OpenQASM 2.0 Code:")
    print(qasm_code)


if __name__ == "__main__":
    main()
