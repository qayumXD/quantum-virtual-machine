# ---

**PROJECT PROPOSAL (SCOPE DOCUMENT)**

**Project Title:** Quantum Virtual Machine (QVM): A Hardware-Agnostic Quantum Execution Runtime aiming for "Write Once, Run Anywhere" (WORA)

**Project Category:** Quantum Computing, System Software, Compiler Design

## **Abstract**

This project aims to develop a Quantum Virtual Machine (QVM) designed with a "Write Once, Run Anywhere" (WORA) philosophy2. Currently, the quantum computing landscape is fragmented, with different hardware vendors (such as IBM, Google, and Rigetti) utilizing unique native gate sets, qubit topologies, and error profiles. This lack of standardization forces developers to rewrite algorithms for specific machines, leading to vendor lock-in and reduced code portability. To address this, the proposed QVM serves as an abstraction layer. It accepts a high-level quantum program, converts it into a hardware-agnostic Intermediate Representation (IR), and then transpiles it to run on diverse backends, including a custom-built internal simulator and simulated hardware profiles. The project will demonstrate the execution of standard quantum algorithms (e.g., Grover’s Algorithm or Quantum Teleportation) across different architectural constraints without code modification. The result is a unified runtime environment that decouples quantum software development from hardware implementation details3.

\+1

## **Introduction**

Quantum computing promises exponential speedups for specific classes of problems; however, the ecosystem is currently facing a "software crisis" due to hardware diversity4. This project proposes the development of a Quantum Virtual Machine (QVM) that acts as a universal runtime for quantum circuits. The system is designed to bridge the gap between abstract quantum algorithms and physical hardware constraints. By implementing a robust transpilation pipeline, the QVM automates the complex tasks of gate decomposition, qubit mapping, and circuit optimization. This document outlines the scope, objectives, and methodology for building this system, detailing the internal simulator, the intermediate representation strategy, and the architectural adaptations required to achieve true cross-platform compatibility.

## **Problem Statement**

The primary problem this project addresses is **hardware fragmentation** and **vendor lock-in** in the quantum computing domain5. Currently, quantum hardware providers use different underlying technologies (e.g., Superconducting Qubits vs. Trapped Ions), which result in incompatible instruction sets and connectivity graphs. A developer writing code for one platform often cannot run it on another without significant manual refactoring. Furthermore, optimizing a circuit for a specific device’s topology is a complex, error-prone task that requires deep knowledge of the hardware. There is a lack of lightweight, educational, and open-source runtimes that demonstrate how to abstract these complexities effectively6. This project aims to solve these interoperability challenges by automating the translation process.

\+1

## **Problem Solution for Proposed System**

The proposed system solves these problems by introducing a middleware layer—the Quantum Virtual Machine7. Instead of targeting a specific device, the developer writes code for the QVM. The system solves the fragmentation issue through a three-stage pipeline:

1. **Ingestion:** The system accepts a high-level circuit and converts it into a standardized Intermediate Representation (IR).  
2. **Transpilation:** The core engine analyzes the target backend’s constraints (native gates and topology). It inserts SWAP gates where necessary and decomposes complex gates into the target's primitive basis gates.  
3. Execution: The system either executes the circuit on its own internal statevector simulator for verification or outputs the compiled circuit for a specific hardware target.  
   This approach ensures that the logic of the algorithm remains preserved while the implementation details are automatically handled by the software.

## **Related System Analysis/Literature Review**

The domain of quantum software development kits (SDKs) is dominated by major hardware vendors8888.

\+1

* **Qiskit (IBM):** The industry standard, offering a comprehensive suite for programming IBM's superconducting quantum processors. It focuses heavily on pulse-level control and extensive libraries but is tightly coupled with the Python ecosystem and IBM's cloud architecture.  
* **ProjectQ:** An open-source framework developed at ETH Zurich. It features a robust compiler engine that can target various backends. It pioneered many concepts in quantum emulation but has a steep learning curve for beginners.  
* **Rigetti Forest (pyQuil):** Focuses on the Quantum Abstract Machine (QAM) and uses the Quil instruction set. It emphasizes hybrid quantum-classical computing but is primarily designed for Rigetti's specific chip architectures.

The proposed project differs by offering a lightweight, educational-focused implementation of the "Write Once, Run Anywhere" philosophy without the overhead of enterprise cloud dependencies.

**Table 1: Related System Analysis**

