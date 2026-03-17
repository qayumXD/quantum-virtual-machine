OPENQASM 3.0;
qubit[2] q;
bit[2] c;
bit parity;

h q[0];
cx q[0], q[1];

c[0] = measure q[0];
c[1] = measure q[1];

// Classical Shadowing: Compute parity
parity = c[0] ^ c[1];

// If parity is 1 (error in Bell state), flip q[0]
// Note: In our ideal simulator, parity will always be 0
if (parity == 1) {
    x q[0];
}
