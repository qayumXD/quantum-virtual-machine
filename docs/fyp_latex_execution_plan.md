# FYP LaTeX Documentation - Execution Plan
**Project:** Quantum Virtual Machine (QVM)  
**Strategy:** Critical Path First Approach  
**Total Duration:** 8 Weeks (~76 hours)  
**Start Date:** April 21, 2026

---

## 🎯 Overall Strategy

**Why Critical Path First?**
1. ✅ Build momentum with quick wins
2. ✅ Tackle hardest parts (Chapters 3 & 4) while fresh
3. ✅ Reduce risk - critical content done early
4. ✅ Flexibility - can adjust timeline if needed
5. ✅ Parallel work possible

---

## 📋 Phase 1: Foundation & Quick Wins (Week 1)
**Goal:** Build momentum, complete 3 chapters to 90%, set up tools  
**Duration:** 7 days  
**Estimated Effort:** 12-15 hours

### Day 1-2: Chapter 7 - Conclusion (2-3 hours)
**Status:** 80% → 100% ✅ **COMPLETE**  
**Tasks:**
- [x] Read existing content from final_project_report.md
- [x] Write Section 7.1: Conclusion (500 words) ✅
- [x] Write Section 7.2: Future Work (450 words) ✅
- [x] Update Section 7.3: Limitations (300 words) ✅
- [x] Review and polish ✅

**Content Sources:**
- `docs/reports/final_project_report.md`
- `docs/reports/status_update_2026_02_27.md`
- `docs/ScopeDocumentV1.md` (limitations section)

---

### Day 3-4: Chapter 1 - Introduction (Sections 1.1-1.6) (4-5 hours)
**Status:** 60% → 90% ✅ **COMPLETE**  
**Tasks:**
- [x] Section 1.1: Introduction (550 words) ✅
  - Extracted from ScopeDocumentV1.md Introduction
  - Added current industry context
  - Mentioned v0.2 features
- [x] Section 1.2: Vision Statement (280 words) ✅
  - Used ScopeDocumentV1.md Abstract
  - Emphasized WORA philosophy
- [x] Section 1.3: Related System Analysis (750 words + table) ✅
  - Expanded existing Table 1 from ScopeDocumentV1.md
  - Added details on Qiskit, ProjectQ, Cirq, PyQuil
- [x] Section 1.4: Project Deliverables (650 words) ✅
  - Listed all 11 deliverables
  - CLI, API, Web GUI
  - Documentation artifacts
- [x] Section 1.5: System Limitations (450 words) ✅
  - Updated from ScopeDocumentV1.md
  - Added current limitations (12 qubits, ideal simulator)
- [x] Section 1.6: Tools & Technologies (400 words + table) ✅
  - Updated Table 2 with current versions
  - Added Lark, FastAPI, pytest, NetworkX

**DEFERRED:** Section 1.7 (Course Relevance) - Will do in Phase 4 ✅

---

### Day 5-6: Chapter 2 - Problem Definition (Sections 2.1-2.6) (4-5 hours)
**Status:** 70% → 90%  
**Tasks:**
- [ ] Section 2.1: Problem Statement (100-150 words)
  - Use ScopeDocumentV1.md Problem Statement
  - Refine wording
- [ ] Section 2.2: Proposed Solution (100-150 words)
  - Use ScopeDocumentV1.md Problem Solution
  - Update with v0.2 features
- [ ] Section 2.3: Objectives (List of BO-1 to BO-5)
  - Format existing objectives as BO-1, BO-2, etc.
- [ ] Section 2.4: Scope (100-150 words)
  - Update from ScopeDocumentV1.md
  - Mention 12 qubits, OpenQASM 3.0 support
- [ ] Section 2.5: Architecture Overview (100-150 words)
  - Describe pipeline architecture
  - Mention we'll add diagram later
- [ ] Section 2.6: Assumptions & Dependencies (80-120 words)
  - Update from ScopeDocumentV1.md

**SKIP FOR NOW:** Section 2.5.1-5 (Module Descriptions) - Will do in Phase 4

---

### Day 7: Tool Setup & Verification (2 hours)
**Tasks:**
- [x] Overleaf account setup (DONE)
- [x] Local LaTeX installation (DONE)
- [x] PlantUML .jar downloaded (DONE)
- [ ] Test PlantUML with simple diagram
- [ ] Upload LaTeX template to Overleaf
- [ ] Test compilation of template
- [ ] Create backup strategy (Git + Overleaf)
- [ ] Install Draw.io (optional, for complex diagrams)

