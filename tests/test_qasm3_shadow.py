# tests/test_qasm3_shadow.py
import numpy as np
from qvm.qasm3_parser import OpenQASM3Parser
from qvm.simulator import Simulator

def test_classical_xor_parity():
    qasm = """
    OPENQASM 3.0;
    qubit[2] q;
    bit[2] c;
    bit parity;

    h q[0];
    cx q[0], q[1];

    c[0] = measure q[0];
    c[1] = measure q[1];

    parity = c[0] ^ c[1];
    
    // In a Bell state, parity is always 0
    // If we manually set parity to 1, then x q[0] would fire.
    """
    parser = OpenQASM3Parser()
    qc = parser.parse(qasm)
    sim = Simulator()
    
    for _ in range(10):
        state, mem = sim.simulate(qc)
        # c[0] and c[1] must be equal
        assert mem['c'][0] == mem['c'][1]
        # parity must be 0
        assert mem['parity'][0] == 0

def test_classical_and_logic():
    qasm = """
    OPENQASM 3.0;
    qubit[2] q;
    bit[2] c;
    bit both;

    x q[0];
    x q[1];
    c[0] = measure q[0];
    c[1] = measure q[1];

    both = c[0] & c[1];
    """
    parser = OpenQASM3Parser()
    qc = parser.parse(qasm)
    sim = Simulator()
    _, mem = sim.simulate(qc)
    assert mem['both'][0] == 1

if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
