# src/qvm/visual.py

"""
Visualization module for the Quantum Virtual Machine.
Provides functions to plot quantum circuits and measurement probabilities.
"""

import matplotlib.pyplot as plt
import numpy as np
from src.qvm.ir import QuantumCircuit

def plot_histogram(data, title="Quantum State Probabilities"):
    """
    Plots a histogram of measurement probabilities or counts.

    Args:
        data (np.ndarray or dict): 
            - If np.ndarray: An array of probabilities for state indices 0..N-1.
            - If dict: A dictionary mapping state labels (e.g., "00") to values.
        title (str): The title of the plot.

    Returns:
        matplotlib.figure.Figure: The generated figure object.
    """
    if isinstance(data, np.ndarray):
        # Convert probability array to dictionary with binary labels
        num_states = len(data)
        num_qubits = int(np.log2(num_states))
        
        # Filter out states with near-zero probability to keep the plot clean
        clean_data = {}
        for i, prob in enumerate(data):
            if prob > 1e-10: # Threshold for display
                # Format binary string with leading zeros
                label = f"{i:0{num_qubits}b}"
                clean_data[label] = prob
        data_to_plot = clean_data
    elif isinstance(data, dict):
        data_to_plot = data
    else:
        raise ValueError("Data must be a numpy array of probabilities or a dictionary of counts.")

    # Sort data by state label (binary string)
    sorted_keys = sorted(data_to_plot.keys())
    sorted_values = [data_to_plot[k] for k in sorted_keys]

    fig, ax = plt.subplots(figsize=(8, 6))
    bars = ax.bar(sorted_keys, sorted_values, color='cornflowerblue', edgecolor='black')

    # Add value labels on top of bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.3f}',
                ha='center', va='bottom')

    ax.set_xlabel('States')
    ax.set_ylabel('Probability / Counts')
    ax.set_title(title)
    plt.xticks(rotation=45)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()

    return fig

def plot_circuit(circuit: QuantumCircuit, title="Quantum Circuit"):
    """
    Visualizes the quantum circuit using a simple grid-based drawing.

    Args:
        circuit (QuantumCircuit): The circuit to visualize.
        title (str): Title of the plot.

    Returns:
        matplotlib.figure.Figure: The generated figure object.
    """
    if not isinstance(circuit, QuantumCircuit):
        raise TypeError("Input must be a QuantumCircuit object.")

    num_qubits = circuit.num_qubits
    ops = circuit.operations
    depth = len(ops)

    fig, ax = plt.subplots(figsize=(max(8, depth), max(4, num_qubits * 0.5)))
    
    # Grid settings
    ax.set_xlim(-1, depth + 1)
    ax.set_ylim(-1, num_qubits)
    ax.set_yticks(range(num_qubits))
    ax.set_yticklabels([f"q[{i}]" for i in range(num_qubits)])
    ax.set_xticks([]) # Hide x-axis ticks
    ax.invert_yaxis() # Qubit 0 at top

    # Draw horizontal wires
    for i in range(num_qubits):
        ax.hlines(i, -0.5, depth + 0.5, color='gray', zorder=1)

    # Draw gates
    for step, op in enumerate(ops):
        name = op['name']
        qubits = op['qubits']
        params = op.get('params', [])

        x_pos = step + 0.5 # Center gate in the time step

        if len(qubits) == 1:
            q = qubits[0]
            # Draw a box for single qubit gates
            rect = plt.Rectangle((x_pos - 0.3, q - 0.3), 0.6, 0.6, 
                                 facecolor='white', edgecolor='purple', zorder=2)
            ax.add_patch(rect)
            
            # Label the gate
            label = name.upper()
            if params:
                label += f"\n({params[0]:.2f})"
            ax.text(x_pos, q, label, ha='center', va='center', fontsize=9, zorder=3)

        elif len(qubits) == 2:
            q_ctrl, q_target = qubits[0], qubits[1]
            
            if name == "cx":
                # Control dot
                ax.plot(x_pos, q_ctrl, 'o', color='black', zorder=3)
                # Target X (circle with cross)
                ax.plot(x_pos, q_target, 'o', color='purple', markerfacecolor='white', markersize=10, zorder=2)
                ax.text(x_pos, q_target, '+', ha='center', va='center', color='purple', fontsize=12, zorder=3)
                # Connection line
                ax.vlines(x_pos, min(q_ctrl, q_target), max(q_ctrl, q_target), color='black', zorder=1)
            
            elif name == "swap":
                # Draw X on both lines
                ax.plot(x_pos, q_ctrl, 'x', color='black', markersize=8, markeredgewidth=2, zorder=3)
                ax.plot(x_pos, q_target, 'x', color='black', markersize=8, markeredgewidth=2, zorder=3)
                ax.vlines(x_pos, min(q_ctrl, q_target), max(q_ctrl, q_target), color='black', zorder=1)

    ax.set_title(title)
    return fig