**Tools Confirmed:**
- ✅ Overleaf (online)
- ✅ Local LaTeX
- ✅ PlantUML (.jar)
- 🔄 Draw.io (optional)
- 🔄 Mermaid (optional, for flowcharts)

---

## 📊 Phase 1 Success Metrics

**By End of Week 1:**
- ✅ Chapter 7: 100% complete
- ✅ Chapter 1 (sections 1.1-1.6): 90% complete
- ✅ Chapter 2 (sections 2.1-2.6): 90% complete
- ✅ All tools tested and working
- ✅ LaTeX compiles successfully
- ✅ ~3 chapters essentially done
- ✅ Momentum and confidence built

---

## 🎯 Phase 2: The Critical Bottleneck (Week 2-4)
**Goal:** Complete Chapters 3 & 4 (Requirements & Design)  
**Duration:** 3 weeks  
**Estimated Effort:** 25-30 hours

### Week 2: Use Cases & Initial Diagrams (8-10 hours)

#### Chapter 3: Requirements - Part 1
**Tasks:**
- [ ] Section 3.3: User Classes (Define 4 user classes)
  - Quantum Algorithm Developer (Primary)
  - System Administrator
  - Educational User
  - External System (API consumer)
- [ ] Section 3.5.1: Use Case Diagram (PlantUML)
  - 8-10 use cases
  - Actors: Developer, Admin, External System
- [ ] Section 3.5.2: Use Case Descriptions (5-6 detailed tables)
  - UC-1.1: Load Circuit (JSON/QASM)
  - UC-1.2: Transpile Circuit
  - UC-1.3: Simulate Circuit
  - UC-1.4: Visualize Results
  - UC-2.1: Configure Architecture
  - UC-3.1: Export Circuit

#### Chapter 4: Design - Part 1
**Tasks:**
- [ ] Section 4.3: Context Diagram (PlantUML/Draw.io)
  - Show QVM system boundary
  - External actors: User, File System, Web Browser
  - Input: QASM files, JSON
  - Output: Results, Visualizations
- [ ] Section 4.4: Architecture Diagram (PlantUML/Draw.io)
  - Pipeline architecture
  - 6 layers: Parser → IR → Decomposer → Transpiler → Simulator → Visualizer

---

### Week 3: Requirements & Class/Activity Diagrams (8-10 hours)

#### Chapter 3: Requirements - Part 2
**Tasks:**
- [ ] Section 3.6: Functional Requirements (20-30 FRs)
  - Extract from code and documentation
  - FR-1.x: Parser Module (5 FRs)
  - FR-2.x: Transpiler Module (5 FRs)
  - FR-3.x: Simulator Module (5 FRs)
  - FR-4.x: Visualization Module (3 FRs)
  - FR-5.x: CLI/API Module (5 FRs)
- [ ] Section 3.7: Non-Functional Requirements (15-20 NFRs)
  - Performance (PER-1 to PER-4)
  - Reliability (REL-1 to REL-3)
  - Usability (USE-1 to USE-4)
  - Maintainability (MAIN-1 to MAIN-3)
  - Scalability (SCA-1 to SCA-3)

#### Chapter 4: Design - Part 2
**Tasks:**
- [ ] Section 4.6: Class Diagram (PlantUML)
  - Core classes: QuantumCircuit, Simulator, Transpiler, Parser
  - Show relationships and key methods
- [ ] Section 4.5.1: Activity Diagram - Circuit Execution (PlantUML)
  - Flow: Load → Parse → Decompose → Transpile → Simulate → Output
- [ ] Section 4.5.2: Activity Diagram - Transpilation (PlantUML)
  - Flow: Check connectivity → Find path → Insert SWAPs → Verify
- [ ] Section 4.5.3: Activity Diagram - Simulation (PlantUML)
  - Flow: Initialize state → Apply gates → Measure → Return results

---

### Week 4: Final Diagrams & Traceability (8-10 hours)

#### Chapter 3: Requirements - Part 3
**Tasks:**
- [ ] Section 3.8: External Interface Requirements
  - UI-1 to UI-4 (CLI, Web GUI)
  - SI-1 to SI-4 (NumPy, Lark, FastAPI)
  - CI-1 to CI-4 (HTTP, JSON, WebSockets)
