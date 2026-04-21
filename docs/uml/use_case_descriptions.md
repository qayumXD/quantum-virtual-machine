# Use Case Descriptions - Quantum Virtual Machine (QVM)

**Document Version:** 1.0  
**Date:** April 21, 2026  
**Status:** Phase 2 - Week 2

---

## UC-1.1: Load Quantum Circuit

**Use Case ID:** UC-1.1  
**Use Case Name:** Load Quantum Circuit  
**Actor:** Quantum Algorithm Developer, Educational User  
**Priority:** High  
**Preconditions:** 
- User has a valid quantum circuit file (QASM or JSON format)
- QVM system is running

**Main Flow:**
1. User specifies the circuit file path
2. System validates file format (QASM 2.0, QASM 3.0, or JSON)
3. System reads the file content
4. System validates file syntax
5. System loads circuit into memory
6. System displays confirmation message

**Postconditions:**
- Circuit is loaded and ready for parsing
- Circuit metadata is available (qubit count, gate count)

**Alternative Flows:**
- **AF-1:** Invalid file format
  - System displays error message
  - System prompts user to provide valid file
- **AF-2:** File not found
  - System displays file not found error
  - System prompts user to check file path

**Business Rules:**
- Supported formats: OpenQASM 2.0, OpenQASM 3.0, JSON
- Maximum file size: 10 MB
- Maximum qubits: 20 (12 for Statevector, 20+ for MPS)

---

## UC-1.2: Parse Circuit (QASM/JSON)

**Use Case ID:** UC-1.2  
**Use Case Name:** Parse Circuit  
**Actor:** System (automated)  
**Priority:** High  
**Preconditions:**
- Circuit file is loaded (UC-1.1 complete)

**Main Flow:**
1. System identifies circuit format (QASM or JSON)
2. System invokes appropriate parser (Lark for QASM, JSON parser for JSON)
3. Parser generates Abstract Syntax Tree (AST)
4. System maps AST to internal Intermediate Representation (IR)
5. System validates circuit semantics (qubit indices, gate parameters)
6. System creates QuantumCircuit object

**Postconditions:**
- Circuit is represented as QuantumCircuit IR
- Circuit is ready for transpilation

**Alternative Flows:**
- **AF-1:** Syntax error in QASM
  - System displays line number and error description
  - System halts execution
- **AF-2:** Invalid gate parameters
  - System displays parameter validation error
  - System suggests valid parameter ranges

**Business Rules:**
- All qubit indices must be within declared range
- Gate parameters must be valid (e.g., rotation angles)
- Control flow constructs (if, for, while) supported in QASM 3.0 only

---

## UC-1.3: Transpile Circuit

**Use Case ID:** UC-1.3  
**Use Case Name:** Transpile Circuit  
**Actor:** Quantum Algorithm Developer  
**Priority:** High  
**Preconditions:**
- Circuit is parsed and in IR format (UC-1.2 complete)
- Target architecture is configured (UC-2.1)

**Main Flow:**
1. User initiates transpilation
2. System retrieves target architecture constraints (topology, native gates)
3. System decomposes high-level gates into native gate set
4. System maps logical qubits to physical qubits
5. System inserts SWAP gates to respect connectivity constraints
6. System optimizes circuit depth
7. System generates transpiled circuit
8. System displays transpilation statistics (depth, SWAP count)

**Postconditions:**
- Circuit is transpiled for target architecture
- Circuit respects hardware constraints
- Circuit is ready for simulation

**Alternative Flows:**
- **AF-1:** No valid qubit mapping found
  - System displays error message
  - System suggests alternative architectures
- **AF-2:** Circuit depth exceeds threshold
  - System displays warning
  - System proceeds with transpilation

**Business Rules:**
- SWAP gates inserted only when necessary
- Routing algorithm: Greedy or SABRE (user-configurable)
- Optimization goal: Minimize circuit depth

---

## UC-1.4: Simulate Circuit

**Use Case ID:** UC-1.4  
**Use Case Name:** Simulate Circuit  
**Actor:** Quantum Algorithm Developer, Educational User  
**Priority:** High  
**Preconditions:**
- Circuit is transpiled (UC-1.3 complete) OR parsed (UC-1.2 complete)
- Simulation backend is selected (UC-2.3)

