"""ghz_state.py
Create a 3-qubit GHZ state: apply H on qubit 0 then CNOT(0,1) and CNOT(0,2).
Show circuit and probabilities (should have 000 and 111 with equal weight).
"""
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit.visualization import plot_histogram
import os

def main():
    qc = QuantumCircuit(3)
    qc.h(0)
    qc.cx(0, 1)
    qc.cx(0, 2)

    print("Circuit:\n", qc)

    sv = Statevector.from_instruction(qc)
    probs = sv.probabilities_dict()
    print("Probabilities:", probs)

    try:
        import matplotlib
        import matplotlib.pyplot as plt
        fig = plot_histogram(probs)
        if 'agg' in matplotlib.get_backend().lower() or not os.environ.get('DISPLAY'):
            fig.savefig('ghz_histogram.png', bbox_inches='tight')
            print('Saved ghz_histogram.png')
        else:
            plt.show()
    except Exception:
        print('matplotlib not available; skipping histogram.')

if __name__ == '__main__':
    main()