| System Name | Features | Limitations | Comparison with Proposed |
| :---- | :---- | :---- | :---- |
| **Qiskit** | Industry standard, huge library | Steep learning curve, heavy install | Proposed system is lightweight and educational. |
| **ProjectQ** | Advanced Compiler Engine | Complex architecture | Proposed system focuses on visual topology mapping. |
| **Quil (Rigetti)** | Hybrid Classical/Quantum support | Vendor specific (Rigetti chips) | Proposed system is hardware agnostic. |

## **Advantages/Benefits of Proposed System**

The advantages of the proposed QVM include9:

* **Hardware Agnosticism:** Developers can write algorithms once and transpile them for different qubit topologies (Linear, Grid) without rewriting code.  
* **Educational Value:** The system provides transparency into the transpilation process, showing users how logical qubits are mapped to physical ones.  
* **Lightweight Runtime:** Unlike massive SDKs (like Qiskit), this QVM is designed to be a minimal, standalone package suitable for local testing.  
* **Cost-Effective:** Eliminates the need for paid cloud subscriptions for testing small-scale algorithms (up to 10 qubits).  
* **Interoperability:** The system can export circuits to the OpenQASM 2.0 standard, making the code compatible with IBM quantum processors.  
* **Visualization:** Provides visual feedback on circuit depth and gate composition before and after transpilation.

## **Scope**

The scope of this project is to develop a desktop-based Quantum Virtual Machine (QVM) using Python10. The system will support the creation, compilation, and simulation of quantum circuits with a maximum capacity of 10 qubits. The core functionality centers on a "Transpiler Pipeline" that accepts a high-level circuit definition and adapts it to specific architectural constraints (e.g., restricted connectivity). The system will strictly use Statevector simulation (exact linear algebra) rather than shot-based sampling to ensure mathematical accuracy for small circuits. The output will include the final state vector, measurement probabilities, and a visualized circuit diagram. The project will **not** include pulse-level control, quantum error correction (QEC), or integration with real hardware APIs beyond OpenQASM string generation.

## **Modules**

The proposed project consists of the following modules11:

Module 1: Quantum Program Parser  
This module serves as the entry point. It accepts the user's high-level quantum code (written in a Python-based DSL) and validates the syntax. It checks for valid gate names, qubit indices, and parameter values.  
Module 2: Intermediate Representation (IR) Engine  
This module converts the parsed code into a hardware-agnostic Directed Acyclic Graph (DAG) or linear instruction list. This IR is the central structure that decouples the algorithm logic from the execution backend.  
Module 3: The Transpiler (Topology Mapper)  
The core intelligence of the system. It takes the IR and a "Target Architecture" (e.g., Linear Line) as input. It utilizes algorithms (such as SWAP insertion) to map logical qubits to physical qubits, ensuring that two-qubit gates only occur between connected neighbors.  
Module 4: Gate Decomposer  
This module translates complex/arbitrary gates into the "Native Gate Set" of the target backend. For example, decomposing a Toffoli gate into a sequence of CNOT and single-qubit rotations.  
Module 5: Statevector Simulator Engine  
The mathematical engine responsible for execution. It utilizes NumPy to perform tensor products and matrix multiplications, evolving the system's state vector step-by-step according to the transpiled circuit.  
Module 6: Visualization and Export Interface  
This module renders the final quantum state as a probability histogram. It also handles the export functionality, converting the internal IR into an OpenQASM 2.0 string for external usage.

## **System Limitations/Constraints**

The limitations of the proposed project are as follows12:

* **Qubit Count Limit:** Due to the exponential memory requirements of statevector simulation ($2^n$ complex numbers), the system is limited to simulating a maximum of 10-12 qubits on standard hardware.  
* **No Error Noise Model:** The simulator is "ideal," meaning it does not simulate decoherence, thermal relaxation, or gate errors.  
* **Classical Overhead:** The transpilation process (finding the optimal SWAP path) is an NP-hard problem; the system will use heuristic approaches which may not always find the absolute optimal circuit depth.

## **Software Process Methodology**

The project will follow the **Agile Iterative Methodology**13. This approach is chosen because quantum software development requires frequent testing and refinement of mathematical kernels. We will develop the core Simulator first (Iteration 1), followed by the Transpiler logic (Iteration 2), and finally the Visualization tools (Iteration 3). This ensures a working prototype is available early in the lifecycle.

## **Tools and Technologies**

The following tools and technologies will be used14:

**Table 2: Tools and Technologies**

| Tool/Technology | Version/Description |
| :---- | :---- |
| **Python** | v3.10+ (Core Programming Language) |
| **NumPy** | Linear Algebra Library for Matrix Operations |
| **NetworkX** | Graph Theory Library (for Topology Mapping) |
| **Matplotlib** | Data Visualization (Histograms/Plots) |
| **VS Code** | Integrated Development Environment |
| **Git/GitHub** | Version Control System |

