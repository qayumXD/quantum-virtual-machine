---
tags: [noise, kraus-operators, monte-carlo, thermal-relaxation, hardware-profiles, simulation]
---
# 🌡️ Quantum Noise and Hardware Profiles

Physical quantum computers suffer from decoherence and gate errors. The QVM provides a noise simulation system in [noise.py](https://github.com/qayumXD/quantum-virtual-machine/blob/main/src/qvm/noise.py), modeling physical noise channels using Kraus operators and stochastic trajectories.

---

## 📐 Mathematical Model: Kraus Channels and Trajectories

Quantum noise is mathematically described using open quantum system dynamics. A noise channel mapping an density matrix $\rho$ is defined by a set of Kraus operators $\{K_i\}$ satisfying the completeness relation:
$$ \rho \to \sum_i K_i \rho K_i^\dagger, \quad \text{with} \quad \sum_i K_i^\dagger K_i = I $$

### The Stochastic Trajectory Method (Monte Carlo)
To simulate noise efficiently on statevectors without converting to density matrices (which would scale as $O(4^N)$), QVM uses the **stochastic trajectory method**:

1.  When a noisy gate is applied, the simulator computes the probability $p_i$ of each Kraus operator $K_i$ occurring on the current state $|\psi\rangle$:
    $$ p_i = \| K_i |\psi\rangle \|^2 = \langle\psi| K_i^\dagger K_i |\psi\rangle $$
2.  Samples a single Kraus operator $K_j$ based on these probabilities $\{p_i\}$.
3.  Applies the sampled operator and re-normalizes the statevector:
    $$ |\psi_{\text{new}}\rangle = \frac{K_j |\psi\rangle}{\sqrt{p_j}} $$

This reproduces the density matrix statistics when averaged over many shots, while keeping simulation scaling at $O(2^N)$.

---

## 🧪 Supported Noise Channels

### 1. Depolarizing Noise
Replaces the qubit state with a maximally mixed state with probability $p$.
*   **Single-Qubit Kraus Operators**:
    $$ K_0 = \sqrt{1 - \frac{3p}{4}} I, \quad K_1 = \sqrt{\frac{p}{4}} X, \quad K_2 = \sqrt{\frac{p}{4}} Y, \quad K_3 = \sqrt{\frac{p}{4}} Z $$
*   **Two-Qubit Kraus Operators**: Scales the $16$ two-qubit tensor product combinations of Pauli operators:
    $$ K_0 = \sqrt{1 - \frac{15p}{16}} II, \quad K_k = \sqrt{\frac{p}{16}} P_a \otimes P_b \quad (P_a, P_b \in \{I, X, Y, Z\}) $$

---

### 2. Amplitude Damping (T1 Decay)
Models energy relaxation (spontaneous emission) where state $|1\rangle$ decays to state $|0\rangle$ with probability $\gamma$:
$$ K_0 = \begin{pmatrix} 1 & 0 \\ 0 & \sqrt{1 - \gamma} \end{pmatrix}, \quad K_1 = \begin{pmatrix} 0 & \sqrt{\gamma} \\ 0 & 0 \end{pmatrix} $$

---

### 3. Phase Damping (T2 Dephasing)
Models pure dephasing (loss of phase coherence without energy loss) with probability $\gamma$:
$$ K_0 = \begin{pmatrix} 1 & 0 \\ 0 & \sqrt{1 - \gamma} \end{pmatrix}, \quad K_1 = \begin{pmatrix} 0 & 0 \\ 0 & \sqrt{\gamma} \end{pmatrix} $$

---

### 4. Thermal Relaxation
Combines $T_1$ relaxation and $T_2$ dephasing over a specific gate duration $t_g$.
*   **Decay Probabilities**:
    $$ p_{\text{amplitude}} = 1 - e^{-t_g / T_1}, \quad p_{\text{phase}} = 1 - e^{-t_g / T_2} $$
*   **Residual Phase Calculation**: To combine these channels, the simulator computes a residual phase damping probability to account for dephasing already caused by the amplitude damping:
    $$ p_{\text{phase\_residual}} = \max\left(0, 1 - \frac{1 - p_{\text{phase}}}{\sqrt{1 - p_{\text{amplitude}}}}\right) $$
*   **Kraus Operators**: Built by composing the amplitude damping and residual phase damping operators, resulting in $4$ combined Kraus operators.

---

## 📊 Readout Error Models (Confusion Matrix)

Readout error models the probability of classical measurement bits flipping. It is defined using a $2 \times 2$ confusion matrix $M$:
$$ M_{ij} = P(\text{measure } j \mid \text{true state is } i) $$
$$ M = \begin{pmatrix} P(0|0) & P(1|0) \\ P(0|1) & P(1|1) \end{pmatrix} $$

During measurement sampling, the simulator evaluates the true state of each qubit and stochastically flips the output bit based on the confusion matrix:
```python
true_bit = int(bits_list[i])
# Sample from confusion matrix row
flip_prob = cm[true_bit, 1 - true_bit]
if rng.random() < flip_prob:
    bits_list[i] = str(1 - true_bit)
```

---

## 🖥️ Predefined Device Profiles

The `DeviceBackend` class loads calibration data (T1, T2, gate times, single/two-qubit gate errors, and readout errors) to generate realistic noise models:

*   **`fake_5q_device()` (IBM Manila)**:
    *   $5$ qubits in a linear chain: $0-1-2-3-4$.
    *   $T_1 \approx 100\,\mu\text{s}$, $T_2 \approx 80\,\mu\text{s}$.
    *   Gate errors: $0.1\%$ for single-qubit gates, $1\%$ for CNOTs.
    *   Readout errors: $\approx 2\%$.
*   **`fake_7q_device()` (IBM Lagos)**:
    *   $7$ qubits in a T-shape.
    *   $T_1 \approx 100\,\mu\text{s}$, $T_2 \approx 80\,\mu\text{s}$.
    *   Gate errors: $0.08\%$ for single-qubit gates, $1.2\%$ for CNOTs.
*   **`ideal()`**: Zero-noise baseline for testing.
