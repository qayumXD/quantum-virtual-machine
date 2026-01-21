# src/qvm/architecture.py

"""
Defines data structures for representing target quantum hardware architectures.
"""

from typing import List, Set, Tuple

class TargetArchitecture:
    """
    Represents the constraints of a target quantum hardware, including
    qubit connectivity and the native gate set.
    """
    def __init__(self, name: str, num_qubits: int, connectivity: Set[Tuple[int, int]], native_gates: Set[str]):
        """
        Initializes a new TargetArchitecture.

        Args:
            name (str): The name of the architecture (e.g., "Linear-4", "IBM-Q-5").
            num_qubits (int): The total number of qubits in the architecture.
            connectivity (Set[Tuple[int, int]]): A set of tuples where each tuple represents
                                                  a physical connection between two qubits.
                                                  Connections are assumed to be bidirectional.
            native_gates (Set[str]): A set of gate names that are natively supported by the hardware.
        """
        if not isinstance(num_qubits, int) or num_qubits <= 0:
            raise ValueError("Number of qubits must be a positive integer.")
        
        self.name = name
        self.num_qubits = num_qubits
        self.connectivity = self._validate_and_normalize_connectivity(connectivity, num_qubits)
        self.native_gates = native_gates

    def _validate_and_normalize_connectivity(self, connectivity: Set[Tuple[int, int]], num_qubits: int) -> Set[Tuple[int, int]]:
        """Validates and ensures bidirectionality of connectivity."""
        normalized = set()
        for edge in connectivity:
            if not (isinstance(edge, tuple) and len(edge) == 2 and
                    isinstance(edge[0], int) and isinstance(edge[1], int) and
                    0 <= edge[0] < num_qubits and 0 <= edge[1] < num_qubits):
                raise ValueError(f"Invalid edge in connectivity: {edge}")
            # Add both (u, v) and (v, u) to ensure bidirectionality and easy lookup
            normalized.add(tuple(sorted(edge)))
        return normalized

    def is_connected(self, qubit1: int, qubit2: int) -> bool:
        """Checks if two physical qubits are directly connected."""
        return tuple(sorted((qubit1, qubit2))) in self.connectivity

    def __str__(self):
        return f"TargetArchitecture(name='{self.name}', num_qubits={self.num_qubits}, native_gates={self.native_gates})"

    def __repr__(self):
        return f"TargetArchitecture('{self.name}', {self.num_qubits}, {self.connectivity}, {self.native_gates})"

# Pre-defined architectures for convenience
def get_linear_architecture(num_qubits: int) -> TargetArchitecture:
    """Creates a linear chain architecture."""
    if num_qubits < 2:
        connectivity = set()
    else:
        connectivity = {(i, i + 1) for i in range(num_qubits - 1)}
    
    # A common, minimal native gate set
    native_gates = {"id", "rz", "sx", "x", "cx"}

    return TargetArchitecture(f"Linear-{num_qubits}", num_qubits, connectivity, native_gates)

def get_fully_connected_architecture(num_qubits: int) -> TargetArchitecture:
    """Creates a fully connected (all-to-all) architecture."""
    connectivity = set()
    if num_qubits >= 2:
        for i in range(num_qubits):
            for j in range(i + 1, num_qubits):
                connectivity.add((i, j))

    native_gates = {"id", "rz", "sx", "x", "cx"}

    return TargetArchitecture(f"FullyConnected-{num_qubits}", num_qubits, connectivity, native_gates)

# Example Usage
if __name__ == "__main__":
    linear_4 = get_linear_architecture(4)
    print(linear_4)
    print("Connectivity:", linear_4.connectivity)
    print("Is 0 and 1 connected?", linear_4.is_connected(0, 1))
    print("Is 0 and 2 connected?", linear_4.is_connected(0, 2))
    
    fully_connected_3 = get_fully_connected_architecture(3)
    print("\n" + str(fully_connected_3))
    print("Connectivity:", fully_connected_3.connectivity)
    print("Is 0 and 2 connected?", fully_connected_3.is_connected(0, 2))
