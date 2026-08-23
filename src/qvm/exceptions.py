# src/qvm/exceptions.py

"""
Hierarchical domain exception system for QVM.

Every error raised by QVM derives from :class:`QVMError`, so callers can
catch a single base class for structured error handling::

    try:
        Simulator().simulate(qc)
    except QVMError:
        ...

For backwards compatibility the concrete classes also inherit from the
built-in exceptions they replace (``ValueError`` / ``RuntimeError`` /
``ImportError``), so existing ``except ValueError`` clauses keep working.
"""


class QVMError(Exception):
    """Root exception for all QVM operations."""


class QVMParseError(QVMError, ValueError):
    """Raised on syntax or grammar parsing failures."""


class QVMCompilationError(QVMError, ValueError):
    """Raised during routing, decomposition, or conversion failures."""


class UnsupportedGateError(QVMCompilationError):
    """Raised when a gate is not supported by a subsystem.

    Raised instead of silently dropping an operation in converters,
    simulators, and decomposers.
    """


class MissingBackendError(QVMError, ImportError):
    """Raised when an optional backend framework (Qiskit / Cirq) is required
    but not installed.  Install it with ``pip install quantum-virtual-machine[qiskit]``
    or ``pip install quantum-virtual-machine[cirq]``."""


class QVMConversionError(QVMCompilationError):
    """Raised when a circuit cannot be faithfully converted between formats."""


class QVMRuntimeError(QVMError, RuntimeError):
    """Raised during simulation execution failures."""


class QVMResourceLimitError(QVMRuntimeError):
    """Raised on memory or operation limit breaches."""
