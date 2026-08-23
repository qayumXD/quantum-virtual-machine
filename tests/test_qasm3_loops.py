# tests/test_qasm3_loops.py
import numpy as np
from qvm.qasm3_parser import OpenQASM3Parser
from qvm.simulator import Simulator

def test_for_loop_unrolling():
    # SX^4 is Identity (up to global phase)
    # SX results in sqrt(X). SX^2 = X. SX^4 = I.
    qasm = """
    OPENQASM 3.0;
    qubit[1] q;
    for i in [0:4] {
        sx q[0];
    }
    """
    parser = OpenQASM3Parser()
    qc = parser.parse(qasm)
    # Check if operations were unrolled
    assert len(qc.operations) == 4
    
    sim = Simulator()
    state, _ = sim.simulate(qc)
    probs = np.abs(state)**2
    # Should be back to |0>
    assert np.allclose(probs, [1.0, 0.0])

def test_while_loop_dynamic():
    # Loop until q[0] is measured as 1
    # This is a classic "repeat-until-success" pattern
    qasm = """
    OPENQASM 3.0;
    qubit[1] q;
    bit[1] c;
    
    // Initial state is 0, c[0] is 0
    h q[0];
    c[0] = measure q[0];
    
    // While c[0] == 0, keep trying
    while(c[0] == 0) {
        h q[0];
        c[0] = measure q[0];
    }
    """
    parser = OpenQASM3Parser()
    qc = parser.parse(qasm)
    
    sim = Simulator()
    state, mem = sim.simulate(qc, seed=42)
    
    # After the loop, c[0] MUST be 1
    assert mem['c'][0] == 1
    # And q[0] must be in state |1> (index 1)
    probs = np.abs(state)**2
    assert np.isclose(probs[1], 1.0)

def test_nested_loops():
    qasm = """
    OPENQASM 3.0;
    qubit[1] q;
    for i in [0:2] {
        for j in [0:2] {
            x q[0];
        }
    }
    """
    # Total 4 X gates = Identity
    parser = OpenQASM3Parser()
    qc = parser.parse(qasm)
    assert len(qc.operations) == 4
    sim = Simulator()
    state, _ = sim.simulate(qc)
    assert np.isclose(np.abs(state[0])**2, 1.0)

if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
