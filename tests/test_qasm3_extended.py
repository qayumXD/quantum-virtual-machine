# tests/test_qasm3_extended.py
import numpy as np
from src.qvm.qasm3_parser import OpenQASM3Parser
from src.qvm.simulator import Simulator

def test_sx_gate():
    qasm = """
    OPENQASM 3.0;
    qubit[1] q;
    sx q[0];
    """
    parser = OpenQASM3Parser()
    qc = parser.parse(qasm)
    sim = Simulator()
    state, _ = sim.simulate(qc)
    # SX gate results in 0.5+0.5j for |0> and 0.5-0.5j for |1> (probabilities 0.5 each)
    probs = np.abs(state)**2
    assert np.allclose(probs, [0.5, 0.5])

def test_ccx_gate():
    qasm = """
    OPENQASM 3.0;
    qubit[3] q;
    x q[0];
    x q[1];
    ccx q[0], q[1], q[2];
    """
    parser = OpenQASM3Parser()
    qc = parser.parse(qasm)
    sim = Simulator()
    state, _ = sim.simulate(qc)
    # |110> -> |111>
    # Index 7 (111 in binary) should be 1.0
    probs = np.abs(state)**2
    assert np.allclose(probs[7], 1.0)

def test_delay_parsing():
    qasm = """
    OPENQASM 3.0;
    qubit[1] q;
    delay[100ns] q[0];
    """
    parser = OpenQASM3Parser()
    qc = parser.parse(qasm)
    assert qc.operations[0]["name"] == "delay"
    assert qc.operations[0]["duration"] == "100ns"

def test_conditional_active_feedback():
    # Verify our "Active Feedback" once more
    qasm = """
    OPENQASM 3.0;
    qubit[2] q;
    bit[1] c;
    h q[0];
    c[0] = measure q[0];
    if (c[0] == 1) {
        x q[1];
    }
    """
    parser = OpenQASM3Parser()
    qc = parser.parse(qasm)
    sim = Simulator()
    
    # We run multiple times to hit both branches
    results = []
    for _ in range(20):
        state, mem = sim.simulate(qc)
        if mem['c'][0] == 1:
            # Should be |11> (index 3)
            assert np.isclose(np.abs(state[3])**2, 1.0)
        else:
            # Should be |00> (index 0)
            assert np.isclose(np.abs(state[0])**2, 1.0)
        results.append(mem['c'][0])
    
    assert 0 in results and 1 in results # Statistical check

if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
