#!/usr/bin/env python3
"""
QAOA Example: MaxCut on a Small Graph
======================================

This script demonstrates the Quantum Approximate Optimization Algorithm (QAOA)
for solving the MaxCut problem — partitioning graph nodes into two sets
to maximize the number of edges between sets.

Graph (4 nodes, 5 edges):
    0 ─── 1
    |  ╲  |
    |   ╲ |
    3 ─── 2

Maximum cut = 4 edges (e.g., partition {0,2} vs {1,3}).

Usage:
    python examples/qaoa_maxcut.py
"""

import numpy as np
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qvm.qaoa import QAOA
from qvm.simulator import Simulator


def main():
    print("=" * 60)
    print("  QAOA: MaxCut on a 4-Node Graph")
    print("=" * 60)
    print()

    # Define the graph
    edges = [(0, 1), (1, 2), (2, 3), (0, 3), (0, 2)]
    num_qubits = 4

    print("  Graph edges:", edges)
    print(f"  Nodes: {num_qubits}, Edges: {len(edges)}")
    print()

    # Find the true optimal MaxCut by brute force
    best_cut = 0
    best_partition = ""
    for i in range(2 ** num_qubits):
        bs = format(i, f"0{num_qubits}b")
        cost = QAOA.maxcut_cost(bs, edges)
        if cost > best_cut:
            best_cut = cost
            best_partition = bs

    print(f"  Exact MaxCut value: {best_cut}")
    print(f"  Optimal partition:  |{best_partition}⟩")
    print()

    # Build the cost Hamiltonian
    cost_hamiltonian = QAOA.maxcut_hamiltonian(edges, num_qubits)
    sim = Simulator()

    # ---- 1-layer QAOA ----
    print("  " + "─" * 40)
    print("  Running 1-layer QAOA...")
    print("  " + "─" * 40)
    qaoa_1 = QAOA(
        cost_hamiltonian=cost_hamiltonian,
        num_layers=1,
        simulator=sim,
    )
    result_1 = qaoa_1.run(
        max_iterations=100,
        shots=1024,
    )

    cut_1 = QAOA.maxcut_cost(result_1.best_bitstring, edges)
    print(f"  Best bitstring: |{result_1.best_bitstring}⟩")
    print(f"  MaxCut value:   {cut_1} / {best_cut}")
    print(f"  Optimal γ:      {result_1.optimal_gamma}")
    print(f"  Optimal β:      {result_1.optimal_beta}")
    print(f"  Circuit evals:  {result_1.num_circuit_evaluations}")
    print()

    # Show top measurement outcomes
    print("  Top measurement outcomes:")
    sorted_counts = sorted(result_1.measurement_counts.items(),
                           key=lambda x: x[1], reverse=True)
    for bs, count in sorted_counts[:5]:
        mc = QAOA.maxcut_cost(bs, edges)
        pct = count / 1024 * 100
        print(f"    |{bs}⟩  count={count:4d} ({pct:5.1f}%)  cut={mc}")
    print()

    # ---- 2-layer QAOA ----
    print("  " + "─" * 40)
    print("  Running 2-layer QAOA...")
    print("  " + "─" * 40)
    qaoa_2 = QAOA(
        cost_hamiltonian=cost_hamiltonian,
        num_layers=2,
        simulator=sim,
    )
    result_2 = qaoa_2.run(
        max_iterations=150,
        shots=1024,
    )

    cut_2 = QAOA.maxcut_cost(result_2.best_bitstring, edges)
    print(f"  Best bitstring: |{result_2.best_bitstring}⟩")
    print(f"  MaxCut value:   {cut_2} / {best_cut}")
    print(f"  Optimal γ:      {result_2.optimal_gamma}")
    print(f"  Optimal β:      {result_2.optimal_beta}")
    print(f"  Circuit evals:  {result_2.num_circuit_evaluations}")
    print()

    print("  " + "─" * 40)
    print(f"  Summary: 1-layer cut={cut_1}, 2-layer cut={cut_2}, exact={best_cut}")
    print("  " + "─" * 40)
    print()
    print("=" * 60)
    print("  Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
