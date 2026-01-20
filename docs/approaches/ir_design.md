# Quantum Intermediate Representation (IR) Design

## Version 0.1

This document outlines the specification for our custom Quantum Assembly Language (QASM).

### Syntax

- **Qubit Declaration:** `qreg q[SIZE];`
- **Classical Bit Declaration:** `creg c[SIZE];`
- **Gates:** `GATE q[INDEX];` or `GATE q[CONTROL],q[TARGET];`
- **Measurement:** `measure q[Q_INDEX] -> c[C_INDEX];`

### Example

```qasm
// Bell State
qreg q[2];
creg c[2];

h q[0];
cx q[0], q[1];

measure q[0] -> c[0];
measure q[1] -> c[1];
```