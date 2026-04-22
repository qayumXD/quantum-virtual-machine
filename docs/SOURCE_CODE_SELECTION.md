# Source Code Selection for Appendix C

**Date:** April 22, 2026  
**Purpose:** Select 5-10 key source files for inclusion in Appendix C

---

## Selected Files (8 files)

### Core System Files (5 files)

1. **src/qvm/ir.py** (~100 lines)
   - **Purpose:** Intermediate Representation (IR) for quantum circuits
   - **Why include:** Demonstrates the core data structure that unifies all circuit representations
   - **Key features:** QuantumCircuit class, classical registers, conditional operations, control flow

2. **src/qvm/parser.py** (~150 lines)
   - **Purpose:** OpenQASM 2.0 parser
   - **Why include:** Shows input processing and validation logic
   - **Key features:** QASM parsing, register declarations, gate parsing, error handling

3. **src/qvm/simulator.py** (~200 lines)
   - **Purpose:** Statevector simulator with classical memory
   - **Why include:** Core execution engine demonstrating quantum gate application
   - **Key features:** Gate matrices, statevector evolution, measurement, conditional execution, control flow

4. **src/qvm/transpiler.py** (~200 lines)
   - **Purpose:** Hardware-aware circuit compilation
   - **Why include:** Demonstrates the transpilation algorithms (Greedy BFS and SABRE)
   - **Key features:** Qubit mapping, SWAP insertion, routing strategies, topology handling

5. **src/qvm/cli.py** (~100 lines)
   - **Purpose:** Command-line interface
   - **Why include:** Shows user interaction and system integration
   - **Key features:** Argument parsing, file loading, pipeline orchestration, visualization

### Supporting Files (3 files)

6. **src/qvm/qasm3_parser.py** (~300 lines - will excerpt key sections)
   - **Purpose:** OpenQASM 3.0 parser with Lark grammar
   - **Why include:** Demonstrates advanced parsing with control flow support
   - **Key sections:** Parser class, grammar transformer, control flow handling
   - **Note:** Will include ~150 lines of most important sections

7. **src/qvm/architecture.py** (~80 lines)
   - **Purpose:** Hardware topology definitions
   - **Why include:** Shows how physical constraints are modeled
   - **Key features:** TargetArchitecture class, linear/grid topologies, connectivity

8. **src/qvm/decomposer.py** (~100 lines)
   - **Purpose:** Gate decomposition into native gate sets
   - **Why include:** Demonstrates circuit transformation logic
   - **Key features:** Toffoli decomposition, gate substitution

---

## Total Line Count Estimate

- ir.py: ~100 lines
- parser.py: ~150 lines
- simulator.py: ~200 lines
- transpiler.py: ~200 lines
- cli.py: ~100 lines
- qasm3_parser.py (excerpt): ~150 lines
- architecture.py: ~80 lines
- decomposer.py: ~100 lines

**Total:** ~1,080 lines

---

## Files NOT Included (and why)

1. **src/qvm/visual.py** - Visualization code is straightforward matplotlib usage
2. **src/qvm/server.py** - Web API is standard FastAPI boilerplate
3. **src/qvm/mps_simulator.py** - Advanced feature, less central to core functionality
4. **src/qvm/util/** - Utility functions are not architecturally significant
5. **src/examples/** - Example usage, not core implementation
6. **Test files** - Testing code is not part of the main system

---

## Formatting Guidelines for Appendix

Each file will be formatted as:

```latex
\subsection{File: src/qvm/filename.py}

\textbf{Purpose:} Brief description

\textbf{Key Features:}
\begin{itemize}
\item Feature 1
\item Feature 2
\item Feature 3
\end{itemize}

\begin{lstlisting}[language=Python, caption={filename.py}]
# Source code here
\end{lstlisting}
```

---

## LaTeX Package Requirements

The appendix will use the `listings` package for syntax highlighting:

```latex
\usepackage{listings}
\usepackage{xcolor}

\lstset{
  language=Python,
  basicstyle=\ttfamily\small,
  keywordstyle=\color{blue},
  commentstyle=\color{gray},
  stringstyle=\color{red},
  numbers=left,
  numberstyle=\tiny\color{gray},
  stepnumber=1,
  numbersep=5pt,
  backgroundcolor=\color{white},
  showspaces=false,
  showstringspaces=false,
  showtabs=false,
  frame=single,
  tabsize=2,
  captionpos=b,
  breaklines=true,
  breakatwhitespace=false
}
```

---

## Next Steps

1. Read each selected file
2. Format with LaTeX listings syntax
3. Add to ch_9_appendix_source_code.tex
4. Compile and verify formatting
5. Check page count (expect ~15-20 pages for appendix)

---

**Status:** Selection complete, ready for LaTeX formatting  
**Estimated Appendix Length:** 15-20 pages
