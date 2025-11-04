# DcisionAI Tools - Architecture Documentation Index

**Complete Architecture Reference for All Optimization Tools**

Version: Intent v2.0  
Last Updated: October 29, 2025

---

## 📚 Table of Contents

1. [Overview](#overview)
2. [Complete Workflow Architecture](#complete-workflow-architecture)
3. [Individual Tool Architectures](#individual-tool-architectures)
4. [Quality Scores Summary](#quality-scores-summary)
5. [Performance Comparison](#performance-comparison)
6. [Integration Matrix](#integration-matrix)
7. [Quick Reference](#quick-reference)

---

## Overview

DcisionAI uses a **6-step optimization workflow** powered by specialized tools. Each tool has comprehensive architecture documentation with:

- ✅ Visual architecture diagrams
- ✅ Data flow examples
- ✅ Error handling strategies
- ✅ Performance characteristics
- ✅ Integration points
- ✅ Quality metrics

---

## Complete Workflow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INPUT                                │
│  Natural language business problem description              │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: INTENT CLASSIFICATION  (3-6s)                     │
│  📄 Doc: INTENT_TOOL_ARCHITECTURE.md                        │
│  ⭐ Score: 9.5/10                                            │
│                                                             │
│  Classifies problem into optimization category             │
│  - intent, industry, use_case                              │
│  - confidence score                                         │
│  - 3-5 sentence narrative reasoning                        │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: DATA ANALYSIS  (5-10s)                            │
│  📄 Doc: DATA_TOOL_ARCHITECTURE.md                          │
│  ⭐ Score: 9.0/10                                            │
│                                                             │
│  Extracts entities, performs gap analysis, generates data  │
│  - variables (realistic names)                             │
│  - constraints (mathematical expressions)                  │
│  - objective (minimize/maximize)                           │
│  - parameters (numerical values)                           │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: MODEL BUILDING  (~400ms)                          │
│  📄 Doc: MODEL_BUILDER_ARCHITECTURE.md                      │
│  ⭐ Score: 8.2/10                                            │
│                                                             │
│  Builds mathematical optimization model                     │
│  - FMCO-based hybrid architecture                          │
│  - domain-specific adapters                                │
│  - realistic variable naming (82.5% quality)               │
│  - model specification for solver                          │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 4: OPTIMIZATION SOLVING  (20-120ms)                  │
│  📄 Doc: SOLVER_TOOL_ARCHITECTURE.md                        │
│  ⭐ Score: 8.5/10                                            │
│                                                             │
│  Solves mathematical model using HiGHS                      │
│  - HiGHS primary (6-7x faster)                             │
│  - OR-Tools backup                                         │
│  - optimal solutions guaranteed                            │
│  - variable values, objective value                        │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 5: EXPLAINABILITY  (TBD)                             │
│  📄 Doc: EXPLAINABILITY_TOOL_ARCHITECTURE.md               │
│  ⭐ Score: TBD                                               │
│                                                             │
│  Translates technical solution to business insights        │
│  - business-friendly explanations                          │
│  - key insights and recommendations                        │
│  - what-if analysis support                                │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 6: SIMULATION  (TBD)                                 │
│  📄 Doc: SIMULATION_TOOL_ARCHITECTURE.md                    │
│  ⭐ Score: TBD                                               │
│                                                             │
│  Simulates scenarios and risk analysis                     │
│  - monte carlo simulation                                  │
│  - sensitivity analysis                                    │
│  - risk assessment                                         │
└─────────────────────────────────────────────────────────────┘
```

**Total Workflow Time:** ~10-20 seconds (LLM-dominated)

---

## Individual Tool Architectures

### 1. Intent Classification Tool
**📄 Document:** [INTENT_TOOL_ARCHITECTURE.md](./INTENT_TOOL_ARCHITECTURE.md)

**Key Features:**
- Fine-tuned GPT-4o primary, Claude/GPT-4 fallback
- 3-5 sentence narrative reasoning (Intent v2.0)
- No Pinecone/KB dependency (simplified)
- 95% classification accuracy

**Quality Score:** ⭐ **9.5/10** (Highest quality tool)

**Performance:** 3-6 seconds

**Status:** ✅ Production-ready, industry-leading

---

### 2. Data Analysis Tool
**📄 Document:** [DATA_TOOL_ARCHITECTURE.md](./DATA_TOOL_ARCHITECTURE.md)

**Key Features:**
- Extracts entities from problem description
- Generates realistic simulated data
- 6-tier JSON parsing fallback
- Intent-aware data generation

**Quality Score:** ⭐ **9.0/10** (High quality)

**Performance:** 5-10 seconds

**Status:** ✅ Production-ready, needs validation improvements

**Related Docs:**
- [DATA_TOOL_DEEP_ANALYSIS.md](./DATA_TOOL_DEEP_ANALYSIS.md) - Full technical review
- [DATA_TOOL_SUMMARY.md](./DATA_TOOL_SUMMARY.md) - Executive summary
- [DATA_TOOL_QUICK_REFERENCE.md](./DATA_TOOL_QUICK_REFERENCE.md) - Cheat sheet

---

### 3. Model Builder Tool
**📄 Document:** [MODEL_BUILDER_ARCHITECTURE.md](./MODEL_BUILDER_ARCHITECTURE.md)

**Key Features:**
- FMCO-based hybrid architecture
- Domain adapters (manufacturing, finance, retail)
- Realistic variable naming (82.5% quality)
- Fast CPU-only execution (~400ms)

**Quality Score:** ⭐ **8.2/10** (Strong, room for improvement)

**Performance:** ~400ms (CPU-bound, fast!)

**Status:** ✅ Production-ready, promoted from fmco_model_builder in Intent v2.0

**Related Docs:**
- [OPTLLM_ENHANCEMENT_PLAN.md](../../OPTLLM_ENHANCEMENT_PLAN.md) - Planned improvements

---

### 4. Optimization Solver Tool
**📄 Document:** [SOLVER_TOOL_ARCHITECTURE.md](./SOLVER_TOOL_ARCHITECTURE.md)

**Key Features:**
- HiGHS primary solver (6-7x faster than OR-Tools)
- Solver selection deprecated (hardcoded HiGHS)
- Optimal solutions guaranteed
- Fast solve times (< 100ms typically)

**Quality Score:** ⭐ **8.5/10** (Fast and reliable)

**Performance:** 20-120ms (problem-dependent)

**Status:** ✅ Production-ready, optimized in Intent v2.0

---

### 5. Explainability Tool
**📄 Document:** EXPLAINABILITY_TOOL_ARCHITECTURE.md *(Coming soon)*

**Key Features:**
- Business-friendly explanations
- Key insights and recommendations
- What-if analysis support

**Quality Score:** ⭐ **TBD**

**Performance:** TBD

**Status:** ⏳ Needs deep review

---

### 6. Simulation Tool
**📄 Document:** SIMULATION_TOOL_ARCHITECTURE.md *(Coming soon)*

**Key Features:**
- Monte Carlo simulation
- Sensitivity analysis
- Risk assessment

**Quality Score:** ⭐ **TBD**

**Performance:** TBD

**Status:** ⏳ Needs deep review

---

## Quality Scores Summary

| Tool | Score | Status | Key Strength | Key Weakness |
|------|-------|--------|--------------|--------------|
| **Intent Classification** | 9.5/10 ⭐ | Production | Narrative reasoning, accuracy | None significant |
| **Data Analysis** | 9.0/10 ⭐ | Production | Robust parsing, intent-aware | Needs validation |
| **Optimization Solver** | 8.5/10 ⭐ | Production | Fast (HiGHS), reliable | Limited features |
| **Model Builder** | 8.2/10 ⭐ | Production | FMCO-based, realistic vars | Retail domain weak |
| **Explainability** | TBD | Needs review | Business insights | Not yet reviewed |
| **Simulation** | TBD | Needs review | Risk analysis | Not yet reviewed |

**Overall Platform Quality:** **8.8/10** ⭐ (Based on reviewed tools)

---

## Performance Comparison

### Time Breakdown

```
STEP 1: Intent Classification    3-6s     ████████████░░░░░░░░  (30-40%)
STEP 2: Data Analysis            5-10s    ████████████████████  (40-50%)
STEP 3: Model Building          ~400ms    █░░░░░░░░░░░░░░░░░░░  (2-3%)
STEP 4: Optimization Solving  20-120ms    █░░░░░░░░░░░░░░░░░░░  (1-2%)
STEP 5: Explainability            TBD     ░░░░░░░░░░░░░░░░░░░░  (TBD)
STEP 6: Simulation                TBD     ░░░░░░░░░░░░░░░░░░░░  (TBD)

TOTAL WORKFLOW TIME:            10-20s    ████████████████████  (100%)
```

**Bottleneck:** LLM calls (Intent & Data steps)

**Fast Steps:** Model building and solving (< 1s combined!)

---

## Integration Matrix

```
┌──────────────┬─────────┬──────────┬───────────┬─────────┐
│ Tool         │ Input   │ Provider │ Output    │ Consumer│
│              │ From    │ (LLM)    │ To        │ UI      │
├──────────────┼─────────┼──────────┼───────────┼─────────┤
│ Intent       │ UI      │ GPT-4o   │ Data      │ ✅      │
│ Classifier   │         │ Claude   │           │         │
├──────────────┼─────────┼──────────┼───────────┼─────────┤
│ Data         │ Intent  │ GPT-4o   │ Model     │ ✅      │
│ Analyzer     │         │ Claude   │ Builder   │         │
├──────────────┼─────────┼──────────┼───────────┼─────────┤
│ Model        │ Data    │ None     │ Solver    │ ✅      │
│ Builder      │         │ (CPU)    │           │         │
├──────────────┼─────────┼──────────┼───────────┼─────────┤
│ Optimization │ Model   │ None     │ Explain   │ ✅      │
│ Solver       │         │ (HiGHS)  │           │         │
├──────────────┼─────────┼──────────┼───────────┼─────────┤
│ Explain      │ Solver  │ GPT-4?   │ Sim       │ ✅      │
│              │         │          │           │         │
├──────────────┼─────────┼──────────┼───────────┼─────────┤
│ Simulation   │ Solver  │ None?    │ UI        │ ✅      │
│              │ Explain │          │           │         │
└──────────────┴─────────┴──────────┴───────────┴─────────┘
```

---

## Quick Reference

### By Performance
1. **Fastest:** Model Builder (~400ms)
2. **Fast:** Solver (20-120ms)
3. **Medium:** Intent (3-6s)
4. **Slower:** Data Analysis (5-10s)

### By Quality
1. **Best:** Intent Classification (9.5/10)
2. **Excellent:** Data Analysis (9.0/10)
3. **Very Good:** Solver (8.5/10)
4. **Good:** Model Builder (8.2/10)

### By Complexity
1. **Most Complex:** Model Builder (FMCO, domain adapters)
2. **Complex:** Data Analysis (JSON parsing, gap analysis)
3. **Moderate:** Intent Classification (classification + reasoning)
4. **Simple:** Solver (standard optimization)

### By Dependencies
1. **No Dependencies:** Model Builder (CPU-only)
2. **Solver Only:** Optimization Solver (HiGHS/OR-Tools)
3. **LLM Required:** Intent, Data, Explain (GPT-4o/Claude)

---

## Documentation Standards

Each tool architecture document includes:

### 1. Visual Architecture Diagram
- Component hierarchy
- Data flow arrows
- LLM provider cascade
- Error handling paths

### 2. Key Components Section
- Main classes and methods
- Architecture overview
- Process description

### 3. Data Flow Example
- Input format (JSON)
- Processing steps
- Output format (JSON)

### 4. Error Handling Strategy
- Provider/parser cascade
- Fallback mechanisms
- Error recovery

### 5. Performance Characteristics
- Time breakdown
- Success rates
- Problem size scaling

### 6. Integration Points
- Input sources
- Output consumers
- UI display elements

### 7. Quality Metrics
- Score breakdown
- Strengths and weaknesses
- Comparison with alternatives

### 8. Code Location
- File paths
- Key methods
- Line numbers

---

## Contributing to Documentation

When adding new tool documentation, follow this template:

1. **Copy** an existing architecture document (e.g., `DATA_TOOL_ARCHITECTURE.md`)
2. **Update** all sections with tool-specific details
3. **Create** visual ASCII architecture diagram
4. **Include** data flow examples with realistic JSON
5. **Document** error handling and fallback strategies
6. **Add** performance metrics and quality scores
7. **Link** from this index document

---

## Related Documentation

### Platform Overview
- [`PLATFORM_OVERVIEW.md`](./PLATFORM_OVERVIEW.md) - High-level platform description
- [`Architecture.md`](./Architecture.md) - Complete system architecture
- [`CUSTOMER_PLATFORM_OVERVIEW.md`](./CUSTOMER_PLATFORM_OVERVIEW.md) - Customer-facing overview

### Development Docs
- [`CODE_CLEANUP_TOOLS_ORGANIZATION.md`](./CODE_CLEANUP_TOOLS_ORGANIZATION.md) - Code organization
- [`TOOLS_QUALITY_ANALYSIS.md`](./TOOLS_QUALITY_ANALYSIS.md) - Quality analysis
- [`CODE_ANALYSIS_FASTAPI_SERVER.md`](./CODE_ANALYSIS_FASTAPI_SERVER.md) - FastAPI analysis

### API Reference
- [`API_REFERENCE.md`](./API_REFERENCE.md) - Complete API documentation

### Deployment
- [`DEPLOYMENT_GUIDE.md`](./DEPLOYMENT_GUIDE.md) - Deployment instructions
- [`QUICK_START.md`](./QUICK_START.md) - Getting started guide

---

## Status & Roadmap

### ✅ Completed (Intent v2.0)
- Intent Classification architecture ✅
- Data Analysis architecture ✅
- Model Builder architecture ✅
- Optimization Solver architecture ✅

### ⏳ In Progress
- Explainability Tool architecture
- Simulation Tool architecture

### 🔮 Future
- Advanced FMCO features documentation
- Multi-objective optimization
- Real-time optimization workflows
- Knowledge base integration

---

## Version History

**Intent v2.0** (October 29, 2025)
- Added comprehensive architecture diagrams for all core tools
- Enhanced narrative reasoning in Intent tool
- Promoted FMCO model builder to primary
- Deprecated solver selection (HiGHS hardcoded)
- Created complete documentation index

**Intent v1.5** (Previous)
- Initial tool documentation
- Code quality analysis
- Platform overview

---

## Contact & Support

**Documentation Maintained By:** DcisionAI Team  
**Last Review:** October 29, 2025  
**Next Review:** TBD  

For questions or improvements, see:
- Platform documentation in `docs/` folder
- Code comments in `dcisionai/fastapi-server/dcisionai_mcp_server/`
- GitHub issues and pull requests

---

**📊 Overall Platform Quality: 8.8/10** ⭐

**🚀 Status: Production-Ready** ✅

**📈 Next: Complete remaining tool architecture docs**