**Main Flow:**
1. User initiates simulation
2. System selects simulation backend (Statevector or MPS)
3. System initializes quantum state (|0...0⟩)
4. System applies gates sequentially
5. System performs measurements (if specified)
6. System calculates final state probabilities
7. System returns simulation results

**Postconditions:**
- Simulation results are available
- State vector or probability distribution is computed
- Classical memory states are updated (if applicable)

**Alternative Flows:**
- **AF-1:** Insufficient memory for Statevector
  - System suggests using MPS backend
  - System halts execution
- **AF-2:** Circuit exceeds qubit limit
  - System displays error message
  - System suggests reducing circuit size

**Business Rules:**
- Statevector: Up to 12 qubits
- MPS: Up to 20+ qubits (low-entanglement circuits)
- Simulation is exact (no noise model)

---

## UC-1.5: Visualize Results

**Use Case ID:** UC-1.5  
**Use Case Name:** Visualize Results  
**Actor:** Quantum Algorithm Developer, Educational User  
**Priority:** Medium  
**Preconditions:**
- Simulation is complete (UC-1.4 complete)

**Main Flow:**
1. System retrieves simulation results
2. System generates probability histogram
3. System displays measurement outcomes
4. System shows classical memory states (if applicable)
5. User can export visualization as image

**Postconditions:**
- Results are visualized
- User understands simulation outcomes

**Alternative Flows:**
- **AF-1:** No measurements in circuit
  - System displays state vector amplitudes
  - System shows probability distribution for all basis states

**Business Rules:**
- Visualization format: Bar chart (probability histogram)
- Export formats: PNG, SVG
- Display top 10 most probable states (if > 10 states)

---

## UC-2.1: Configure Target Architecture

**Use Case ID:** UC-2.1  
**Use Case Name:** Configure Target Architecture  
**Actor:** Quantum Algorithm Developer  
**Priority:** Medium  
**Preconditions:**
- QVM system is running

**Main Flow:**
1. User selects target architecture type (Linear, Grid, Custom)
2. User specifies qubit count
3. User defines connectivity graph (for Custom)
4. System validates architecture configuration
5. System saves architecture settings
6. System displays confirmation

**Postconditions:**
- Target architecture is configured
- Transpiler will use this architecture for qubit mapping

**Alternative Flows:**
- **AF-1:** Invalid connectivity graph
  - System displays validation error
  - System prompts user to correct graph

**Business Rules:**
- Supported architectures: Linear, Grid, Custom
- Minimum qubits: 2
- Maximum qubits: 20

---

## UC-2.2: Select Routing Algorithm

**Use Case ID:** UC-2.2  
**Use Case Name:** Select Routing Algorithm  
**Actor:** Quantum Algorithm Developer  
**Priority:** Low  
**Preconditions:**
- QVM system is running

**Main Flow:**
1. User selects routing algorithm (Greedy or SABRE)
2. System validates selection
3. System saves routing algorithm preference
4. System displays confirmation

**Postconditions:**
- Routing algorithm is configured
- Transpiler will use selected algorithm

**Business Rules:**
- Supported algorithms: Greedy, SABRE
- Default: SABRE (better optimization)

---

## UC-2.3: Set Simulation Backend

**Use Case ID:** UC-2.3  
**Use Case Name:** Set Simulation Backend  
**Actor:** Quantum Algorithm Developer  
**Priority:** Medium  
**Preconditions:**
- QVM system is running

**Main Flow:**
1. User selects simulation backend (Statevector or MPS)
2. System validates selection based on circuit size
3. System saves backend preference
4. System displays confirmation

**Postconditions:**
- Simulation backend is configured
- Simulator will use selected backend

**Alternative Flows:**
- **AF-1:** Circuit too large for Statevector
  - System suggests MPS backend
  - System allows user to override (with warning)

**Business Rules:**
- Statevector: Recommended for ≤ 12 qubits
- MPS: Recommended for low-entanglement circuits (up to 20+ qubits)

---

## UC-3.1: Export Circuit (OpenQASM)

**Use Case ID:** UC-3.1  
**Use Case Name:** Export Circuit  
**Actor:** Quantum Algorithm Developer  
**Priority:** Medium  
**Preconditions:**
- Circuit is loaded and optionally transpiled

