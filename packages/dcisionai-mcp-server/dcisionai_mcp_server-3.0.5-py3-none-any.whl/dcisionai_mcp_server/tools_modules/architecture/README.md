# Tools Architecture Documentation

**Comprehensive architecture documentation for all DcisionAI optimization tools**

**Location:** `dcisionai/fastapi-server/dcisionai_mcp_server/tools_modules/architecture/`

This directory contains detailed architecture documentation for each tool, co-located with the actual tool implementation code.

---

## 📚 Start Here

**[TOOLS_ARCHITECTURE_INDEX.md](./TOOLS_ARCHITECTURE_INDEX.md)** - Master index with complete workflow visualization and all tool links

---

## 📖 Individual Tool Architectures

### Core Workflow Tools

1. **[Intent Classification Tool](./INTENT_TOOL_ARCHITECTURE.md)** ⭐ 9.5/10
   - Classifies business problems into optimization categories
   - Fine-tuned GPT-4o with narrative reasoning
   - 3-6 seconds, 95% accuracy

2. **[Data Analysis Tool](./DATA_TOOL_ARCHITECTURE.md)** ⭐ 9.0/10
   - Extracts entities and generates simulated data
   - 6-tier JSON parsing fallback
   - 5-10 seconds, robust error handling
   - **Additional Docs:**
     - [Deep Analysis](./DATA_TOOL_DEEP_ANALYSIS.md) - Full technical review
     - [Summary](./DATA_TOOL_SUMMARY.md) - Executive summary
     - [Quick Reference](./DATA_TOOL_QUICK_REFERENCE.md) - Cheat sheet

3. **[Model Builder Tool](./MODEL_BUILDER_ARCHITECTURE.md)** ⭐ 8.2/10
   - FMCO-based hybrid architecture
   - Domain-specific adapters
   - ~400ms, realistic variable naming

4. **[Optimization Solver Tool](./SOLVER_TOOL_ARCHITECTURE.md)** ⭐ 8.5/10
   - HiGHS primary (6-7x faster)
   - OR-Tools backup
   - 20-120ms, optimal solutions

### Coming Soon

5. **Explainability Tool** (Architecture doc in progress)
   - Business-friendly explanations
   - Key insights and recommendations

6. **Simulation Tool** (Architecture doc in progress)
   - Monte Carlo simulation
   - Sensitivity analysis

---

## 📂 Directory Structure

```
dcisionai/fastapi-server/dcisionai_mcp_server/tools_modules/
├── architecture/                        ← Architecture docs (you are here)
│   ├── README.md                        ← This file
│   ├── TOOLS_ARCHITECTURE_INDEX.md      ← Master index
│   │
│   ├── INTENT_TOOL_ARCHITECTURE.md      ← Step 1: Intent Classification
│   ├── DATA_TOOL_ARCHITECTURE.md        ← Step 2: Data Analysis
│   │   ├── DATA_TOOL_DEEP_ANALYSIS.md   ←   └─ Detailed analysis
│   │   ├── DATA_TOOL_SUMMARY.md         ←   └─ Executive summary
│   │   └── DATA_TOOL_QUICK_REFERENCE.md ←   └─ Quick reference
│   ├── MODEL_BUILDER_ARCHITECTURE.md    ← Step 3: Model Building
│   └── SOLVER_TOOL_ARCHITECTURE.md      ← Step 4: Optimization Solving
│
├── intent_classifier.py                 ← Step 1 implementation
├── data_analyzer.py                     ← Step 2 implementation
├── model_builder.py                     ← Step 3 implementation
├── optimization_solver.py               ← Step 4 implementation
├── explainability.py                    ← Step 5 implementation
├── simulation.py                        ← Step 6 implementation
│
├── garage/                              ← Archived tools
└── orchestrators/                       ← (parent directory)
```

**Co-located Design:** Architecture docs are now in the same directory tree as the tool implementations for easy reference.

---

## 🎯 What's Inside Each Architecture Doc

