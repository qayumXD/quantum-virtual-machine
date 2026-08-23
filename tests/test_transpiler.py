# tests/test_transpiler.py

import pytest
from qvm.ir import QuantumCircuit
from qvm.parser import QASMParser
from qvm.architecture import get_linear_architecture
from qvm.transpiler import Transpiler
from qvm.simulator import Simulator
import numpy as np

def test_transpile_on_connected_arch():
    """Tests transpilation on a fully connected architecture where no SWAPs are needed."""
    circuit_desc = [
        {"name": "h", "qubits": [0]},
        {"name": "cx", "qubits": [0, 2]}
    ]
    logical_qc = QASMParser.parse(circuit_desc, 3)
    
    # On a fully connected architecture, the physical circuit should be identical
    from qvm.architecture import get_fully_connected_architecture
    arch = get_fully_connected_architecture(3)
    transpiler = Transpiler(arch)
    physical_qc = transpiler.transpile(logical_qc)
    
    assert len(physical_qc.operations) == 2
    assert physical_qc.operations[0]["name"] == "h"
    assert physical_qc.operations[1]["name"] == "cx"
    assert physical_qc.operations[1]["qubits"] == [0, 2]

def test_transpile_with_swap_insertion():
    """Tests that the transpiler correctly inserts a SWAP gate."""
    # CNOT(0, 2) on a 3-qubit linear chain 0-1-2 requires a SWAP
    circuit_desc = [
        {"name": "cx", "qubits": [0, 2]}
    ]
    logical_qc = QASMParser.parse(circuit_desc, 3)
    
    arch = get_linear_architecture(3) # Connectivity: {(0, 1), (1, 2)}
    transpiler = Transpiler(arch)
    physical_qc = transpiler.transpile(logical_qc)
    
    # Expected output: SWAP(0,1), CNOT(1,2) (if we move logical 0 to physical 1)
    # or SWAP(1,2), CNOT(0,1) (if we move logical 2 to physical 1)
    # Our BFS-based implementation will choose one path. Let's trace it:
    # Path from 0 to 2 is [0, 1, 2]. Loop runs for len-2 = 1 time.
    # Swaps path[0] (0) and path[1] (1).
    # So we expect: SWAP(0, 1), then CNOT on the new positions.
    # After SWAP(0,1): logical 0 is on physical 1, logical 1 is on physical 0.
    # The CNOT's logical qubits are 0 and 2.
    # Logical 0 is now on physical 1.
    # Logical 2 is still on physical 2.
    # So the CNOT should be on physical qubits [1, 2].
    
    op_names = [op["name"] for op in physical_qc.operations]
    # With swap-back enabled we expect swap, cx, swap
    assert op_names == ["swap", "cx", "swap"]
    
    assert physical_qc.operations[0]["qubits"] == [0, 1]
    assert physical_qc.operations[1]["qubits"] == [1, 2]
    assert physical_qc.operations[2]["qubits"] == [0, 1]

def test_transpile_no_path():
    """Tests that the transpiler raises an error if no path exists."""
    circuit_desc = [{"name": "cx", "qubits": [0, 3]}]
    logical_qc = QASMParser.parse(circuit_desc, 4)
    
    # A disconnected architecture
    from qvm.architecture import TargetArchitecture
    arch = TargetArchitecture("Disconnected-4", 4, {(0, 1), (2, 3)}, {"cx"})
    transpiler = Transpiler(arch)
    
    with pytest.raises(RuntimeError, match="No path between qubits"):
        transpiler.transpile(logical_qc)


def test_transpilation_is_logically_correct():
    """
    Tests that the transpiled circuit is logically equivalent to the original
    by comparing the final statevectors of both. This is the ultimate test of correctness.
    """
    # 1. Define the scenario
    logical_circuit_desc = [
        {"name": "h", "qubits": [0]},
        {"name": "cx", "qubits": [0, 2]}
    ]
    logical_qc = QASMParser.parse(logical_circuit_desc, 3)
    arch = get_linear_architecture(3)
    simulator = Simulator()

    # 2. Get the expected statevector by simulating the LOGICAL circuit
    # The simulator doesn't care about connectivity, so this gives the "correct" answer.
    expected_state, _ = simulator.simulate(logical_qc)

    # 3. Get the actual statevector by transpiling and then simulating the PHYSICAL circuit
    transpiler = Transpiler(arch)
    physical_qc = transpiler.transpile(logical_qc)
    actual_state, _ = simulator.simulate(physical_qc)

    # 4. Assert that the results are the same (up to floating point tolerance)
    # This test will FAIL with the current transpiler implementation, proving the bug.
    assert np.allclose(expected_state, actual_state)


def test_sabre_reduces_swaps_for_repeated_far_gates():
    """
    SABRE strategy with restore_mapping=False should reuse routing and emit fewer swaps
    for consecutive distant gates.
    """
    circuit_desc = [
        {"name": "cx", "qubits": [0, 2]},
        {"name": "cx", "qubits": [0, 2]},
    ]
    logical_qc = QASMParser.parse(circuit_desc, 3)
    arch = get_linear_architecture(3)

    greedy = Transpiler(arch, strategy="greedy", restore_mapping=True).transpile(logical_qc)
    sabre = Transpiler(arch, strategy="sabre", restore_mapping=False).transpile(logical_qc)

    greedy_swaps = sum(1 for op in greedy.operations if op["name"] == "swap")
    sabre_swaps = sum(1 for op in sabre.operations if op["name"] == "swap")

    assert sabre_swaps < greedy_swaps
    # sanity: sabre should produce expected concise sequence swap, cx, cx
    assert [op["name"] for op in sabre.operations][0] == "swap"
