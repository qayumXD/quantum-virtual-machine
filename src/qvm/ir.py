# src/qvm/ir.py

"""
Intermediate Representation (IR) for Quantum Circuits.
Extends the IR to support OpenQASM 3.0 classical registers and conditional operations.
"""

from typing import List, Dict, Optional, Any

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
            # Basic gate registry – extend as needed.
            GATE_SPEC = {
                "h": 0, "x": 0, "y": 0, "z": 0,
                "cx": 0, "cz": 0, "swap": 0, "ccx": 0, "toffoli": 0,
                "id": 0, "sx": 0, "sxdg": 0, "s": 0, "sdg": 0, "t": 0, "tdg": 0,
                "rx": 1, "ry": 1, "rz": 1, "p": 1,
                "measure": 0,
            }
            if not isinstance(qubits, list) or not all(isinstance(q, int) for q in qubits):
                raise ValueError(f"Qubits must be a list of integers. Got: {qubits}")
            
            if gate_name not in GATE_SPEC:
                raise ValueError(f"Unsupported gate '{gate_name}'. Add it to GATE_SPEC if needed.")
            
            if params is not None and not isinstance(params, list):
                raise ValueError("Parameters must be a list or None.")

            expected_params = GATE_SPEC[gate_name]
            actual_params = len(params) if params else 0
            if actual_params != expected_params:
                raise ValueError(f"Gate '{gate_name}' expects {expected_params} parameters, got {actual_params}.")
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
        from src.qvm.qasm3_parser import OpenQASM3Parser
        parser = OpenQASM3Parser()
        return parser.parse(qasm_str)

    @classmethod
    def qiskit_to_cirq(cls, qiskit_circuit: "QiskitCircuit") -> "cirq.Circuit":
        qc = cls.from_qiskit(qiskit_circuit)
        return qc.to_cirq()

    @classmethod
    def cirq_to_qiskit(cls, cirq_circuit: "cirq.Circuit") -> "QiskitCircuit":
        qc = cls.from_cirq(cirq_circuit)
        return qc.to_qiskit()

    def to_qiskit(self) -> "QiskitCircuit | None":
        """Convert this IR to a Qiskit :class:`QuantumCircuit`.

        Returns ``None`` if Qiskit is not installed.
        """
        if qiskit is None:
            return None
        from qiskit import QuantumRegister, ClassicalRegister
        qr = QuantumRegister(self.num_qubits, "q")
        cregs = [ClassicalRegister(size, name) for name, size in self.classical_registers.items()]
        qc = QiskitCircuit(qr, *cregs)
        for op in self.operations:
            name = op["name"]
            qubits = op["qubits"]
            params = op["params"]
            if name == "h":
                qc.h(qubits[0])
            elif name == "x":
                qc.x(qubits[0])
            elif name == "cx":
                qc.cx(qubits[0], qubits[1])
            elif name == "measure":
                cr, idx = op["target_bit"]
                for creg in cregs:
                    if creg.name == cr:
                        qc.measure(qr[qubits[0]], creg[idx])
                        break
            # Extend with more gates as needed.
        return qc

    @classmethod
    def from_qiskit(cls, qiskit_circuit: "QiskitCircuit") -> "QuantumCircuit":
        """Create a :class:`QuantumCircuit` from a Qiskit circuit.

        Classical registers are inferred from the Qiskit circuit's classical bits.
        """
        if qiskit is None:
            raise ImportError("Qiskit is not installed")
        num_qubits = qiskit_circuit.num_qubits
        circuit = cls(num_qubits)
        # Extract classical registers (simple flat mapping)
        for i, creg in enumerate(qiskit_circuit.cregs):
            circuit.add_classical_register(creg.name, creg.size)
        for instruction in qiskit_circuit.data:
            name = instruction.operation.name
            qubits = [qiskit_circuit.find_bit(qb).index for qb in instruction.qubits]
            cargs = instruction.clbits
            params = list(instruction.operation.params) if instruction.operation.params else None
            if name == "measure" and cargs:
                cb = cargs[0]
                regs = qiskit_circuit.find_bit(cb).registers
                if regs:
                    reg, idx = regs[0]
                    target_bit = (reg.name, idx)
                else:
                    target_bit = ("c", qiskit_circuit.find_bit(cb).index)
                circuit.add_operation(name, qubits, params=params, target_bit=target_bit)
            else:
                circuit.add_operation(name, qubits, params=params)
        return circuit

    def run_qiskit_simulator(self, shots: int = 1024) -> dict:
        """Execute the circuit on Qiskit's Aer simulator and return measurement counts.
        """
        if AerSimulator is None:
            raise RuntimeError("Qiskit Aer simulator is not available")
        qc = self.to_qiskit()
        if qc is None:
            raise RuntimeError("Failed to convert circuit to Qiskit")
        sim = AerSimulator()
        result = sim.run(qc, shots=shots).result()
        return result.get_counts()

    # ---------------------------------------------------------------------
    # Cirq integration helpers
    # ---------------------------------------------------------------------
    def to_cirq(self) -> "cirq.Circuit | None":
        """Convert this IR to a Cirq :class:`Circuit`.

        Returns ``None`` if Cirq is not installed.
        """
        if cirq is None:
            return None
        circuit = cirq.Circuit()
        qubit_map = {i: cirq.LineQubit(i) for i in range(self.num_qubits)}
        for op in self.operations:
            name = op["name"]
            qs = [qubit_map[i] for i in op["qubits"]]
            if name == "h":
                circuit.append(cirq.H(qs[0]))
            elif name == "x":
                circuit.append(cirq.X(qs[0]))
            elif name == "cx":
                circuit.append(cirq.CNOT(qs[0], qs[1]))
            elif name == "measure":
                target = op["target_bit"]
                # Simple flat register mapping: one classical bit per qubit
                circuit.append(cirq.measure(qs[0], key=str(target)))
            # Add more gates as needed.
        return circuit

    @classmethod
    def from_cirq(cls, cirq_circuit: "cirq.Circuit") -> "QuantumCircuit":
        """Create a :class:`QuantumCircuit` from a Cirq circuit.
        """
        if cirq is None:
            raise ImportError("Cirq is not installed")
        # Determine the highest qubit index used.
        max_index = max(q.x for op in cirq_circuit.all_operations() for q in op.qubits)
        circuit = cls(max_index + 1)
        for op in cirq_circuit.all_operations():
            if op.gate == cirq.H:
                circuit.add_operation("h", [op.qubits[0].x])
            elif op.gate == cirq.X:
                circuit.add_operation("x", [op.qubits[0].x])
            elif op.gate == cirq.CNOT:
                circuit.add_operation("cx", [op.qubits[0].x, op.qubits[1].x])
            elif isinstance(op.gate, cirq.MeasurementGate):
                key = op.gate.key
                creg = "c"
                idx = 0
                if key.startswith("(") and key.endswith(")"):
                    try:
                        inner = key[1:-1].split(",")
                        creg = inner[0].strip("' ")
                        idx = int(inner[1])
                    except:
                        pass
                circuit.add_operation("measure", [op.qubits[0].x], target_bit=(creg, idx))
            # Extend for additional gates as needed.
            
        cregs_needed = {}
        for op in circuit.operations:
            if op["name"] == "measure":
                cr, idx = op["target_bit"]
                cregs_needed[cr] = max(cregs_needed.get(cr, 0), idx + 1)
        for cr, size in cregs_needed.items():
            circuit.add_classical_register(cr, size)
            
        return circuit

    def run_cirq_simulator(self, repetitions: int = 1024) -> dict:
        """Simulate the circuit with Cirq's built‑in simulator.
        """
        if cirq is None:
            raise RuntimeError("Cirq is not installed")
        circuit = self.to_cirq()
        if circuit is None:
            raise RuntimeError("Failed to convert circuit to Cirq")
        simulator = cirq.Simulator()
        result = simulator.run(circuit, repetitions=repetitions)
        # Flatten result into a simple counts dict.
        measurements = result.measurements
        if not measurements:
            return {}
        keys = sorted(measurements.keys())
        counts = {}
        for i in range(repetitions):
            bit_str = "".join(str(measurements[k][i][0]) for k in keys)
            counts[bit_str] = counts.get(bit_str, 0) + 1
        return counts