Every tool architecture document includes:

✅ **Visual Architecture Diagram** - ASCII art showing component hierarchy and data flow  
✅ **Key Components** - Main classes, methods, and architecture  
✅ **Data Flow Example** - Realistic JSON input/output examples  
✅ **Error Handling Strategy** - Provider cascades and fallback mechanisms  
✅ **Performance Characteristics** - Time breakdown and success rates  
✅ **Integration Points** - How the tool connects to others  
✅ **Quality Metrics** - Scores, strengths, and weaknesses  
✅ **Code Location** - File paths and line numbers  

---

## 📊 Quality Overview

| Tool | Score | Performance | Status |
|------|-------|-------------|--------|
| Intent Classification | 9.5/10 ⭐ | 3-6s | ✅ Production |
| Data Analysis | 9.0/10 ⭐ | 5-10s | ✅ Production |
| Optimization Solver | 8.5/10 ⭐ | 20-120ms | ✅ Production |
| Model Builder | 8.2/10 ⭐ | ~400ms | ✅ Production |
| **Platform Average** | **8.8/10** ⭐ | **10-20s** | **✅ Production** |

---

## 🔄 Complete Workflow Visualization

```
User Input (Natural Language)
        ↓
[Intent Classification] 3-6s ⭐ 9.5/10
        ↓
[Data Analysis] 5-10s ⭐ 9.0/10
        ↓
[Model Building] ~400ms ⭐ 8.2/10
        ↓
[Optimization Solving] 20-120ms ⭐ 8.5/10
        ↓
[Explainability] TBD
        ↓
[Simulation] TBD
        ↓
Final Results & Insights
```

**Total Time:** 10-20 seconds

---

## 🚀 Quick Links

- **[Master Index](./TOOLS_ARCHITECTURE_INDEX.md)** - Start here for complete overview
- **[Intent Tool](./INTENT_TOOL_ARCHITECTURE.md)** - Best quality (9.5/10)
- **[Data Tool Deep Dive](./DATA_TOOL_DEEP_ANALYSIS.md)** - Most detailed analysis
- **[Solver Tool](./SOLVER_TOOL_ARCHITECTURE.md)** - Fastest execution (20-120ms)

---

## 📝 Documentation Standards

All architecture docs follow a consistent format:
1. Visual architecture diagram (ASCII art)
2. Key components and features
3. Data flow with JSON examples
4. Error handling strategies
5. Performance characteristics
6. Integration points
7. Quality metrics and scoring
8. Code locations

---

## 🔧 Related Documentation

**Tool Implementations (parent directory):**
- `../intent_classifier.py` - Intent Classification implementation
- `../data_analyzer.py` - Data Analysis implementation
- `../model_builder.py` - Model Builder implementation (FMCO-based)
- `../optimization_solver.py` - Optimization Solver implementation
- `../explainability.py` - Explainability implementation
- `../simulation.py` - Simulation implementation

**Platform-Level (docs/):**
- `/docs/PLATFORM_OVERVIEW.md` - High-level platform description
- `/docs/Architecture.md` - Complete system architecture
- `/docs/API_REFERENCE.md` - API documentation

**Development:**
- `/docs/CODE_CLEANUP_TOOLS_ORGANIZATION.md` - Code organization
- `/docs/TOOLS_QUALITY_ANALYSIS.md` - Quality analysis

**Deployment:**
- `/docs/DEPLOYMENT_GUIDE.md` - Deployment instructions
- `/docs/QUICK_START.md` - Getting started guide

---

## 📅 Version History

**Intent v2.0** (October 29, 2025)
- Created comprehensive architecture docs for all core tools
- Added visual architecture diagrams
- Enhanced narrative reasoning in Intent tool
- Promoted FMCO model builder to primary
- Organized docs into `docs/architecture/tools/` directory

---

**Status:** ✅ Production-Ready  
**Last Updated:** October 29, 2025  
**Maintained By:** DcisionAI Team

