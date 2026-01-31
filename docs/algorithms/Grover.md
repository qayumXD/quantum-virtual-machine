# Grover's Search Algorithm

Grover's Algorithm provides a quadratic speedup for searching an unsorted database. Given a search space of size $N=2^n$, it finds a marked item in $O(\sqrt{N})$ steps.

## The Circuit
The algorithm consists of two parts repeated for $\approx \frac{\pi}{4}\sqrt{N}$ iterations:

1.  **Oracle ($U_f$):** Marks the target state $|w\rangle$ by flipping its phase.
    $$ |x\rangle \to (-1)^{f(x)} |x\rangle $$
    where $f(w)=1$ and $f(x)=0$ otherwise.
    In our implementation, we construct this using a Multi-Controlled Z gate (MCZ), sandwiched by X gates if the target bit is 0.

2.  **Diffuser (Amplification):** Inverts amplitudes about the mean.
    $$ U_s = 2|s\rangle\langle s| - I $$
    where $|s\rangle$ is the equal superposition state.
    This is implemented as: $H^{\otimes n} \to X^{\otimes n} \to \text{MCZ} \to X^{\otimes n} \to H^{\otimes n}$.

## Running the Example on QVM

We support generating circuits for 2 and 3 qubits.

### 1. Generate the Circuit
Let's find the state "101" (3 qubits). The secret is `101`.

```bash
python examples/generate_grover.py --target 101 --output examples/grover_101.json
```

### 2. Run Simulation
```bash
python -m src.qvm.cli examples/grover_101.json --nqubits 3
```

### 3. Verify Results
After 2 iterations (for 3 qubits), the probability of measuring the target state ("101") should be very high (~94-96%).

**Expected Output:**
```
|101>: 0.9453
```
(Other states will have very small probabilities).
