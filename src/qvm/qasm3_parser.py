# src/qvm/qasm3_parser.py
from lark import Lark, Tree, Token
import os
import numpy as np
from src.qvm.ir import QuantumCircuit

class OpenQASM3Parser:
    def __init__(self):
        grammar_path = os.path.join(os.path.dirname(__file__), "qasm3.lark")
        with open(grammar_path, "r") as f:
            self.grammar = f.read()
        self.parser = Lark(self.grammar, start="start", parser="lalr")
        self._label_counter = 0
        self.qc = None
        self.qubit_map = {}
        self.next_qubit_idx = 0

    def parse(self, text: str) -> QuantumCircuit:
        tree = self.parser.parse(text)
        self.qc = None
        self.qubit_map = {}
        self.next_qubit_idx = 0
        self._label_counter = 0
        
        # 1. First pass: Declarations
        self._find_declarations(tree)
        
        # 2. Second pass: Operations
        self._process_node(tree, None)
        return self.qc

    def _find_declarations(self, node):
        if not isinstance(node, Tree): return
        if node.data == "qubit_decl":
            size, name = int(node.children[0]), str(node.children[1])
            self.qubit_map[name] = (self.next_qubit_idx, size)
            self.next_qubit_idx += size
            if self.qc is None: self.qc = QuantumCircuit(self.next_qubit_idx)
            else: self.qc.num_qubits = self.next_qubit_idx
        elif node.data == "bit_decl":
            if self.qc: self.qc.add_classical_register(str(node.children[1]), int(node.children[0]))
        elif node.data == "bit_single_decl":
            if self.qc: self.qc.add_classical_register(str(node.children[0]), 1)
        
        for child in node.children:
            self._find_declarations(child)

    def _evaluate(self, node):
        """Recursively evaluates atomic expressions (qubits, bit_idxs, boolean logic)."""
        if isinstance(node, Token):
            if node.type == "INT": return int(node)
            if node.type == "NUMBER": return float(node)
            if node.type == "CNAME": return str(node)
            return node
        
        if not isinstance(node, Tree): return node
        
        if node.data == "qubit":
            name, idx = str(node.children[0]), int(node.children[1])
            return self.qubit_map[name][0] + idx
        elif node.data == "qubit_list":
            return [self._evaluate(c) for c in node.children]
        elif node.data == "bit_idx":
            return (str(node.children[0]), int(node.children[1]))
        elif node.data == "bit_name":
            return (str(node.children[0]), 0)
        elif node.data == "and_expr":
            return {"op": "&", "args": [self._evaluate(c) for c in node.children]}
        elif node.data == "or_expr":
            return {"op": "|", "args": [self._evaluate(c) for c in node.children]}
        elif node.data == "xor_expr":
            return {"op": "^", "args": [self._evaluate(c) for c in node.children]}
        elif node.data == "not_expr":
            return {"op": "~", "args": [self._evaluate(c) for c in node.children]}
        elif node.data == "cond_indexed":
            return {"register": str(node.children[0]), "index": int(node.children[1]), "value": int(node.children[2])}
        elif node.data == "cond_simple":
            return {"register": str(node.children[0]), "index": 0, "value": int(node.children[1])}
        elif node.data == "arguments":
            return [self._evaluate(c) for c in node.children]
        elif node.data == "duration":
            return f"{node.children[0]}{node.children[1]}"
        
        # Default recursive evaluation
        res = [self._evaluate(c) for c in node.children]
        return res[0] if len(res) == 1 else res

    def _process_node(self, node, current_condition):
        if not isinstance(node, Tree): return

        if node.data == "gate_call":
            name = str(node.children[0])
            params = self._evaluate(node.children[1]) if node.children[1] else []
            qubits = self._evaluate(node.children[2])
            self.qc.add_operation(name, qubits=qubits, params=params, condition=current_condition)
            return
        
        elif node.data == "measurement":
            target = self._evaluate(node.children[0])
            q_phys = self._evaluate(node.children[1])
            self.qc.add_operation("measure", qubits=[q_phys], target_bit=target, condition=current_condition)
            return
            
        elif node.data == "assignment":
            target = self._evaluate(node.children[0])
            expr = self._evaluate(node.children[1])
            if isinstance(expr, (tuple, int)):
                cop = {"op": "=", "target": target, "args": [expr]}
            else:
                cop = {"op": expr["op"], "target": target, "args": expr["args"]}
            self.qc.add_operation("classical_op", qubits=[], classical_op=cop, condition=current_condition)
            return

        elif node.data == "if_statement":
            condition = self._evaluate(node.children[0])
            program_block = node.children[1]
            for stmt in program_block.children:
                self._process_node(stmt, condition)
            return
        
        elif node.data == "for_loop":
            start_val = int(node.children[1].children[0])
            end_val = int(node.children[1].children[1])
            program_block = node.children[2]
            for _ in range(start_val, end_val):
                for stmt in program_block.children:
                    self._process_node(stmt, current_condition)
            return
        
        elif node.data == "while_loop":
            condition = self._evaluate(node.children[0])
            program_block = node.children[1]
            label_id = self._label_counter
            self._label_counter += 1
            start_label = f"while_start_{label_id}"
            self.qc.add_operation("label", [], label=start_label)
            for stmt in program_block.children:
                self._process_node(stmt, current_condition)
            self.qc.add_operation("jump", [], condition=condition, jump_to=start_label)
            return
        
        elif node.data == "delay_call":
            dur = self._evaluate(node.children[0])
            qubits = self._evaluate(node.children[1])
            self.qc.add_operation("delay", qubits=qubits, duration=dur, condition=current_condition)
            return

        else:
            for child in node.children:
                self._process_node(child, current_condition)

if __name__ == "__main__":
    qasm_text = """
    OPENQASM 3.0;
    qubit[2] q;
    bit[2] c;
    h q[0];
    c[0] = measure q[0];
    if (c[0] == 1) {
        x q[1];
    }
    """
    parser = OpenQASM3Parser()
    qc = parser.parse(qasm_text)
    print(qc)
