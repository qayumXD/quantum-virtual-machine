# Performance snapshot — QVM vs Aer vs Cirq

Best-of-3 wall clock, identical circuits per engine. qiskit 2.4.1, cirq 1.6.1.

QVM's dense kernel is pure NumPy; Aer uses compiled C. The MPS column 
shows where structured simulation wins on low-entanglement families.

| family | n | qvm statevector | qvm MPS | qiskit Aer | cirq |
|---|---|---|---|---|---|
| GHZ | 8 |    0.6ms |    1.0ms |    1.2ms |    4.8ms |
| GHZ | 12 |    1.3ms |    1.3ms |    2.0ms |    5.4ms |
| GHZ | 16 |   14.5ms |    1.7ms |   40.1ms |    8.8ms |
| GHZ | 20 |  313.5ms |    1.3ms |  470.0ms |   96.2ms |
| GHZ | 24 |  13.66s |    1.6ms |  17.58s | - |
| QFT | 8 |    2.4ms |   50.8ms |   10.4ms |   14.6ms |
| QFT | 10 |    5.4ms |  152.8ms |   11.4ms |   13.9ms |
| QFT | 12 |   10.0ms | - |   21.4ms |   18.5ms |
