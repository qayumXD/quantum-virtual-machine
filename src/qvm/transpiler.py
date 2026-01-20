# src/qvm/transpiler.py

"""
Transpiler for mapping logical quantum circuits to physical hardware architectures.
"""

from src.qvm.ir import QuantumCircuit
from src.qvm.architecture import TargetArchitecture, get_linear_architecture
from src.qvm.parser import QASMParser

from collections import deque

class Transpiler:
    """
    A simple transpiler that inserts SWAP gates to satisfy hardware connectivity.
    """
    def __init__(self, target_architecture: TargetArchitecture):
        self.architecture = target_architecture

    def _bfs_shortest_path(self, start_node: int, end_node: int) -> list:
        """Finds the shortest path between two nodes using BFS."""
        if start_node == end_node:
            return [start_node]
        
        # Build an adjacency list from the set of edges
        adj = {i: [] for i in range(self.architecture.num_qubits)}
        for q1, q2 in self.architecture.connectivity:
            adj[q1].append(q2)
            adj[q2].append(q1)

        queue = deque([(start_node, [start_node])])
        visited = {start_node}

        while queue:
            current_node, path = queue.popleft()
            if current_node == end_node:
                return path
            
            for neighbor in adj[current_node]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    new_path = list(path)
                    new_path.append(neighbor)
                    queue.append((neighbor, new_path))
        
        return [] # Return empty list if no path is found

    def transpile(self, logical_circuit: QuantumCircuit) -> QuantumCircuit:
        """
        Transpiles a logical circuit into a physical circuit that respects
        the connectivity constraints of the target architecture.
        """
        if logical_circuit.num_qubits > self.architecture.num_qubits:
            raise ValueError("Logical circuit has more qubits than the target architecture.")

        physical_circuit = QuantumCircuit(self.architecture.num_qubits)
        # logical_qubit_index -> physical_qubit_index
        qubit_map = {i: i for i in range(logical_circuit.num_qubits)}
        # physical_qubit_index -> logical_qubit_index
        inverse_qubit_map = {v: k for k, v in qubit_map.items()}


        for op in logical_circuit.operations:
            gate_name = op["name"]
            logical_qubits = op["qubits"]
            params = op["params"]

            physical_qubits = [qubit_map[q] for q in logical_qubits]

            if len(logical_qubits) <= 1:
                physical_circuit.add_operation(gate_name, physical_qubits, params)
            
            elif len(logical_qubits) == 2:
                q1_log, q2_log = logical_qubits[0], logical_qubits[1]
                q1_phys, q2_phys = physical_qubits[0], physical_qubits[1]

                if self.architecture.is_connected(q1_phys, q2_phys):
                    physical_circuit.add_operation(gate_name, physical_qubits, params)
                else:
                    # Pathfinding: Find shortest path for one of the qubits to reach the other's neighborhood
                    path = self._bfs_shortest_path(q1_phys, q2_phys)
                    if not path or len(path) < 2:
                        raise RuntimeError(f"No path between qubits {q1_phys} and {q2_phys}")

                    # Move logical qubit q1_log along the path to become adjacent to q2_log's final position
                    # We need to SWAP along the path from path[0] to path[-2]
                    for i in range(len(path) - 2):
                        p1, p2 = path[i], path[i+1]
                        physical_circuit.add_operation("swap", [p1, p2])
                        
                        # Update the qubit maps after the SWAP
                        log_at_p1 = inverse_qubit_map[p1]
                        log_at_p2 = inverse_qubit_map[p2]
                        qubit_map[log_at_p1], qubit_map[log_at_p2] = qubit_map[log_at_p2], qubit_map[log_at_p1]
                        inverse_qubit_map[p1], inverse_qubit_map[p2] = inverse_qubit_map[p2], inverse_qubit_map[p1]
                    
                    # After swaps, the logical qubit q1_log is now on physical qubit path[-2]
                    # and q2_log is on q2_phys (which is path[-1])
                    final_q1_phys = path[-2]
                    final_q2_phys = path[-1] # q2_phys did not move
                    
                    # Apply the original gate to the now-adjacent physical qubits
                    physical_circuit.add_operation(gate_name, [final_q1_phys, final_q2_phys], params)

            else:
                physical_circuit.add_operation(gate_name, physical_qubits, params)

        return physical_circuit

# Example Usage
if __name__ == "__main__":
    # 1. Define a logical circuit that would require a SWAP on a linear chain
    # CNOT(0, 2) on a 3-qubit system
    logical_circuit_desc = [
        {"name": "h", "qubits": [0]},
        {"name": "cx", "qubits": [0, 2]}
    ]
    logical_qc = QASMParser.parse(logical_circuit_desc, 3)
    print("Original Logical Circuit:")
    print(logical_qc)

    # 2. Define a target architecture with limited connectivity
    linear_3_arch = get_linear_architecture(3)
    print("\nTarget Architecture:")
    print(linear_3_arch)
    print("Connectivity:", linear_3_arch.connectivity)


    # 3. Transpile the circuit
    transpiler = Transpiler(linear_3_arch)
    physical_qc = transpiler.transpile(logical_qc)
    
    print("\nTranspiled Physical Circuit (basic, no SWAPs):")
    print(physical_qc)
    
    # In a future version with SWAP insertion, the output would be different.
    # For a CNOT(0,2) on a line [0-1-2], a possible transpilation is:
    # SWAP(1, 2)
    # CNOT(0, 1)
    # SWAP(1, 2)
    # The qubit map would change accordingly.