- [ ] Section 3.9: Requirement Traceability Matrix
  - Map BO-1 to BO-5 → Use Cases → Functional Requirements
- [ ] Review and polish Chapter 3

#### Chapter 4: Design - Part 3
**Tasks:**
- [ ] Section 4.7.1: Sequence Diagram - CLI Execution (PlantUML)
  - User → CLI → Parser → Simulator → Visualizer
- [ ] Section 4.7.2: Sequence Diagram - API Request (PlantUML)
  - Client → FastAPI → QVM Core → Response
- [ ] Section 4.8: State Diagram - Circuit Lifecycle (PlantUML)
  - States: Loaded → Parsed → Decomposed → Transpiled → Simulated → Complete
- [ ] Section 4.9.1: Level 1 DFD (PlantUML/Draw.io)
  - Major processes: Parse, Transpile, Simulate
- [ ] Section 4.9.2: Level 2 DFD - Transpilation (PlantUML/Draw.io)
  - Sub-processes: Map qubits, Find paths, Insert SWAPs
- [ ] Review and polish Chapter 4

---

## 📊 Phase 2 Success Metrics

**By End of Week 4:**
- ✅ Chapter 3: 100% complete (all requirements documented)
- ✅ Chapter 4: 100% complete (all diagrams created)
- ✅ 10-12 UML diagrams created
- ✅ 20-30 functional requirements documented
- ✅ Traceability matrix complete
- ✅ Hardest work DONE!

---

## 🎯 Phase 3: Implementation & Testing (Week 5-6)
**Goal:** Document existing implementation and testing  
**Duration:** 2 weeks  
**Estimated Effort:** 15-18 hours

### Week 5: Implementation Documentation (8-9 hours)

#### Chapter 5: Implementation - Part 1
**Tasks:**
- [ ] Section 5.1: Development Environment (200-300 words)
  - Python 3.10+, VS Code, Git
  - NumPy, Lark, FastAPI, pytest
- [ ] Section 5.2: Core Module Implementation
  - 5.2.1: Parser Module (explain qasm3_parser.py)
  - 5.2.2: IR Module (explain ir.py)
  - 5.2.3: Transpiler Module (explain transpiler.py)
  - 5.2.4: Simulator Module (explain simulator.py)
  - 5.2.5: Visualization Module (explain visual.py)
- [ ] Section 5.3: Algorithm Implementation
  - Algorithm 1: SABRE Routing (pseudocode)
  - Algorithm 2: Statevector Simulation (pseudocode)
  - Algorithm 3: MPS Simulation (pseudocode)

#### Chapter 6: Testing - Part 1
**Tasks:**
- [ ] Section 6.1: Testing Strategy (150-200 words)
  - Pytest framework
  - Unit, integration, system testing
- [ ] Section 6.2: Unit Testing (Format existing tests)
  - UT-01 to UT-10 (from test_simulator.py, test_transpiler.py)
  - Create test case tables

---

### Week 6: UI, Testing & Performance (7-9 hours)

#### Chapter 5: Implementation - Part 2
**Tasks:**
- [ ] Section 5.4: External APIs/SDKs (Table)
  - NumPy, Lark, FastAPI, Matplotlib
- [ ] Section 5.5: User Interface Implementation
  - 5.5.1: UI Design Approach (CLI-first, then Web)
  - 5.5.2: CLI Interface (screenshot + explanation)
  - 5.5.3: Web GUI (screenshot + explanation)
  - Capture 3-4 screenshots
- [ ] Section 5.6: Deployment (Local setup instructions)

#### Chapter 6: Testing - Part 2
**Tasks:**
- [ ] Section 6.3: Integration Testing (3-5 test cases)
- [ ] Section 6.4: System Testing (End-to-end validation)
- [ ] Section 6.5: Performance Testing
  - Run benchmarks (2-12 qubits)
  - Create performance metrics table
- [ ] Section 6.8: User Acceptance Testing
  - Conduct UAT with 3-5 users
  - Collect feedback
  - Create feedback summary table
- [ ] Section 6.9: Testing Summary

---

## 📊 Phase 3 Success Metrics

