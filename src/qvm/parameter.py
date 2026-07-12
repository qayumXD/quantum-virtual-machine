# src/qvm/parameter.py

"""
Symbolic parameter system for parameterized quantum circuits.
Allows circuits to be defined with symbolic angles that are bound at runtime —
the foundation of all variational quantum algorithms (VQE, QAOA).
"""

from __future__ import annotations
import math
from typing import Dict, Set, Union


class Parameter:
    """A named symbolic parameter for use in gate angles.

    >>> theta = Parameter("theta")
    >>> expr = 2 * theta + 0.5
    >>> expr.evaluate({theta: 1.0})
    2.5
    """

    __slots__ = ("name", "_id")
    _counter = 0

    def __init__(self, name: str):
        if not isinstance(name, str) or not name:
            raise ValueError("Parameter name must be a non-empty string.")
        self.name = name
        Parameter._counter += 1
        self._id = Parameter._counter  # unique identity

    # ---- Arithmetic: produce ParameterExpression ----
    def __add__(self, other):
        return ParameterExpression._from_param(self).__add__(other)

    def __radd__(self, other):
        return ParameterExpression._from_param(self).__radd__(other)

    def __sub__(self, other):
        return ParameterExpression._from_param(self).__sub__(other)

    def __rsub__(self, other):
        return ParameterExpression._from_param(self).__rsub__(other)

    def __mul__(self, other):
        return ParameterExpression._from_param(self).__mul__(other)

    def __rmul__(self, other):
        return ParameterExpression._from_param(self).__rmul__(other)

    def __neg__(self):
        return ParameterExpression._from_param(self).__neg__()

    def __truediv__(self, other):
        return ParameterExpression._from_param(self).__truediv__(other)

    # ---- Identity ----
    def __hash__(self):
        return hash(self._id)

    def __eq__(self, other):
        return isinstance(other, Parameter) and self._id == other._id

    def __repr__(self):
        return f"Parameter('{self.name}')"

    def __str__(self):
        return self.name


class ParameterExpression:
    """A linear expression of Parameters: c₀ + Σ cᵢ·θᵢ

    Supports evaluation when given a binding map {Parameter → float}.
    """

    __slots__ = ("_coeffs", "_constant")

    def __init__(self, coeffs: Dict[Parameter, float], constant: float = 0.0):
        # Filter out zero coefficients
        self._coeffs = {p: c for p, c in coeffs.items() if c != 0.0}
        self._constant = float(constant)

    @classmethod
    def _from_param(cls, param: Parameter) -> ParameterExpression:
        return cls({param: 1.0}, 0.0)

    @classmethod
    def _from_constant(cls, value: float) -> ParameterExpression:
        return cls({}, float(value))

    # ---- Core API ----
    @property
    def parameters(self) -> Set[Parameter]:
        """Return the set of free (unbound) parameters."""
        return set(self._coeffs.keys())

    def is_bound(self) -> bool:
        """True if the expression has no free parameters (is a plain number)."""
        return len(self._coeffs) == 0

    def evaluate(self, bindings: Dict[Parameter, float] = None) -> float:
        """Substitute parameter values and return a float.

        Raises ValueError if any parameter lacks a binding.
        """
        if bindings is None:
            bindings = {}
        result = self._constant
        for param, coeff in self._coeffs.items():
            if param not in bindings:
                raise ValueError(
                    f"Parameter '{param.name}' has no binding. "
                    f"Provide a value via bindings dict."
                )
            result += coeff * bindings[param]
        return result

    # ---- Arithmetic ----
    def __add__(self, other):
        if isinstance(other, ParameterExpression):
            new_coeffs = dict(self._coeffs)
            for p, c in other._coeffs.items():
                new_coeffs[p] = new_coeffs.get(p, 0.0) + c
            return ParameterExpression(new_coeffs, self._constant + other._constant)
        if isinstance(other, Parameter):
            return self.__add__(ParameterExpression._from_param(other))
        if isinstance(other, (int, float)):
            return ParameterExpression(dict(self._coeffs), self._constant + other)
        return NotImplemented

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        if isinstance(other, ParameterExpression):
            return self.__add__(-other)
        if isinstance(other, Parameter):
            return self.__sub__(ParameterExpression._from_param(other))
        if isinstance(other, (int, float)):
            return ParameterExpression(dict(self._coeffs), self._constant - other)
        return NotImplemented

    def __rsub__(self, other):
        return (-self).__add__(other)

    def __neg__(self):
        return ParameterExpression(
            {p: -c for p, c in self._coeffs.items()},
            -self._constant,
        )

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return ParameterExpression(
                {p: c * other for p, c in self._coeffs.items()},
                self._constant * other,
            )
        return NotImplemented

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            if other == 0:
                raise ZeroDivisionError("Division by zero in ParameterExpression")
            return self.__mul__(1.0 / other)
        return NotImplemented

    # ---- Display ----
    def __repr__(self):
        parts = []
        for param, coeff in self._coeffs.items():
            if coeff == 1.0:
                parts.append(param.name)
            elif coeff == -1.0:
                parts.append(f"-{param.name}")
            else:
                parts.append(f"{coeff}*{param.name}")
        if self._constant != 0.0 or not parts:
            parts.append(str(self._constant))
        return " + ".join(parts).replace(" + -", " - ")

    def __str__(self):
        return self.__repr__()


def is_parameterized(value) -> bool:
    """Check if a value contains unbound symbolic parameters."""
    if isinstance(value, Parameter):
        return True
    if isinstance(value, ParameterExpression):
        return not value.is_bound()
    return False


def resolve_param(value, bindings: Dict[Parameter, float] = None) -> float:
    """Resolve a value that may be a Parameter, ParameterExpression, or float."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, Parameter):
        expr = ParameterExpression._from_param(value)
        return expr.evaluate(bindings or {})
    if isinstance(value, ParameterExpression):
        return value.evaluate(bindings or {})
    raise TypeError(f"Cannot resolve parameter of type {type(value)}")
