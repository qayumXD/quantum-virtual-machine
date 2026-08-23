# src/qvm/synthesis.py
"""Exact ancilla-free synthesis of multi-controlled gates from the QVM
basis vocabulary (h, rx/ry/rz/p, cx, cz, swap, rxx/rzz, cp, ccx).

Every builder here returns a list of operation dictionaries in the same
shape used by ``QuantumCircuit.add_operation``, so decomposer, simulator
and importers share one source of truth.

Constructions (all validated against Qiskit's reference unitaries):

* Multi-controlled rotations (``mcry`` / ``mcrz`` / ``mcrx``) use the
  half-angle CX-conjugation recursion::

      C^k Rot(theta) = C^{k-1} Rot(theta/2) . CX . C^{k-1} Rot(-theta/2) . CX

* Multi-controlled phase ``mcp(lambda)`` splits the projector::

      |1..1><1..1| over (S, t)  =  P_S x (I + Z_t) / 2

    into a control-line phase (recursively a plain ``cp`` chain) plus an
    ``mcrz`` on the target, giving exact phase semantics without the
    stray conditional phase a naive CX-conjugation produces.

* ``mcx`` is the Hadamard-conjugated ``mcp(pi)``.
"""

from typing import Dict, List, Sequence

_ROT_AXIS = {"rx", "ry", "rz"}


def _op(name: str, qubits: Sequence[int], params=None) -> Dict:
    op = {"name": name, "qubits": list(qubits), "params": list(params or [])}
    return op


# ---------------------------------------------------------------------------
# Multi-controlled rotations (exact)
# ---------------------------------------------------------------------------
def _mc_rot_ops(controls: Sequence[int], target: int, theta, axis: str,
                out: List[Dict]) -> None:
    if axis not in _ROT_AXIS:
        raise ValueError(f"unsupported rotation axis '{axis}'")
    cs = list(controls)
    if not cs:
        out.append(_op(axis, [target], [theta]))
        return
    head, rest = cs[0], cs[1:]
    _mc_rot_ops(rest, target, theta / 2, axis, out)
    out.append(_op("cx", [head, target]))
    _mc_rot_ops(rest, target, -theta / 2, axis, out)
    out.append(_op("cx", [head, target]))


def mc_ry_ops(controls, target, theta):        # -> List[Dict]
    ops: List[Dict] = []
    _mc_rot_ops(controls, target, theta, "ry", ops)
    return ops


def mc_rz_ops(controls, target, theta):
    ops: List[Dict] = []
    _mc_rot_ops(controls, target, theta, "rz", ops)
    return ops


def mc_rx_ops(controls, target, theta):
    # Direct recursion is not exact for the X axis; conjugate the verified
    # MCRZ instead:  H . RZ(theta) . H = RX(theta)  (target-local basis change,
    # controls untouched).
    ops: List[Dict] = [_op("h", [target])]
    _mc_rot_ops(controls, target, theta, "rz", ops)
    ops.append(_op("h", [target]))
    return ops


# ---------------------------------------------------------------------------
# Control-line phase: e^{i*beta} whenever every qubit in `qubits` is |1>
# ---------------------------------------------------------------------------
def _phase_all_ones_ops(qubits: Sequence[int], beta, out: List[Dict]) -> None:
    qs = list(qubits)
    if len(qs) == 1:
        # single-qubit pure phase: p(beta) acts on |1> only
        out.append(_op("p", [qs[0]], [beta]))
        return
    last, rest = qs[-1], qs[:-1]
    _phase_all_ones_ops(rest, beta / 2, out)
    # exp(i*(beta/2)*P_rest*Z_last) == mc_rz(last; +beta): rz(beta)=e^{-i beta Z/2}
    # puts e^{-i beta/2} on |1>, cancelling the prefix phase there and leaving
    # e^{+i beta} exactly when every qubit in `qs` is |1>.
    _mc_rot_ops(rest, last, beta, "rz", out)


# ---------------------------------------------------------------------------
# MCP / MCZ / MCX
# ---------------------------------------------------------------------------
def mcp_ops(controls: Sequence[int], target: int, lam) -> List[Dict]:
    """Multi-controlled phase: diag(..., e^{i*lam}) on |1..1> of controls+t."""
    cs = list(controls)
    if len(cs) == 0:
        raise ValueError("mcp requires at least one control")
    if len(cs) == 1:
        return [_op("cp", [cs[0], target], [lam])]
    # |1_S><1_S| x (I - Z_t)/2 split:
    #   exp(i*lam/2 * P_S)        -> control-line phase (any target value)
    #   exp(-i*lam/2 * Z_t * P_S) -> mcrz(theta=+lam): rz(th)=e^{-i th Z/2}
    ops: List[Dict] = []
    _phase_all_ones_ops(cs, lam / 2, ops)
    _mc_rot_ops(cs, target, lam, "rz", ops)
    return ops


def mcz_ops(controls: Sequence[int], target: int) -> List[Dict]:
    return mcp_ops(controls, target, 3.141592653589793)


def mcx_ops(controls: Sequence[int], target: int) -> List[Dict]:
    """Hadamard-conjugated MCZ: flips target iff all controls are |1>."""
    ops = [_op("h", [target])]
    ops.extend(mcz_ops(controls, target))
    ops.append(_op("h", [target]))
    return ops


# Foreign-name table used by the Qiskit importer ----------------------------
QISKIT_MC_ALIASES = {
    "mcx": "mcx",
    "mcx_gray": "mcx",
    "mcx_recursive": "mcx",
    "mcx_vchain": "mcx",
    "c3x": "mcx",
    "c4x": "mcx",
    "mcz": "mcz",
    "ccz": "mcz",
    "mcphase": "mcp",
    "mcu1": "mcp",
    "mcry": "mcry",
    "mcrz": "mcrz",
    "mcrx": "mcrx",
}


def lower_macro(name: str, qubits: Sequence[int], params) -> List[Dict]:
    """Lower a macro gate name into vocabulary operations.

    Raises ValueError for unknown macros or arity violations so callers can
    surface precise errors instead of silently mis-lowering.
    """
    qs = list(qubits)
    kind = QISKIT_MC_ALIASES.get(name, name)
    n_params = len(params or [])

    if kind == "mcx":
        if len(qs) < 2:
            raise ValueError("mcx needs >=1 control + target")
        return mcx_ops(qs[:-1], qs[-1])
    if kind == "mcz":
        if len(qs) < 2:
            raise ValueError("mcz needs >=1 control + target")
        return mcz_ops(qs[:-1], qs[-1])
    if kind == "mcp":
        if len(qs) < 2 or n_params != 1:
            raise ValueError("mcp/mcphase/mcu1 needs >=1 control, target, 1 angle")
        return mcp_ops(qs[:-1], qs[-1], float(params[0]))
    if kind in ("mcry", "mcrz", "mcrx"):
        axis = kind[2]
        if len(qs) < 2 or n_params != 1:
            raise ValueError(f"{kind} needs >=1 control, target, 1 angle")
        builder = {"mcry": mc_ry_ops, "mcrz": mc_rz_ops, "mcrx": mc_rx_ops}[kind]
        return builder(qs[:-1], qs[-1], float(params[0]))
    raise ValueError(f"unknown macro gate '{name}'")
