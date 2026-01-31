# tests/test_visual.py

"""
Tests for the visualization module.
"""

import pytest
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from src.qvm.visual import plot_histogram, plot_circuit
from src.qvm.ir import QuantumCircuit

# Use a non-interactive backend for testing to avoid GUI windows
matplotlib.use("Agg")

def test_plot_histogram_creates_figure():
    """Test that plot_histogram returns a matplotlib Figure."""
    probabilities = np.array([0.5, 0.0, 0.0, 0.5])
    counts = {"00": 500, "11": 500}
    
    # Test with probabilities array
    fig = plot_histogram(probabilities)
    assert isinstance(fig, plt.Figure)
    
    # Test with dictionary
    fig2 = plot_histogram(counts)
    assert isinstance(fig2, plt.Figure)
    
    # Cleanup
    plt.close(fig)
    plt.close(fig2)

def test_plot_circuit_creates_figure():
    """Test that plot_circuit returns a matplotlib Figure."""
    qc = QuantumCircuit(2)
    qc.add_operation("h", [0])
    qc.add_operation("cx", [0, 1])
    
    fig = plot_circuit(qc)
    assert isinstance(fig, plt.Figure)
    
    # Cleanup
    plt.close(fig)

def test_plot_histogram_invalid_input():
    """Test that plot_histogram raises error for invalid input."""
    with pytest.raises(ValueError):
        plot_histogram("invalid input")

def test_plot_circuit_invalid_input():
    """Test that plot_circuit raises error for invalid input."""
    with pytest.raises(TypeError):
        plot_circuit("not a circuit")
