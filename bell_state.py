"""bell_state.py
Create a Bell pair using H on qubit 0 followed by CNOT(0,1).
Print circuit and the resulting probabilities for outcomes 00 and 11.
"""
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit.visualization import plot_histogram
import os

def main():
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)

    print("Circuit:\n", qc)

    sv = Statevector.from_instruction(qc)
    probs = sv.probabilities_dict()
    print("Probabilities:", probs)

    try:
        import matplotlib
        import matplotlib.pyplot as plt
        fig = plot_histogram(probs)
        if 'agg' in matplotlib.get_backend().lower() or not os.environ.get('DISPLAY'):
            fig.savefig('bell_histogram.png', bbox_inches='tight')
            print('Saved bell_histogram.png')
        else:
            plt.show()
    except Exception:
        print('matplotlib not available; skipping histogram.')

if __name__ == '__main__':
    main()
