# src/qvm/transpiler.py

"""
Transpiler for mapping logical quantum circuits to physical hardware architectures.

Strategies:
- greedy (default): legacy BFS routing with swap-back restoration to preserve logical mapping.
- sabre: lightweight SABRE-inspired heuristic with lookahead; optional mapping restoration.
"""

from collections import deque
import math
from typing import List, Tuple

from src.qvm.ir import QuantumCircuit
from src.qvm.architecture import TargetArchitecture, get_linear_architecture
from src.qvm.parser import QASMParser


class Transpiler:
    def __init__(self, target_architecture: TargetArchitecture, strategy: str = "greedy", restore_mapping: bool = True):
        self.architecture = target_architecture
        self.strategy = strategy
        self.restore_mapping = restore_mapping
        self._distance_cache = {}

    # Public API --------------------------------------------------
    def transpile(self, logical_circuit: QuantumCircuit) -> QuantumCircuit:
        if logical_circuit.num_qubits > self.architecture.num_qubits:
            raise ValueError("Logical circuit has more qubits than the target architecture.")
        if self.strategy == "sabre":
            return self._transpile_sabre(logical_circuit)
        return self._transpile_greedy(logical_circuit)

    # Greedy (legacy) --------------------------------------------
    def _transpile_greedy(self, logical_circuit: QuantumCircuit) -> QuantumCircuit:
        physical_circuit = QuantumCircuit(self.architecture.num_qubits)
        qubit_map = {i: i for i in range(logical_circuit.num_qubits)}
        inverse_map = {v: k for k, v in qubit_map.items()}

        for op in logical_circuit.operations:
            name, logical_qubits, params = op["name"], op["qubits"], op["params"]
            phys_qubits = [qubit_map[q] for q in logical_qubits]

            if len(logical_qubits) <= 1:
                physical_circuit.add_operation(name, phys_qubits, params)
                continue

            if len(logical_qubits) == 2:
                p1, p2 = phys_qubits
                if self.architecture.is_connected(p1, p2):
                    physical_circuit.add_operation(name, phys_qubits, params)
                    continue

                path = self._bfs_shortest_path(p1, p2)
                if not path or len(path) < 2:
                    raise RuntimeError(f"No path between qubits {p1} and {p2}")

                swap_pairs = []
                for i in range(len(path) - 2):
                    s1, s2 = path[i], path[i + 1]
                    swap_pairs.append((s1, s2))
                    physical_circuit.add_operation("swap", [s1, s2], [])
                    self._swap_update_maps(s1, s2, qubit_map, inverse_map)

                physical_circuit.add_operation(name, [path[-2], path[-1]], params)

                for s1, s2 in reversed(swap_pairs):
                    physical_circuit.add_operation("swap", [s1, s2], [])
                    self._swap_update_maps(s1, s2, qubit_map, inverse_map)
                continue

            physical_circuit.add_operation(name, phys_qubits, params)

        return physical_circuit

    # SABRE-inspired ---------------------------------------------
    def _transpile_sabre(self, logical_circuit: QuantumCircuit) -> QuantumCircuit:
        physical_circuit = QuantumCircuit(self.architecture.num_qubits)
        qubit_map = {i: i for i in range(logical_circuit.num_qubits)}
        inverse_map = {v: k for k, v in qubit_map.items()}

        ops = list(logical_circuit.operations)
        op_index = 0
        ready: List[Tuple[int, dict]] = []

        def enqueue_ready(start_idx: int) -> int:
            """Push next two-qubit gate into ready list; emit intervening 1-qubit gates immediately."""
            for j in range(start_idx, len(ops)):
                op = ops[j]
                if len(op["qubits"]) == 2:
                    ready.append((j, op))
                    return j + 1
                else:
                    phys = [qubit_map[q] for q in op["qubits"]]
                    physical_circuit.add_operation(op["name"], phys, op["params"])
            return len(ops)

        op_index = enqueue_ready(0)
        decay = 0.6

        while ready:
            _, op = ready[0]
            q1_log, q2_log = op["qubits"]
            p1, p2 = qubit_map[q1_log], qubit_map[q2_log]

            if self.architecture.is_connected(p1, p2):
                physical_circuit.add_operation(op["name"], [p1, p2], op["params"])
                ready.pop(0)
                op_index = enqueue_ready(op_index)
                continue

            best_swap = None
            best_cost = math.inf
            for edge in self.architecture.connectivity:
                s1, s2 = edge
                self._swap_update_maps(s1, s2, qubit_map, inverse_map)
                cost = self._heuristic_cost(ready, qubit_map, decay)
                if cost < best_cost:
                    best_cost = cost
                    best_swap = (s1, s2)
                self._swap_update_maps(s1, s2, qubit_map, inverse_map)  # revert

            if best_swap is None:
                raise RuntimeError("No swap candidate found; architecture may be disconnected.")

            s1, s2 = best_swap
            physical_circuit.add_operation("swap", [s1, s2], [])
            self._swap_update_maps(s1, s2, qubit_map, inverse_map)

        if self.restore_mapping:
            self._restore_identity_mapping(physical_circuit, qubit_map, inverse_map)

        return physical_circuit

    # Helpers ----------------------------------------------------
    def _swap_update_maps(self, p1, p2, qubit_map, inverse_map):
        l1 = inverse_map[p1]
        l2 = inverse_map[p2]
        qubit_map[l1], qubit_map[l2] = qubit_map[l2], qubit_map[l1]
        inverse_map[p1], inverse_map[p2] = inverse_map[p2], inverse_map[p1]

    def _heuristic_cost(self, ready, qubit_map, decay):
        """SABRE-like cost: sum of distances for front layer plus decayed lookahead."""
        if not ready:
            return 0.0
        total = 0.0
        front = ready[:3]  # small window
        for idx, (_, op) in enumerate(front):
            q1, q2 = op["qubits"]
            p1, p2 = qubit_map[q1], qubit_map[q2]
            total += (decay ** idx) * self._distance(p1, p2)
        return total

    def _distance(self, u, v):
        key = (min(u, v), max(u, v))
        if key in self._distance_cache:
            return self._distance_cache[key]
        dist = self._bfs_shortest_path_length(u, v)
        self._distance_cache[key] = dist
        return dist

    def _restore_identity_mapping(self, physical_circuit: QuantumCircuit, qubit_map, inverse_map):
        """Swap back to logical==physical labeling."""
        # While mapping not identity, swap misplaced qubits into place.
        for logical in range(len(qubit_map)):
            target_phys = logical
            current_phys = qubit_map[logical]
            if current_phys == target_phys:
                continue
            swap_partner_logical = inverse_map[target_phys]
            physical_circuit.add_operation("swap", [current_phys, target_phys], [])
            self._swap_update_maps(current_phys, target_phys, qubit_map, inverse_map)

    def _bfs_shortest_path(self, start_node: int, end_node: int) -> List[int]:
        if start_node == end_node:
            return [start_node]
        adj = {i: [] for i in range(self.architecture.num_qubits)}
        for q1, q2 in self.architecture.connectivity:
            adj[q1].append(q2)
            adj[q2].append(q1)
        queue = deque([(start_node, [start_node])])
        visited = {start_node}
        while queue:
            node, path = queue.popleft()
            for n in adj[node]:
                if n == end_node:
                    return path + [n]
                if n not in visited:
                    visited.add(n)
                    queue.append((n, path + [n]))
        return []

    def _bfs_shortest_path_length(self, start_node: int, end_node: int) -> int:
        if start_node == end_node:
            return 0
        adj = {i: [] for i in range(self.architecture.num_qubits)}
        for q1, q2 in self.architecture.connectivity:
            adj[q1].append(q2)
            adj[q2].append(q1)
        queue = deque([(start_node, 0)])
        visited = {start_node}
        while queue:
            node, dist = queue.popleft()
            for n in adj[node]:
                if n == end_node:
                    return dist + 1
                if n not in visited:
                    visited.add(n)
                    queue.append((n, dist + 1))
        return math.inf


# Example usage (manual test)
if __name__ == "__main__":
    logical_circuit_desc = [
        {"name": "h", "qubits": [0]},
        {"name": "cx", "qubits": [0, 2]},
        {"name": "cx", "qubits": [0, 2]},
    ]
    logical_qc = QASMParser.parse(logical_circuit_desc, 3)
    linear_3_arch = get_linear_architecture(3)
    transpiler = Transpiler(linear_3_arch, strategy="sabre", restore_mapping=False)
    physical_qc = transpiler.transpile(logical_qc)
    print(physical_qc)
