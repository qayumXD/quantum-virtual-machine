"""superposition.py
Create a single-qubit superposition using the Hadamard (H) gate and show probabilities.
"""
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit.visualization import plot_histogram
import os

def main():
    qc = QuantumCircuit(1)
    # Put the qubit into equal superposition
    qc.h(0)

    print("Circuit:\n", qc)

    sv = Statevector.from_instruction(qc)
    probs = sv.probabilities_dict()
    print("Probabilities:", probs)

    # Try to plot/save histogram if matplotlib present
    try:
        import matplotlib
        import matplotlib.pyplot as plt
        fig = plot_histogram(probs)
        if 'agg' in matplotlib.get_backend().lower() or not os.environ.get('DISPLAY'):
            fig.savefig('superposition_histogram.png', bbox_inches='tight')
            print('Saved superposition_histogram.png')
        else:
            plt.show()
    except Exception:
        print('matplotlib not available; skipping histogram.')

if __name__ == '__main__':
    main()
