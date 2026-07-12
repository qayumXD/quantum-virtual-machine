# src/qvm/observable.py

"""
Observable / Hamiltonian system for computing expectation values.
Supports Pauli string operators and their linear combinations.

Example:
    H = Hamiltonian.from_dict({"ZZ": -1.0, "XI": 0.5, "IX": 0.5})
    energy = simulator.expectation_value(circuit, H)
"""

from __future__ import annotations
import numpy as np
from typing import Dict, List, Optional


# Pre-computed Pauli matrices
_PAULI = {
    "I": np.array([[1, 0], [0, 1]], dtype=complex),
    "X": np.array([[0, 1], [1, 0]], dtype=complex),
    "Y": np.array([[0, -1j], [1j, 0]], dtype=complex),
    "Z": np.array([[1, 0], [0, -1]], dtype=complex),
}


class PauliOp:
    """A single Pauli string with a coefficient.

    E.g. PauliOp("ZZI", coeff=-1.0) represents -1.0 · (Z ⊗ Z ⊗ I).

    The string must contain only characters I, X, Y, Z.
    The length must match the number of qubits at evaluation time.
    """

    __slots__ = ("pauli_string", "coeff")

    def __init__(self, pauli_string: str, coeff: float = 1.0):
        pauli_string = pauli_string.upper()
        if not all(c in "IXYZ" for c in pauli_string):
            raise ValueError(
                f"Pauli string must contain only I, X, Y, Z. Got: '{pauli_string}'"
            )
        if len(pauli_string) == 0:
            raise ValueError("Pauli string must be non-empty.")
        self.pauli_string = pauli_string
        self.coeff = float(coeff)

    @property
    def num_qubits(self) -> int:
        return len(self.pauli_string)

    def is_identity(self) -> bool:
        """True if all Pauli operators are identity."""
        return all(c == "I" for c in self.pauli_string)

    def to_matrix(self, num_qubits: Optional[int] = None) -> np.ndarray:
        """Build the full 2^n × 2^n matrix for this Pauli string.

        If num_qubits is None, uses the length of the Pauli string.
        If num_qubits > len(pauli_string), pads with identity on the right.
        """
        n = num_qubits if num_qubits is not None else self.num_qubits
        if n < self.num_qubits:
            raise ValueError(
                f"num_qubits ({n}) < Pauli string length ({self.num_qubits})"
            )

        # Build tensor product: P_0 ⊗ P_1 ⊗ ... ⊗ P_{n-1}
        matrices = [_PAULI[c] for c in self.pauli_string]
        # Pad with identity if needed
        for _ in range(n - self.num_qubits):
            matrices.append(_PAULI["I"])

        result = matrices[0]
        for m in matrices[1:]:
            result = np.kron(result, m)

        return self.coeff * result

    def __repr__(self):
        return f"PauliOp('{self.pauli_string}', coeff={self.coeff})"

    def __str__(self):
        if self.coeff == 1.0:
            return self.pauli_string
        elif self.coeff == -1.0:
            return f"-{self.pauli_string}"
        return f"{self.coeff}·{self.pauli_string}"


class Hamiltonian:
    """A sum of weighted Pauli strings: H = Σ cᵢ Pᵢ

    Example:
        H = Hamiltonian([
            PauliOp("ZZ", coeff=-1.0),
            PauliOp("XI", coeff=0.5),
            PauliOp("IX", coeff=0.5),
        ])

    Or more conveniently:
        H = Hamiltonian.from_dict({"ZZ": -1.0, "XI": 0.5, "IX": 0.5})
    """

    def __init__(self, terms: Optional[List[PauliOp]] = None):
        self.terms: List[PauliOp] = list(terms) if terms else []

    @classmethod
    def from_dict(cls, pauli_dict: Dict[str, float]) -> Hamiltonian:
        """Create a Hamiltonian from a dict mapping Pauli strings to coefficients.

        Example: Hamiltonian.from_dict({"ZZ": -1.0, "XI": 0.5, "IX": 0.5})
        """
        terms = [PauliOp(ps, coeff) for ps, coeff in pauli_dict.items()]
        return cls(terms)

    @property
    def num_qubits(self) -> int:
        """Infer qubit count from the longest Pauli string."""
        if not self.terms:
            return 0
        return max(t.num_qubits for t in self.terms)

    def to_matrix(self, num_qubits: Optional[int] = None) -> np.ndarray:
        """Build the full Hermitian matrix H = Σ cᵢ Pᵢ."""
        n = num_qubits if num_qubits is not None else self.num_qubits
        if n == 0:
            raise ValueError("Hamiltonian has no terms.")

        dim = 2 ** n
        matrix = np.zeros((dim, dim), dtype=complex)
        for term in self.terms:
            matrix += term.to_matrix(n)
        return matrix

    def eigenvalues(self, num_qubits: Optional[int] = None) -> np.ndarray:
        """Return the sorted eigenvalues of the Hamiltonian."""
        matrix = self.to_matrix(num_qubits)
        eigvals = np.linalg.eigvalsh(matrix)
        return np.sort(eigvals)

    def ground_state_energy(self, num_qubits: Optional[int] = None) -> float:
        """Return the exact ground state energy (smallest eigenvalue)."""
        return float(self.eigenvalues(num_qubits)[0])

    # ---- Arithmetic for combining Hamiltonians ----
    def __add__(self, other):
        if isinstance(other, Hamiltonian):
            return Hamiltonian(self.terms + other.terms)
        if isinstance(other, PauliOp):
            return Hamiltonian(self.terms + [other])
        return NotImplemented

    def __radd__(self, other):
        if isinstance(other, PauliOp):
            return Hamiltonian([other] + self.terms)
        if isinstance(other, (int, float)) and other == 0:
            return self  # Allows sum() to work
        return NotImplemented

    def __rmul__(self, scalar):
        if isinstance(scalar, (int, float)):
            return Hamiltonian([PauliOp(t.pauli_string, t.coeff * scalar) for t in self.terms])
        return NotImplemented

    def __mul__(self, scalar):
        return self.__rmul__(scalar)

    def __neg__(self):
        return -1 * self

    def __sub__(self, other):
        if isinstance(other, Hamiltonian):
            return self + (-other)
        return NotImplemented

    def __repr__(self):
        if not self.terms:
            return "Hamiltonian([])"
        return "Hamiltonian([" + ", ".join(repr(t) for t in self.terms) + "])"

    def __str__(self):
        if not self.terms:
            return "0"
        return " + ".join(str(t) for t in self.terms).replace(" + -", " - ")


# ---- Convenience constructors for common Hamiltonians ----

def pauli_z(qubit: int, num_qubits: int, coeff: float = 1.0) -> Hamiltonian:
    """Create Z_i operator: identity on all qubits except Z on qubit i."""
    s = "I" * qubit + "Z" + "I" * (num_qubits - qubit - 1)
    return Hamiltonian([PauliOp(s, coeff)])


def pauli_x(qubit: int, num_qubits: int, coeff: float = 1.0) -> Hamiltonian:
    """Create X_i operator."""
    s = "I" * qubit + "X" + "I" * (num_qubits - qubit - 1)
    return Hamiltonian([PauliOp(s, coeff)])


def zz_interaction(q1: int, q2: int, num_qubits: int, coeff: float = 1.0) -> Hamiltonian:
    """Create Z_i ⊗ Z_j interaction term."""
    chars = ["I"] * num_qubits
    chars[q1] = "Z"
    chars[q2] = "Z"
    return Hamiltonian([PauliOp("".join(chars), coeff)])