## **Project Stakeholders and Roles**

15

**Table 3: Project Stakeholders**

| Stakeholder | Role |
| :---- | :---- |
| **Student Developer** | System Architecture, Implementation, Testing |
| **FYP Supervisor** | Guidance, Code Review, Academic Requirements |
| **Quantum Learners** | End-users utilizing the tool for education |

## **Team Members Individual Tasks/Work Division**

(Note: Assuming a single developer based on current context. If there are two, split these tasks.)

**Table 4: Work Division**

| Team Member | Tasks |
| :---- | :---- |
| **Member 1** | Simulator Engine, Transpiler Logic, Documentation, Visualization |

## **Data Gathering Approach**

Since this is a system development project rather than a data science project, "Data Gathering" refers to the acquisition of technical specifications16.

* **Literature Review:** Analyzing whitepapers from IBM and Rigetti to understand their native gate sets and topology constraints.  
* **Algorithm Benchmarking:** Collecting standard quantum algorithms (Bernstein-Vazirani, Grover's) to use as test cases for the transpiler.

## **Concepts**

The following concepts will be learned during the project17:

Concept-1: Quantum Superposition  
The fundamental principle where a qubit exists in a linear combination of |0⟩ and |1⟩ states simultaneously. The simulator must mathematically represent this using complex vectors.  
Concept-2: Qubit Topology & Mapping  
Real quantum chips have limited connectivity (not all qubits are connected). This concept involves using Graph Theory to map abstract program variables to physical nodes on a chip.  
Concept-3: Transpilation  
The process of source-to-source compiling. In this project, it specifically refers to transforming a high-level circuit into a lower-level equivalent that respects hardware constraints (inserting SWAP gates).  
Concept-4: Unitary Transformations  
Quantum gates are unitary matrices that preserve the norm of the probability amplitude. The project involves implementing these linear algebra operations efficiently.

## **Gantt Chart**

(Below is a tabular representation of the timeline to be converted into a chart)

| Phase | Task | Duration | Month |
| :---- | :---- | :---- | :---- |
| **Phase 1** | Literature Review & Requirement Analysis | 2 Weeks | Month 1 |
| **Phase 2** | Design of Intermediate Representation (IR) | 2 Weeks | Month 1 |
| **Phase 3** | Implementation of Simulator Engine | 4 Weeks | Month 2 |
| **Phase 4** | Implementation of Transpiler (Basic) | 3 Weeks | Month 3 |
| **Phase 5** | Implementation of Topology Mapping | 3 Weeks | Month 3-4 |
| **Phase 6** | Testing & Validation (Standard Algos) | 2 Weeks | Month 4 |
| **Phase 7** | Final Documentation & Thesis Writing | 4 Weeks | Month 5 |

## **Mockups**

18

Figure 1: Main Dashboard  
Description: A split-screen interface. The left panel is a code editor where the user writes python-like quantum code. The right panel displays a live-updated circuit diagram showing the gates placed on the qubits.  
Figure 2: Transpilation View  
Description: A comparison view. The top shows the "Logical Circuit" (clean, ideal). The bottom shows the "Physical Circuit" (after transpilation), highlighting where SWAP gates were inserted to respect the device's connectivity constraints.  
Figure 3: Execution Results  
Description: A probability histogram (bar chart). The X-axis represents the measurement states (00, 01, 10, 11\) and the Y-axis represents the probability percentage, verifying the algorithm's correctness.

## **Conclusion**

In conclusion, the development of a hardware-agnostic Quantum Virtual Machine addresses the critical issue of fragmentation in the quantum computing ecosystem. By enabling a "Write Once, Run Anywhere" workflow, this project not only facilitates easier experimentation for students and researchers but also demonstrates the fundamental principles of quantum compilation. The successful implementation of the transpiler and simulator will result in a robust tool that bridges the gap between high-level algorithmic logic and low-level physical constraints.

## **References**

19

1. M. A. Nielsen and I. L. Chuang, *Quantum Computation and Quantum Information*, Cambridge University Press, 2010\.  
2. IBM Quantum, "Qiskit Documentation," \[Online\]. Available: [https://qiskit.org/](https://qiskit.org/).  
3. A. W. Cross, et al., "OpenQASM 3: A broader and deeper quantum assembly language," *arXiv preprint arXiv:2104.01472*, 2021\.  
4. Steiger, D. S., Häner, T., & Troyer, M. (2018). "ProjectQ: An open source software framework for quantum computing." *Quantum*, 2, 49\.