**By End of Week 6:**
- ✅ Chapter 5: 100% complete (all implementation documented)
- ✅ Chapter 6: 100% complete (all testing documented)
- ✅ 3-4 screenshots captured
- ✅ UAT conducted with 3-5 users
- ✅ Performance benchmarks run
- ✅ Only polish work remaining!

---

## 🎯 Phase 4: Polish & Complete (Week 7-8)
**Goal:** Fill remaining gaps, polish, finalize  
**Duration:** 2 weeks  
**Estimated Effort:** 10-12 hours

### Week 7: Fill Gaps & Review (6-7 hours)

**Tasks:**
- [ ] Chapter 1.7: Relevance to Course Modules (400-600 words)
  - 1.7.1: Programming Fundamentals (80-120 words)
  - 1.7.2: Data Structures & Algorithms (80-120 words)
  - 1.7.3: Database Management (80-120 words) - Explain N/A
  - 1.7.4: Software Engineering (80-120 words)
  - 1.7.5: Other Courses (80-120 words) - Linear Algebra, Quantum Computing
- [ ] Chapter 2.5.1-5: Module Descriptions (5 × 80-120 words)
  - Module 1: Parser Module
  - Module 2: Transpiler Module
  - Module 3: Simulator Module
  - Module 4: Visualization Module
  - Module 5: CLI/API Module
- [ ] Review all chapters for consistency
- [ ] Check all cross-references
- [ ] Verify all figure/table numbers

---

### Week 8: Final Polish & Submission (4-5 hours)

**Tasks:**
- [ ] Write Executive Summary (1 page)
- [ ] Write Dedication
- [ ] Write Acknowledgements
- [ ] Create Abbreviations list
- [ ] Appendix A: Turnitin Report (generate)
- [ ] Appendix B: AI Detection Report (generate)
- [ ] Appendix C: Source Code (select key files)
- [ ] Final LaTeX compilation check
- [ ] Generate PDF
- [ ] Check formatting (margins, fonts, spacing)
- [ ] Proofread entire document
- [ ] Submit!

---

## 📊 Phase 4 Success Metrics

**By End of Week 8:**
- ✅ All 7 chapters: 100% complete
- ✅ All appendices complete
- ✅ Executive summary written
- ✅ PDF generated and formatted correctly
- ✅ Document proofread
- ✅ READY FOR SUBMISSION! 🎉

---

## 🛠️ Tools & Resources

### Diagram Tools
- **PlantUML** (.jar) - Primary for UML diagrams
- **Draw.io** - Backup for complex diagrams
- **Mermaid** - Optional for flowcharts

### LaTeX Environment
- **Overleaf** - Online collaborative editing
- **Local LaTeX** - Backup compilation
- **Git** - Version control

### Testing Tools
- **pytest** - Already in use
- **Greenshot/Snipping Tool** - Screenshots

---

## 📈 Progress Tracking

### Overall Completion Status
```
Phase 1 (Week 1):  [█████░░░░░] 50% → Target: 100%
Phase 2 (Week 2-4): [░░░░░░░░░░] 0% → Target: 100%
Phase 3 (Week 5-6): [░░░░░░░░░░] 0% → Target: 100%
Phase 4 (Week 7-8): [░░░░░░░░░░] 0% → Target: 100%
```

### Chapter Completion Status
```
Chapter 7: [██████████] 100% ✅ COMPLETE
Chapter 1: [█████████░] 90% ✅ (1.7 deferred to Phase 4)
Chapter 2: [░░░░░░░░░░] 0% → Target: 90% (Phase 1)
```

### Time Tracking
```
Estimated Phase 1: 12-15 hours
Actual Time Spent: ~5-6 hours (Days 1-4)
Remaining: ~6-9 hours (Days 5-7)
Status: AHEAD OF SCHEDULE ✅
```

---

## 🎯 Current Focus: PHASE 1 - DAY 1-2

**Immediate Task:** Complete Chapter 7 (Conclusion)  
**Estimated Time:** 2-3 hours  
**Status:** Ready to start!

**Next Steps:**
1. Read existing content from reports
2. Write Section 7.1: Conclusion (300-500 words)
3. Write Section 7.2: Future Work (200-300 words)
4. Update Section 7.3: Limitations (100-150 words)
5. Review and polish

---

**Document Version:** 1.0  
**Last Updated:** April 21, 2026  
**Status:** Phase 1 - Day 1 - Ready to Execute! 🚀
