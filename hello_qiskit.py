from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit.visualization import plot_histogram
import os
try:
	import matplotlib
	import matplotlib.pyplot as plt
	_HAS_MATPLOTLIB = True
	_MPL_BACKEND = matplotlib.get_backend()
except Exception:
	_HAS_MATPLOTLIB = False
	_MPL_BACKEND = None

# 1. Create a Quantum Circuit
# A circuit with 2 quantum bits (qubits)
qc = QuantumCircuit(2)

# 2. Add Gates to Create a Bell State (Entanglement)
# Add a Hadamard gate on the first qubit to create a superposition
qc.h(0)
# Add a CNOT gate to entangle the two qubits
qc.cx(0, 1)

# Note: StatevectorSampler works with circuits without final measurement operations.
# We'll not add explicit measurements so the sampler can return a statevector-based
# quasi-distribution of outcomes.

# Print the circuit to visualize it
print("Quantum Circuit:")
print(qc)

# 4. Simulate the Circuit using the Statevector (no Aer required)
# Compute the statevector and extract probabilities directly. This avoids
# depending on qiskit-aer or a Sampler primitive that's not available in
# the installed qiskit version.
sv = Statevector.from_instruction(qc)
probs = sv.probabilities_dict()
print("\nSimulation Results (Probabilities):")
print(probs)

# For a visual representation, you can plot a histogram (if matplotlib present)
print("\nPlotting histogram...")
if _HAS_MATPLOTLIB:
	fig = plot_histogram(probs)
	# If backend is non-interactive (Agg) or no DISPLAY, save to file instead of showing
	is_non_interactive = (_MPL_BACKEND and 'agg' in _MPL_BACKEND.lower()) or (not os.environ.get('DISPLAY'))
	try:
		if is_non_interactive:
			# try to save from figure object returned by plot_histogram
			if hasattr(fig, 'savefig'):
				fig.savefig('histogram.png', bbox_inches='tight')
				print("Saved histogram to histogram.png (non-interactive backend).")
			elif hasattr(fig, 'figure') and hasattr(fig.figure, 'savefig'):
				fig.figure.savefig('histogram.png', bbox_inches='tight')
				print("Saved histogram to histogram.png (non-interactive backend).")
			else:
				plt.savefig('histogram.png', bbox_inches='tight')
				print("Saved histogram to histogram.png (non-interactive backend).")
		else:
			plt.show()
	except Exception as e:
		# fallback: attempt to save using pyplot
		try:
			plt.savefig('histogram.png', bbox_inches='tight')
			print("Saved histogram to histogram.png (fallback due to error).")
		except Exception as e2:
			print("Could not show or save histogram:", e, e2)
else:
	print("matplotlib not installed; skipping histogram display.")
print(qc)