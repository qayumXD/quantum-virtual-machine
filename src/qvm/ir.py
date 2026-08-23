# src/qvm/ir.py

"""
Intermediate Representation (IR) for Quantum Circuits.
Extends the IR to support OpenQASM 3.0 classical registers, conditional operations,
and parameterized circuits for variational algorithms (VQE, QAOA).
"""

import re
from typing import List, Dict, Optional, Any, Set

import numpy as np

from qvm.parameter import Parameter, ParameterExpression, is_parameterized, resolve_param
from qvm.exceptions import (
    QVMError,
    QVMConversionError,
    UnsupportedGateError,
    MissingBackendError,
)
from qvm import synthesis

# Optional imports for external backends – they are loaded lazily so the core library works without them.
try:
    import qiskit
    from qiskit import QuantumCircuit as QiskitCircuit
    try:
        from qiskit_aer import AerSimulator
    except ImportError:
        from qiskit.providers.aer import AerSimulator
except ImportError:  # pragma: no cover
    qiskit = None
    QiskitCircuit = None
    AerSimulator = None

try:
    import cirq
except ImportError:  # pragma: no cover
    cirq = None

class QuantumCircuit:
    def __init__(self, num_qubits: int):
        if not isinstance(num_qubits, int) or num_qubits <= 0:
            raise ValueError("Number of qubits must be a positive integer.")
        self.num_qubits = num_qubits
        self.operations = []  # List of dictionaries: gate, qubits, params, condition, target_bit
        self.classical_registers: Dict[str, int] = {}  # name -> size

    def add_classical_register(self, name: str, size: int):
        """Declares a classical bit register."""
        if name in self.classical_registers:
            raise ValueError(f"Classical register '{name}' already exists.")
        self.classical_registers[name] = size

    def add_operation(self, gate_name: str, qubits: list, params: list = None, condition: dict = None, target_bit: tuple = None, duration: str = None, label: str = None, jump_to: str = None, classical_op: dict = None):
        """Add a quantum or classical operation to the circuit.

        The method now validates known gate parameters against a simple registry.
        """
        """
        Adds a quantum or classical operation to the circuit.

        Args:
            gate_name (str): The name (e.g., "h", "measure", "classical_op").
            qubits (list): Target quantum bits.
            params (list, optional): Gate parameters.
            condition (dict, optional): {"register": str, "index": int, "value": int}
            target_bit (tuple, optional): (register_name, index) for results.
            duration (str, optional): Timing string.
            label (str, optional): Label for jumps.
            jump_to (str, optional): Target label for jumps.
            classical_op (dict, optional): {"op": str, "target": tuple, "args": list}
        """
        if not isinstance(gate_name, str) or not gate_name:
            raise ValueError("Gate name must be a non-empty string.")
        if gate_name not in ["label", "jump", "classical_op", "delay"]:
            # Gate registry: name -> expected parameter count.
            # Multi-controlled macros (mcx/mcz/mcp/mcry/...) are validated
            # here and lowered to basis gates by QuantumCircuit.lowered().
            GATE_SPEC = {
                "h": 0, "x": 0, "y": 0, "z": 0,
                "cx": 0, "cz": 0, "swap": 0, "ccx": 0, "toffoli": 0,
                "id": 0, "sx": 0, "sxdg": 0, "s": 0, "sdg": 0, "t": 0, "tdg": 0,
                "rx": 1, "ry": 1, "rz": 1, "p": 1,
                "rxx": 1, "rzz": 1, "cp": 1,
                "measure": 0, "barrier": 0,
                "mcx": 0, "mcz": 0, "mcp": 1,
                "mcry": 1, "mcrz": 1, "mcrx": 1,
            }
            _MACRO_ALIASES = {"mcphase": "mcp", "mcu1": "mcp"}
            gate_name = _MACRO_ALIASES.get(gate_name, gate_name)
            # Gate registry: name -> exact number of qubits the gate acts on.
            # measure/barrier act on one or more qubits (variable arity);
            # multi-controlled macros act on >= 2 (controls + target).
            GATE_ARITY = {
                "h": 1, "x": 1, "y": 1, "z": 1, "id": 1,
                "sx": 1, "sxdg": 1, "s": 1, "sdg": 1, "t": 1, "tdg": 1,
                "rx": 1, "ry": 1, "rz": 1, "p": 1,
                "cx": 2, "cz": 2, "swap": 2, "rxx": 2, "rzz": 2, "cp": 2,
                "ccx": 3, "toffoli": 3,
            }
            if gate_name not in GATE_SPEC:
                raise UnsupportedGateError(
                    f"Unsupported gate '{gate_name}'. Add it to GATE_SPEC if needed."
                )
            if not isinstance(qubits, list) or not all(isinstance(q, int) for q in qubits):
                raise ValueError(f"Qubits must be a list of integers. Got: {qubits}")

            if gate_name in ("measure", "barrier"):
                if len(qubits) < 1:
                    raise ValueError(f"Gate '{gate_name}' requires at least one target qubit.")
            elif gate_name in ("mcx", "mcz", "mcp", "mcry", "mcrz", "mcrx"):
                if len(qubits) < 2:
                    raise ValueError(
                        f"Gate '{gate_name}' requires at least one control and a "
                        f"target qubit (>= 2 qubits), got {qubits}"
                    )
                if len(set(qubits)) != len(qubits):
                    raise ValueError(f"Gate '{gate_name}' requires distinct qubits, got {qubits}")
            else:
                arity = GATE_ARITY[gate_name]
                if len(qubits) != arity:
                    raise ValueError(
                        f"Gate '{gate_name}' acts on {arity} qubit(s), "
                        f"got {len(qubits)}: {qubits}"
                    )
                if arity == 2 and qubits[0] == qubits[1]:
                    raise ValueError(
                        f"Gate '{gate_name}' requires two distinct qubits, got {qubits}"
                    )

            if params is not None and not isinstance(params, list):
                raise ValueError("Parameters must be a list or None.")

            expected_params = GATE_SPEC[gate_name]
            actual_params = len(params) if params else 0
            if actual_params != expected_params:
                raise ValueError(f"Gate '{gate_name}' expects {expected_params} parameters, got {actual_params}.")
            # Validate param types: allow float, int, Parameter, ParameterExpression
            if params:
                for p_val in params:
                    if not isinstance(p_val, (int, float, Parameter, ParameterExpression)):
                        raise ValueError(
                            f"Parameter values must be int, float, Parameter, or ParameterExpression. "
                            f"Got: {type(p_val)}"
                        )
            if not isinstance(qubits, list) or not all(isinstance(q, int) and 0 <= q < self.num_qubits for q in qubits):
                raise ValueError(f"Qubits must be a list of integers within [0, {self.num_qubits-1}].")
        else:
            if qubits is not None and not isinstance(qubits, list):
                raise ValueError("Qubits must be a list or None.")

        if params is not None and not isinstance(params, list):
            raise ValueError("Parameters must be a list or None.")

        if condition:
            reg = condition.get("register")
            if reg not in self.classical_registers:
                raise ValueError(f"Unknown classical register in condition: {reg}")
            if not (0 <= condition.get("index", 0) < self.classical_registers[reg]):
                raise ValueError(f"Index out of bounds for classical register '{reg}'")

        if target_bit is not None:
            tb_reg, tb_idx = target_bit
            if tb_reg not in self.classical_registers:
                raise ValueError(
                    f"Measurement targets classical register '{tb_reg}' which was never declared. "
                    f"Declared registers: {list(self.classical_registers)}"
                )
            if not isinstance(tb_idx, int) or not (0 <= tb_idx < self.classical_registers[tb_reg]):
                raise ValueError(
                    f"Classical bit index {tb_idx} out of bounds for register "
                    f"'{tb_reg}' of size {self.classical_registers[tb_reg]}"
                )

        operation = {
            "name": gate_name,
            "qubits": qubits if qubits is not None else [],
            "params": params if params is not None else [],
            "condition": condition,
            "target_bit": target_bit,
            "duration": duration,
            "label": label,
            "jump_to": jump_to,
            "classical_op": classical_op
        }
        self.operations.append(operation)

    # -----------------------------------------------------------------
    # Parameterized circuit support
    # -----------------------------------------------------------------
    @property
    def parameters(self) -> Set[Parameter]:
        """Return the set of all unbound Parameters used in this circuit."""
        params = set()
        for op in self.operations:
            for p_val in op.get("params", []):
                if isinstance(p_val, Parameter):
                    params.add(p_val)
                elif isinstance(p_val, ParameterExpression):
                    params.update(p_val.parameters)
        return params

    def bind_parameters(self, bindings: Dict[Parameter, float]) -> "QuantumCircuit":
        """Return a new circuit with all parameters substituted with concrete values.

        Raises ValueError if any parameter is left unbound.
        """
        new_qc = QuantumCircuit(self.num_qubits)
        new_qc.classical_registers = dict(self.classical_registers)
        for op in self.operations:
            new_op = dict(op)
            if op.get("params"):
                new_params = []
                for p_val in op["params"]:
                    new_params.append(resolve_param(p_val, bindings))
                new_op["params"] = new_params
            new_qc.operations.append(new_op)

        # Verify no unbound parameters remain
        remaining = new_qc.parameters
        if remaining:
            names = ", ".join(p.name for p in remaining)
            raise ValueError(f"Unbound parameters remain after binding: {names}")
        return new_qc

    # Multi-controlled macro names (canonical forms after aliasing).
    _MACRO_GATES = frozenset({"mcx", "mcz", "mcp", "mcry", "mcrz", "mcrx"})

    def lowered(self) -> "QuantumCircuit":
        """Return an equivalent circuit with multi-controlled macros
        (``mcx`` / ``mcz`` / ``mcp`` / ``mcry`` / ``mcrz`` / ``mcrx``)
        expanded into the basis vocabulary.

        Returns ``self`` unchanged when no macros are present.  Classical
        conditions and metadata on a macro are propagated to every generated
        sub-operation.  Symbolic parameters must be bound first.
        """
        from qvm import synthesis

        if not any(op["name"] in self._MACRO_GATES for op in self.operations):
            return self

        out = QuantumCircuit(self.num_qubits)
        out.classical_registers = dict(self.classical_registers)
        for op in self.operations:
            if op["name"] not in self._MACRO_GATES:
                out.operations.append(dict(op))
                continue
            try:
                params = [float(resolve_param(p)) for p in (op.get("params") or [])]
                sub_ops = synthesis.lower_macro(op["name"], op["qubits"], params)
            except QVMError:
                raise
            except (TypeError, ValueError) as exc:
                raise QVMConversionError(
                    f"Cannot lower '{op['name']}': {exc}. "
                    f"Bind symbolic parameters before lowering."
                ) from exc
            for sub in sub_ops:
                out.add_operation(
                    sub["name"],
                    list(sub["qubits"]),
                    params=list(sub["params"]),
                    condition=op.get("condition"),
                    target_bit=op.get("target_bit"),
                    label=op.get("label"),
                )
        return out

    def __str__(self):
        """Human‑readable representation of the circuit."""
        s = f"QuantumCircuit(num_qubits={self.num_qubits}, registers={self.classical_registers})\n"
        for op in self.operations:
            if op["name"] == "label":
                s += f"  LABEL {op['label']}:\n"
                continue
            if op["name"] == "jump":
                cond_str = f" IF {op['condition']}" if op['condition'] else ""
                s += f"  JUMP {op['jump_to']}{cond_str}\n"
                continue
            if op["name"] == "classical_op":
                s += f"  CLASSICAL {op['classical_op']['target']} = {op['classical_op']['op']} {op['classical_op']['args']}\n"
                continue
            
            cond_str = f" IF {op['condition']}" if op['condition'] else ""
            target_str = f" -> {op['target_bit']}" if op['target_bit'] else ""
            dur_str = f" [{op['duration']}]" if op['duration'] else ""
            s += f"  {op['name']}{dur_str} {op['qubits']}{cond_str}{target_str}\n"
        return s

    # ---------------------------------------------------------------------
    # Qiskit integration helpers
    # ---------------------------------------------------------------------
    def to_json(self) -> str:
        import json
        data = {
            "num_qubits": self.num_qubits,
            "classical_registers": self.classical_registers,
            "operations": self.operations
        }
        return json.dumps(data)

    @classmethod
    def from_json(cls, json_str: str) -> "QuantumCircuit":
        import json
        data = json.loads(json_str)
        qc = cls(data["num_qubits"])
        qc.classical_registers = data["classical_registers"]
        for op in data["operations"]:
            if op.get("target_bit"):
                op["target_bit"] = tuple(op["target_bit"])
            qc.operations.append(op)
        return qc

    def to_qasm(self) -> str:
        lines = ["OPENQASM 3.0;"]
        lines.append(f"qubit[{self.num_qubits}] q;")
        for name, size in self.classical_registers.items():
            lines.append(f"bit[{size}] {name};")
        
        for op in self.operations:
            name = op["name"]
            qubits = ", ".join(f"q[{q}]" for q in op["qubits"])
            params = ""
            if op["params"]:
                params = "(" + ", ".join(str(p) for p in op["params"]) + ")"
            
            if name == "measure":
                cr, idx = op["target_bit"]
                lines.append(f"{cr}[{idx}] = measure {qubits};")
            else:
                lines.append(f"{name}{params} {qubits};")
        return "\n".join(lines)

    @classmethod
    def from_qasm(cls, qasm_str: str) -> "QuantumCircuit":
        from qvm.qasm3_parser import OpenQASM3Parser
        parser = OpenQASM3Parser()
        return parser.parse(qasm_str)

    # ---------------------------------------------------------------------
    # Qiskit integration helpers
    # ---------------------------------------------------------------------

    # Canonical gate vocabulary shared by all converters.  Anything outside
    # this set raises UnsupportedGateError instead of being silently dropped.
    _PARAMLESS_1Q = frozenset({"h", "x", "y", "z", "s", "sdg", "t", "tdg", "sx", "sxdg", "id"})
    _ONE_PARAM_1Q = frozenset({"rx", "ry", "rz", "p"})
    _PARAMLESS_2Q = frozenset({"cx", "cz", "swap"})
    _ONE_PARAM_2Q = frozenset({"rxx", "rzz", "cp"})

    @staticmethod
    def _export_param(p, framework: str):
        """Convert a QVM parameter (float / Parameter / ParameterExpression)
        into a float or a parameter *name* for the target framework."""
        if isinstance(p, bool):
            raise QVMConversionError(f"Invalid boolean gate parameter: {p!r}")
        if isinstance(p, (int, float)):
            return float(p)
        if isinstance(p, Parameter):
            return p.name  # caller maps the name to the framework symbol
        if isinstance(p, ParameterExpression):
            if p.is_bound():
                return float(p.evaluate({}))
            raise QVMConversionError(
                f"Cannot export unbound symbolic expression '{p}' to {framework}. "
                f"Call bind_parameters() first."
            )
        raise QVMConversionError(
            f"Unsupported parameter type for {framework} export: {type(p).__name__}"
        )

    @classmethod
    def _transpile_to_basis(cls, qk_circuit: "QiskitCircuit") -> "QiskitCircuit":
        """Lower any Qiskit circuit onto the supported basis set using
        Qiskit's own compiler. Requires the [qiskit] extra."""
        if qiskit is None:
            raise MissingBackendError("Qiskit is not installed.")
        from qiskit import transpile
        basis = sorted(
            set(cls._PARAMLESS_1Q) | set(cls._ONE_PARAM_1Q)
            | set(cls._PARAMLESS_2Q) | set(cls._ONE_PARAM_2Q)
            | {"ccx", "measure"}
        )
        return transpile(qk_circuit, basis_gates=basis, optimization_level=0)

    @classmethod
    def _import_param(cls, value) -> "float | Parameter | ParameterExpression":
        """Convert a numeric foreign-framework parameter into a QVM parameter.

        Returns a float, an existing :class:`Parameter`, or raises
        :class:`QVMConversionError`.  Framework-specific symbol objects are
        handled by the framework-specific importers before calling this.
        """
        if isinstance(value, bool):
            raise QVMConversionError(f"Invalid boolean gate parameter: {value!r}")
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, Parameter):
            return value
        if isinstance(value, ParameterExpression):
            if value.is_bound():
                return float(value.evaluate({}))
            raise QVMConversionError(
                f"Unbound QVM expression '{value}' cannot be re-imported; "
                f"bind parameters first."
            )
        raise QVMConversionError(
            f"Unsupported parameter type for import: {type(value).__name__}"
        )

    @classmethod
    def qiskit_to_cirq(cls, qiskit_circuit: "QiskitCircuit") -> "cirq.Circuit":
        """Convert a Qiskit circuit to Cirq via the QVM IR pivot."""
        qc = cls.from_qiskit(qiskit_circuit)
        return qc.to_cirq()

    @classmethod
    def cirq_to_qiskit(cls, cirq_circuit: "cirq.Circuit") -> "QiskitCircuit":
        """Convert a Cirq circuit to Qiskit via the QVM IR pivot."""
        qc = cls.from_cirq(cirq_circuit)
        return qc.to_qiskit()

    def to_qiskit(self) -> "QiskitCircuit":
        """Convert this IR circuit to a Qiskit ``QuantumCircuit``.

        Raises:
            MissingBackendError: If Qiskit is not installed.
            UnsupportedGateError: If the circuit contains operations with no
                Qiskit mapping (control flow, classical arithmetic).
            QVMConversionError: On malformed measurements or unbound
                symbolic expressions.

        Note: global phase is not represented in the IR and is therefore lost.
        """
        if qiskit is None or QiskitCircuit is None:
            raise MissingBackendError(
                "Qiskit is not installed. Install it with: "
                "pip install 'quantum-virtual-machine[qiskit]'"
            )
        from qiskit import QuantumRegister, ClassicalRegister
        from qiskit.circuit import Parameter as QKParameter

        qr = QuantumRegister(self.num_qubits, "q")
        cregs = [ClassicalRegister(size, name) for name, size in self.classical_registers.items()]
        creg_by_name = {creg.name: creg for creg in cregs}
        qc = QiskitCircuit(qr, *cregs)

        def qp(p):
            v = self._export_param(p, "Qiskit")
            return QKParameter(v) if isinstance(v, str) else v

        for op in self.operations:
            name = op["name"]
            qs = [qr[i] for i in op["qubits"]]
            params = [qp(p) for p in (op.get("params") or [])]

            if name == "toffoli":
                name = "ccx"

            if name in ("label", "jump"):
                raise UnsupportedGateError(
                    f"Control-flow operation '{name}' cannot be exported to Qiskit. "
                    f"Flatten loops/unrolling before exporting."
                )
            elif name == "classical_op":
                raise UnsupportedGateError(
                    "Classical register arithmetic cannot be exported to Qiskit."
                )
            elif name == "delay":
                duration = op.get("duration")
                try:
                    ns = int(str(duration).rstrip(" ns"))
                except (TypeError, ValueError):
                    raise UnsupportedGateError(
                        f"Delay duration '{duration}' cannot be expressed as whole "
                        f"nanoseconds for Qiskit export."
                    )
                qc.delay(ns, qs[0], unit="ns")
            elif name == "barrier":
                qc.barrier(*qs)
            elif name == "measure":
                tb = op.get("target_bit")
                if not tb:
                    raise QVMConversionError(
                        "measure operation is missing its classical target_bit; "
                        "cannot export to Qiskit."
                    )
                reg_name, bit_idx = tb[0], tb[1]
                creg = creg_by_name.get(reg_name)
                if creg is None:
                    raise QVMConversionError(
                        f"measure targets undeclared classical register '{reg_name}'."
                    )
                if not (0 <= bit_idx < creg.size):
                    raise QVMConversionError(
                        f"Classical bit index {bit_idx} out of range for register "
                        f"'{reg_name}' of size {creg.size}."
                    )
                qc.measure(qs[0], creg[bit_idx])
            elif name in self._PARAMLESS_1Q:
                getattr(qc, name)(qs[0])
            elif name in self._ONE_PARAM_1Q:
                getattr(qc, name)(params[0], qs[0])
            elif name in self._PARAMLESS_2Q:
                getattr(qc, name)(qs[0], qs[1])
            elif name in self._ONE_PARAM_2Q:
                getattr(qc, name)(params[0], qs[0], qs[1])
            elif name == "ccx":
                qc.ccx(qs[0], qs[1], qs[2])
            elif name in ("mcx", "mcz", "mcp", "mcry", "mcrz", "mcrx"):
                controls, target = qs[:-1], qs[-1]
                if name == "mcx":
                    qc.mcx(controls, target)
                elif name == "mcz":
                    qc.mcz(controls, target)
                else:
                    getattr(qc, name)(params[0], *controls, target)
            else:
                supported = sorted(
                    self._PARAMLESS_1Q | self._ONE_PARAM_1Q | self._PARAMLESS_2Q
                    | self._ONE_PARAM_2Q | {"ccx", "measure", "barrier", "delay"}
                )
                raise UnsupportedGateError(
                    f"Gate '{op['name']}' cannot be exported to Qiskit. "
                    f"Supported gates: {supported}"
                )
        return qc

    @classmethod
    def from_qiskit(cls, qiskit_circuit: "QiskitCircuit",
                    transpile_foreign: bool = False) -> "QuantumCircuit":
        """Create a :class:`QuantumCircuit` from a Qiskit circuit.

        Multi-controlled gates (``mcx``, ``mcphase``, ``mcry``, ``ccz``, ...)
        are lowered exactly into the basis vocabulary during import.

        Args:
            transpile_foreign: when True, circuits containing other foreign
                gates are first passed through ``qiskit.transpile`` onto the
                supported basis set instead of raising UnsupportedGateError.

        Only the supported basis-gate vocabulary is accepted; anything else
        raises :class:`UnsupportedGateError` instead of being silently dropped.

        Note: Qiskit's ``global_phase`` attribute is ignored (physically
        unobservable).
        """
        if qiskit is None or QiskitCircuit is None:
            raise MissingBackendError(
                "Qiskit is not installed. Install it with: "
                "pip install 'quantum-virtual-machine[qiskit]'"
            )
        from qiskit.circuit import (
            Parameter as QKParameter,
            ParameterExpression as QKParameterExpression,
        )

        circuit = cls(qiskit_circuit.num_qubits)
        for creg in qiskit_circuit.cregs:
            circuit.add_classical_register(creg.name, creg.size)

        known = set(cls._PARAMLESS_1Q) | set(cls._ONE_PARAM_1Q) \
            | set(cls._PARAMLESS_2Q) | set(cls._ONE_PARAM_2Q) | {"ccx"}

        # Unify same-named symbolic parameters into one QVM Parameter
        # instance so bind_parameters() matches every occurrence.
        param_cache: Dict[str, Parameter] = {}

        def get_param(name: str) -> Parameter:
            if name not in param_cache:
                param_cache[name] = Parameter(name)
            return param_cache[name]

        for instruction in qiskit_circuit.data:
            operation = instruction.operation
            raw_name = operation.name.lower()
            qubits = [qiskit_circuit.find_bit(b).index for b in instruction.qubits]

            def get_params():
                """Lazily convert parameters only for recognized gates so that
                unknown gates always surface as UnsupportedGateError."""
                converted = []
                for p in (operation.params or []):
                    if isinstance(p, QKParameter):
                        converted.append(get_param(str(p.name)))
                    elif isinstance(p, QKParameterExpression):
                        free = getattr(p, "parameters", set())
                        if not free:
                            converted.append(float(p))
                        elif len(free) == 1:
                            # Linear single-parameter expressions map onto
                            # QVM's own ParameterExpression: c·θ + d.
                            # NOTE: sympify must be told that parameter names
                            # are Symbols — bare 'gamma' would otherwise parse
                            # as the Euler Gamma *function*.
                            import sympy
                            sym_name = str(next(iter(free)).name)
                            expr = sympy.sympify(
                                str(p), locals={sym_name: sympy.Symbol(sym_name)}
                            )
                            sym = next(iter(expr.free_symbols))
                            name = str(sym)
                            coeff = float(expr.coeff(sym))
                            const = float(expr.coeff(sym, 0))
                            if abs(coeff - 1.0) < 1e-12 and abs(const) < 1e-12:
                                converted.append(get_param(name))
                            else:
                                converted.append(
                                    ParameterExpression({get_param(name): coeff}, const)
                                )
                        else:
                            raise QVMConversionError(
                                f"Symbolic Qiskit expression '{p}' cannot be imported. "
                                f"Only single-parameter linear expressions or "
                                f"numeric angles are supported."
                            )
                    else:
                        converted.append(cls._import_param(p))
                return converted

            if raw_name == "measure":
                clbits = instruction.clbits
                if not clbits:
                    raise QVMConversionError(
                        "Qiskit measure instruction has no classical bit target."
                    )
                cb = clbits[0]
                regs = qiskit_circuit.find_bit(cb).registers
                if regs:
                    target_bit = (regs[0][0].name, regs[0][1])
                else:
                    target_bit = ("c", qiskit_circuit.find_bit(cb).index)
                circuit.add_operation("measure", qubits, target_bit=target_bit)
            elif raw_name == "barrier":
                circuit.add_operation("barrier", qubits)
            elif raw_name == "delay":
                duration = operation.duration
                unit = getattr(operation, "unit", None) or "dt"
                circuit.add_operation("delay", qubits, duration=f"{duration}{unit}")
            elif raw_name in ("toffoli", "ccx"):
                circuit.add_operation("ccx", qubits)
            elif raw_name in known:
                circuit.add_operation(raw_name, qubits, params=get_params() or None)
            elif raw_name in synthesis.QISKIT_MC_ALIASES:
                # Multi-controlled family: lower exactly into the vocabulary.
                params = [float(p) for p in get_params()]
                for sub in synthesis.lower_macro(raw_name, qubits, params):
                    circuit.add_operation(
                        sub["name"], list(sub["qubits"]),
                        params=list(sub["params"]) or None,
                    )
            else:
                if transpile_foreign:
                    lowered = cls._transpile_to_basis(qiskit_circuit)
                    return cls.from_qiskit(lowered, transpile_foreign=False)
                raise UnsupportedGateError(
                    f"Qiskit gate '{operation.name}' cannot be imported into QVM IR. "
                    f"Supported basis gates: "
                    f"{sorted(known | {'measure', 'barrier', 'delay'})}; multi-controlled "
                    f"macros ({sorted(synthesis.QISKIT_MC_ALIASES)}) are lowered automatically. "
                    f"Pass transpile_foreign=True to auto-transpile anything else."
                )
        return circuit

    def run_qiskit_simulator(self, shots: int = 1024) -> dict:
        """Execute the circuit on Qiskit's Aer simulator and return measurement counts.
        """
        if AerSimulator is None:
            raise MissingBackendError(
                "qiskit-aer is not installed. Install it with: "
                "pip install 'quantum-virtual-machine[qiskit]'"
            )
        qc = self.to_qiskit()
        sim = AerSimulator()
        result = sim.run(qc, shots=shots).result()
        return result.get_counts()

    # ---------------------------------------------------------------------
    # Cirq integration helpers
    # ---------------------------------------------------------------------
    def to_cirq(self) -> "cirq.Circuit":
        """Convert this IR circuit to a Cirq :class:`Circuit`.

        Raises MissingBackendError if Cirq is not installed and
        UnsupportedGateError / QVMConversionError instead of silently dropping
        operations it cannot represent.

        Measurement keys use the canonical ``"<register>[<index>]"`` format
        (legacy tuple-string keys are still understood when importing).
        Barriers are emitted as identity operations on their wires to preserve
        moment ordering, since Cirq has no barrier primitive.
        """
        if cirq is None:
            raise MissingBackendError(
                "Cirq is not installed. Install it with: "
                "pip install 'quantum-virtual-machine[cirq]'"
            )
        import numpy as _np

        circuit = cirq.Circuit()
        qubit_map = {i: cirq.LineQubit(i) for i in range(self.num_qubits)}
        pi = _np.pi

        def cp(p):
            v = self._export_param(p, "Cirq")
            if isinstance(v, str):
                import sympy
                return sympy.Symbol(v)
            return v

        for op in self.operations:
            name = op["name"]
            qs = [qubit_map[i] for i in op["qubits"]]
            params = [cp(p) for p in (op.get("params") or [])]

            if name == "toffoli":
                name = "ccx"

            if name in ("label", "jump"):
                raise UnsupportedGateError(
                    f"Control-flow operation '{name}' cannot be exported to Cirq. "
                    f"Flatten loops/unrolling before exporting."
                )
            elif name == "classical_op":
                raise UnsupportedGateError(
                    "Classical register arithmetic cannot be exported to Cirq."
                )
            elif name == "delay":
                duration = op.get("duration")
                try:
                    nanos = int(str(duration).rstrip(" ns"))
                except (TypeError, ValueError):
                    raise UnsupportedGateError(
                        f"Delay duration '{duration}' cannot be expressed as whole "
                        f"nanoseconds for Cirq export."
                    )
                circuit.append(cirq.wait(*qs, nanos=nanos))
            elif name == "barrier":
                for q in qs:
                    circuit.append(cirq.I(q))
            elif name == "measure":
                tb = op.get("target_bit")
                if not tb:
                    raise QVMConversionError(
                        "measure operation is missing its classical target_bit; "
                        "cannot export to Cirq."
                    )
                circuit.append(cirq.measure(qs[0], key=f"{tb[0]}[{tb[1]}]"))
            elif name in self._PARAMLESS_1Q:
                gate = {
                    "h": cirq.H, "x": cirq.X, "y": cirq.Y, "z": cirq.Z,
                    "s": cirq.S, "t": cirq.T,
                    "sdg": cirq.S ** -1, "tdg": cirq.T ** -1,
                    "sx": cirq.X ** 0.5, "sxdg": cirq.X ** -0.5,
                    "id": cirq.I,
                }[name]
                circuit.append(gate(qs[0]))
            elif name in self._ONE_PARAM_1Q:
                theta = params[0]
                gate = {
                    "rx": cirq.rx(theta), "ry": cirq.ry(theta), "rz": cirq.rz(theta),
                    "p": cirq.Z ** (theta / pi),
                }[name]
                circuit.append(gate(qs[0]))
            elif name in self._PARAMLESS_2Q:
                gate = {"cx": cirq.CNOT, "cz": cirq.CZ, "swap": cirq.SWAP}[name]
                circuit.append(gate(*qs))
            elif name in self._ONE_PARAM_2Q:
                theta = params[0]
                gate = {
                    "rxx": cirq.XXPowGate(exponent=theta / pi),
                    "rzz": cirq.ZZPowGate(exponent=theta / pi),
                    "cp": cirq.CZPowGate(exponent=theta / pi),
                }[name]
                circuit.append(gate(*qs))
            elif name == "ccx":
                circuit.append(cirq.TOFFOLI(qs[0], qs[1], qs[2]))
            else:
                supported = sorted(
                    self._PARAMLESS_1Q | self._ONE_PARAM_1Q | self._PARAMLESS_2Q
                    | self._ONE_PARAM_2Q | {"ccx", "measure", "barrier", "delay"}
                )
                raise UnsupportedGateError(
                    f"Gate '{op['name']}' cannot be exported to Cirq. "
                    f"Supported gates: {supported}"
                )
        return circuit

    # Matches canonical "<register>[<index>]" measurement keys.
    _MEASURE_KEY_RE = re.compile(r"^(?P<reg>.+)\[(?P<idx>\d+)\]$")

    @classmethod
    def _parse_measure_key(cls, key) -> tuple:
        """Parse a Cirq measurement key into a ``(register, index)`` tuple.

        Supports the canonical ``reg[idx]`` format plus legacy formats
        (``('reg', idx)`` tuple-strings and bare integers).
        """
        key = str(key)
        m = cls._MEASURE_KEY_RE.match(key)
        if m:
            return m.group("reg"), int(m.group("idx"))
        # Legacy tuple-string format: "('c', 0)"
        if key.startswith("(") and key.endswith(")"):
            inner = key[1:-1].split(",")
            if len(inner) == 2:
                try:
                    return inner[0].strip().strip("'\" "), int(inner[1])
                except ValueError:
                    pass
        # Bare integer index → default register 'c'
        if key.isdigit():
            return "c", int(key)
        return key, 0

    @staticmethod
    def _sort_measure_key(key) -> tuple:
        reg, idx = QuantumCircuit._parse_measure_key(key)
        return (reg, idx)

    @classmethod
    def from_cirq(cls, cirq_circuit: "cirq.Circuit") -> "QuantumCircuit":
        """Create a :class:`QuantumCircuit` from a Cirq circuit.

        Only the supported basis-gate vocabulary is accepted; anything else
        raises :class:`UnsupportedGateError` instead of being silently dropped.

        PowGates with arbitrary exponents are imported as their continuous
        rotation equivalents (e.g. ``XPowGate(e)`` → ``rx(pi*e)``); canonical
        fractions keep their named gates (``Z**0.25`` → ``t``).
        Symbolic single-symbol angles import as :class:`Parameter` /
        :class:`ParameterExpression`.
        """
        if cirq is None:
            raise MissingBackendError(
                "Cirq is not installed. Install it with: "
                "pip install 'quantum-virtual-machine[cirq]'"
            )
        import sympy

        indices = [q.x for op in cirq_circuit.all_operations() for q in op.qubits]
        num_qubits = (max(indices) + 1) if indices else 1
        circuit = cls(num_qubits)
        pi = float(np.pi)

        # Pre-pass: declare classical registers referenced by single-qubit
        # measurements so add_operation target_bit validation passes.
        for op in cirq_circuit.all_operations():
            gate = op.gate
            if isinstance(gate, cirq.MeasurementGate) and len(op.qubits) == 1:
                reg, idx = cls._parse_measure_key(gate.key)
                known_size = circuit.classical_registers.get(reg, 0)
                if idx >= known_size:
                    if reg in circuit.classical_registers:
                        circuit.classical_registers[reg] = idx + 1
                    else:
                        circuit.add_classical_register(reg, idx + 1)

        def exp_to_angle(g):
            """Recover the rotation angle θ = π·exponent from a Cirq PowGate.

            Returns a float, or Parameter / ParameterExpression when the
            exponent is symbolic.
            """
            e = getattr(g, "exponent", None)
            if e is None:
                raise UnsupportedGateError(f"Cirq gate {g!r} exposes no exponent.")
            if not isinstance(e, sympy.Expr):
                return pi * float(e)
            theta = sympy.simplify(sympy.pi * e)
            if not theta.free_symbols:
                return float(theta)
            syms = list(theta.free_symbols)
            if len(syms) != 1:
                raise QVMConversionError(
                    f"Symbolic Cirq angle '{theta}' involves multiple parameters; "
                    f"only single-parameter angles are supported."
                )
            sym = syms[0]
            coeff = float(theta.coeff(sym))
            const = float(theta.coeff(sym, 0))
            param = Parameter(str(sym.name))
            if const == 0.0 and coeff == 1.0:
                return param
            return ParameterExpression({param: coeff}, const)

        for op in cirq_circuit.all_operations():
            gate = op.gate
            qs = [q.x for q in op.qubits]

            if isinstance(gate, cirq.MeasurementGate):
                if len(qs) != 1:
                    raise QVMConversionError(
                        f"Multi-qubit Cirq measurement on qubits {qs} cannot map to a "
                        f"single classical target bit; measure qubits one at a time."
                    )
                reg, idx = cls._parse_measure_key(gate.key)
                circuit.add_operation("measure", qs, target_bit=(reg, idx))
                continue

            if isinstance(gate, cirq.IdentityGate):
                circuit.add_operation("id", qs)
                continue

            if isinstance(gate, cirq.CXPowGate):
                if float(gate.exponent) == 1:
                    circuit.add_operation("cx", qs)
                else:
                    raise UnsupportedGateError(
                        f"Cirq gate {gate!r} has no QVM equivalent; only CNOT is supported."
                    )
                continue

            if isinstance(gate, cirq.SwapPowGate):
                if float(gate.exponent) == 1:
                    circuit.add_operation("swap", qs)
                else:
                    raise UnsupportedGateError(
                        f"Cirq gate {gate!r} has no QVM equivalent; only SWAP is supported."
                    )
                continue

            if isinstance(gate, cirq.CCXPowGate):
                if float(gate.exponent) == 1:
                    circuit.add_operation("ccx", qs)
                else:
                    raise UnsupportedGateError(
                        f"Cirq gate {gate!r} has no QVM equivalent; only TOFFOLI is supported."
                    )
                continue

            if isinstance(gate, cirq.WaitGate):
                nanos = gate.duration.nanos
                if nanos is None:
                    raise UnsupportedGateError(
                        f"Cirq wait gate {gate!r} has no whole-nanosecond duration."
                    )
                circuit.add_operation("delay", qs, duration=f"{int(nanos)}ns")
                continue

            if isinstance(gate, cirq.XPowGate):
                ang = exp_to_angle(gate)
                if gate.global_shift == -0.5 or isinstance(ang, (Parameter, ParameterExpression)):
                    circuit.add_operation("rx", qs, params=[ang])
                elif float(gate.exponent) == 1:
                    circuit.add_operation("x", qs)
                elif float(gate.exponent) == 0.5:
                    circuit.add_operation("sx", qs)
                elif float(gate.exponent) == -0.5:
                    circuit.add_operation("sxdg", qs)
                else:
                    circuit.add_operation("rx", qs, params=[ang])
                continue

            if isinstance(gate, cirq.YPowGate):
                ang = exp_to_angle(gate)
                if gate.global_shift == -0.5 or isinstance(ang, (Parameter, ParameterExpression)):
                    circuit.add_operation("ry", qs, params=[ang])
                elif float(gate.exponent) == 1:
                    circuit.add_operation("y", qs)
                else:
                    circuit.add_operation("ry", qs, params=[ang])
                continue

            if isinstance(gate, cirq.ZPowGate):
                ang = exp_to_angle(gate)
                if gate.global_shift == -0.5 or isinstance(ang, (Parameter, ParameterExpression)):
                    circuit.add_operation("rz", qs, params=[ang])
                elif float(gate.exponent) == 1:
                    circuit.add_operation("z", qs)
                elif float(gate.exponent) == 0.25:
                    circuit.add_operation("t", qs)
                elif float(gate.exponent) == 0.5:
                    circuit.add_operation("s", qs)
                elif float(gate.exponent) == -0.25:
                    circuit.add_operation("tdg", qs)
                elif float(gate.exponent) == -0.5:
                    circuit.add_operation("sdg", qs)
                else:
                    circuit.add_operation("rz", qs, params=[ang])
                continue

            if isinstance(gate, cirq.HPowGate):
                if float(gate.exponent) == 1:
                    circuit.add_operation("h", qs)
                else:
                    raise UnsupportedGateError(
                        f"Cirq gate {gate!r} has no QVM equivalent; only H is supported."
                    )
                continue

            if isinstance(gate, cirq.XXPowGate):
                circuit.add_operation("rxx", qs, params=[exp_to_angle(gate)])
                continue
            if isinstance(gate, cirq.ZZPowGate):
                circuit.add_operation("rzz", qs, params=[exp_to_angle(gate)])
                continue
            if isinstance(gate, cirq.CZPowGate):
                ang = exp_to_angle(gate)
                if not isinstance(ang, (Parameter, ParameterExpression)) and float(gate.exponent) == 1:
                    circuit.add_operation("cz", qs)
                else:
                    circuit.add_operation("cp", qs, params=[ang])
                continue

            if isinstance(gate, cirq.ControlledGate):
                sub = gate.gate
                if gate.num_controls() == 1:
                    if isinstance(sub, cirq.XPowGate) and float(sub.exponent) == 1:
                        circuit.add_operation("cx", qs)
                        continue
                    if isinstance(sub, cirq.ZPowGate) and float(sub.exponent) == 1:
                        circuit.add_operation("cz", qs)
                        continue
                raise UnsupportedGateError(
                    f"Controlled Cirq gate {gate!r} cannot be imported into QVM IR."
                )

            raise UnsupportedGateError(
                f"Cirq gate {gate!r} cannot be imported into QVM IR. Supported gates: "
                f"H/X/Y/Z/S/T/Sdg/Tdg/SX/SXdg/I (and pow variants), rx/ry/rz/p, "
                f"CNOT/CZ/SWAP/TOFFOLI, XX/ZZ/CZ pow gates, single-qubit measurements."
            )

        return circuit

    def run_cirq_simulator(self, repetitions: int = 1024) -> dict:
        """Simulate the circuit with Cirq's built-in simulator.
        """
        if cirq is None:
            raise MissingBackendError(
                "Cirq is not installed. Install it with: "
                "pip install 'quantum-virtual-machine[cirq]'"
            )
        circuit = self.to_cirq()
        simulator = cirq.Simulator()
        result = simulator.run(circuit, repetitions=repetitions)
        # Flatten result into a simple counts dict, ordered by (register, index).
        measurements = result.measurements
        if not measurements:
            return {}
        ordered_keys = sorted(measurements.keys(), key=self._sort_measure_key)
        counts = {}
        for i in range(repetitions):
            bit_str = "".join(str(measurements[k][i][0]) for k in ordered_keys)
            counts[bit_str] = counts.get(bit_str, 0) + 1
        return counts