**Main Flow:**
1. User initiates export
2. User selects export format (QASM 2.0 or QASM 3.0)
3. System converts internal IR to QASM format
4. System writes QASM string to file
5. System displays export confirmation

**Postconditions:**
- Circuit is exported as QASM file
- File is compatible with external quantum platforms (e.g., IBM Quantum)

**Business Rules:**
- Supported formats: OpenQASM 2.0, OpenQASM 3.0
- Export includes all gates and measurements
- Classical control flow exported only in QASM 3.0

---

## UC-3.2: Access via REST API

**Use Case ID:** UC-3.2  
**Use Case Name:** Access via REST API  
**Actor:** External System  
**Priority:** Medium  
**Preconditions:**
- QVM API server is running
- External system has valid API credentials (if required)

**Main Flow:**
1. External system sends HTTP POST request with circuit data
2. API validates request format
3. API invokes QVM core (parse, transpile, simulate)
4. API returns simulation results as JSON
5. External system processes results

**Postconditions:**
- External system receives simulation results
- Results are in JSON format

**Alternative Flows:**
- **AF-1:** Invalid request format
  - API returns 400 Bad Request error
  - API provides error details in response

**Business Rules:**
- API endpoint: POST /api/execute
- Request format: JSON
- Response format: JSON
- Timeout: 60 seconds

---

## UC-3.3: Access via Web GUI

**Use Case ID:** UC-3.3  
**Use Case Name:** Access via Web GUI  
**Actor:** Educational User, Quantum Algorithm Developer  
**Priority:** Medium  
**Preconditions:**
- QVM web server is running
- User has web browser

**Main Flow:**
1. User opens web browser and navigates to QVM GUI
2. User enters or uploads circuit code
3. User configures simulation parameters (optional)
4. User clicks "Execute" button
5. GUI sends request to backend API
6. GUI displays simulation results and visualizations

**Postconditions:**
- User sees simulation results in browser
- User can interact with visualizations

**Business Rules:**
- GUI URL: http://localhost:8000
- Supports circuit input via text editor or file upload
- Real-time result updates

---

## UC-4.1: View System Metrics

**Use Case ID:** UC-4.1  
**Use Case Name:** View System Metrics  
**Actor:** System Administrator  
**Priority:** Low  
**Preconditions:**
- QVM system is running
- Admin has access credentials

**Main Flow:**
1. Admin accesses system metrics dashboard
2. System displays performance metrics (CPU, memory usage)
3. System displays execution statistics (circuits executed, average time)
4. Admin can export metrics as CSV

**Postconditions:**
- Admin has visibility into system performance

**Business Rules:**
- Metrics updated every 5 seconds
- Historical data retained for 30 days

---

## UC-4.2: Manage Configurations

**Use Case ID:** UC-4.2  
**Use Case Name:** Manage Configurations  
**Actor:** System Administrator  
**Priority:** Low  
**Preconditions:**
- QVM system is running
- Admin has access credentials

**Main Flow:**
1. Admin accesses configuration management interface
2. Admin modifies system settings (timeouts, limits, defaults)
3. System validates configuration changes
4. System saves new configuration
5. System displays confirmation

**Postconditions:**
- System configuration is updated
- New settings take effect immediately or after restart

**Business Rules:**
- Configuration stored in config file
- Backup created before changes
- Invalid configurations rejected

---

## Summary

**Total Use Cases:** 13  
**High Priority:** 5 (UC-1.1 to UC-1.5)  
**Medium Priority:** 6 (UC-2.1, UC-2.3, UC-3.1, UC-3.2, UC-3.3)  
**Low Priority:** 2 (UC-2.2, UC-4.1, UC-4.2)

**Actors:**
- Quantum Algorithm Developer (Primary)
- Educational User
- System Administrator
- External System

**Key Relationships:**
- UC-1.1 includes UC-1.2 (Load → Parse)
- UC-1.2 includes UC-1.3 (Parse → Transpile)
- UC-1.3 includes UC-1.4 (Transpile → Simulate)
- UC-1.4 includes UC-1.5 (Simulate → Visualize)
- UC-1.3 extends UC-2.1, UC-2.2 (Transpile configuration)
- UC-1.4 extends UC-2.3 (Simulation backend selection)

---

**Document Status:** Complete  
**Next Step:** Create Class Diagram
