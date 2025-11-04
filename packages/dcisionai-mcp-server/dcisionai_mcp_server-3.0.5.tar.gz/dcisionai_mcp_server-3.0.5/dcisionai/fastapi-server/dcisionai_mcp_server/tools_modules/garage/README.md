# Tools Garage

**Purpose:** Storage for non-primary, experimental, or deprecated tool implementations

**Date Created:** October 28, 2025

---

## 📦 Archived Files

### **Model Builders**

#### 1. `model_builder_old.py` (259 lines)
- **Original Name:** `model_builder.py`
- **Status:** ❌ **DEPRECATED** - Had syntax errors, replaced by FMCO
- **Date Archived:** October 28, 2025
- **Reason:** Multiple syntax errors, lower quality than FMCO
- **Issues:**
  - Indentation errors (line 34, 77)
  - Incomplete implementation
  - Not tested in production
- **Replacement:** FMCO-based `model_builder.py` (now primary)

#### 2. `fmco_model_builder_original.py` (928 lines)
- **Original Name:** `fmco_model_builder.py`
- **Status:** ✅ **BACKUP** - Original FMCO implementation
- **Date Archived:** October 28, 2025
- **Reason:** Promoted to primary `model_builder.py`
- **Quality Scores:**
  - Manufacturing: 82.5% (Grade B)
  - Finance: 76% (Grade C)
  - Retail: 60% (Grade D)
- **Note:** This is now the active `model_builder.py` in parent directory

---

### **Benchmarking & Testing**

#### 3. `model_benchmarker.py` (503 lines)
- **Status:** ⚠️ **EXPERIMENTAL** - Not actively used
- **Date Archived:** October 28, 2025
- **Purpose:** Model performance benchmarking and comparison
- **Reason:** Has API endpoint but not used by UI
- **Future Use:** May be useful for development/testing
- **Quality:** Well-structured code, comprehensive metrics

---

### **Narrative Generation**

#### 4. `business_narrative_generator.py` (262 lines)
- **Status:** ❌ **DEPRECATED** - Functionality moved
- **Date Archived:** October 28, 2025
- **Purpose:** Generate business narratives and stakeholder communication
- **Reason:** Functionality now in `explainability.py`
- **Note:** No longer imported anywhere in active code

---

### **Pre-Processing**

#### 5. `pre_intent_sanity_check.py` (174 lines)
- **Status:** ❌ **DEPRECATED** - Functionality moved
- **Date Archived:** October 28, 2025
- **Purpose:** Pre-intent validation and query filtering
- **Reason:** Functionality now in `SessionAwareOrchestrator`
- **Note:** Not imported in active code

---

### **FMCO Phase 2 Features (GPU/Pinecone Required)**

All Phase 2 FMCO features archived as they require GPU resources or Pinecone, and are not actively used by the UI.

#### 6. `fmco_benchmarking.py` (489 lines)
- **Status:** ⚠️ **DORMANT** - Requires GPU
- **Date Archived:** October 28, 2025
- **Purpose:** Benchmarking pipelines for optimization algorithms
- **Features:**
  - TSPLib, CVRPLIB, MIPLib dataset integration
  - Performance metrics (optimality gap, runtime)
  - Result visualization
- **Reason:** UI does not pass `fmco_features` parameter
- **Requirements:** GPU, TSPLib datasets
- **Note:** Can be re-enabled when GPU resources available

#### 7. `fmco_hyperparameter_tuning.py` (523 lines)
- **Status:** ⚠️ **DORMANT** - Requires GPU
- **Date Archived:** October 28, 2025
- **Purpose:** Automated hyperparameter optimization
- **Features:**
  - Bayesian Optimization
  - Random Search
  - Evolutionary Algorithms
- **Reason:** UI does not pass `fmco_features` parameter
- **Requirements:** GPU, scikit-optimize
- **Note:** Can be re-enabled when GPU resources available

#### 8. `fmco_llm_solvers.py` (484 lines)
- **Status:** ⚠️ **EXPERIMENTAL** - Not production-ready
- **Date Archived:** October 28, 2025
- **Purpose:** LLM-based optimization solvers
- **Features:**
  - Zero-shot prompting
  - Few-shot with examples
  - Chain-of-Thought reasoning
  - Iterative refinement
- **Reason:** Experimental, not used by production UI
- **Requirements:** LLM API access
- **Note:** Research feature, not validated for production

#### 9. `fmco_model_finetuning.py` (693 lines)
- **Status:** ⚠️ **DORMANT** - Requires GPU
- **Date Archived:** October 28, 2025
- **Purpose:** Fine-tune models for specific CO problems
- **Features:**
  - LoRA (Low-Rank Adaptation)
  - Adapter-based fine-tuning
  - Domain-specific customization
- **Reason:** UI does not pass `fmco_features` parameter
- **Requirements:** GPU, CUDA, PyTorch
- **Note:** Can be re-enabled when GPU resources available

#### 10. `fmco_multitask.py` (512 lines)
- **Status:** ⚠️ **DORMANT** - Requires GPU
- **Date Archived:** October 28, 2025
- **Purpose:** Multi-task learning for CO problems
- **Features:**
  - Shared encoder architecture
  - Task-specific heads
  - Cross-domain learning
- **Reason:** UI does not pass `fmco_features` parameter
- **Requirements:** GPU, CUDA, PyTorch
- **Note:** Can be re-enabled when GPU resources available

#### 11. `fmco_paper_integration.py` (482 lines)
- **Status:** ⚠️ **DORMANT** - Requires Pinecone
- **Date Archived:** October 28, 2025
- **Purpose:** Integrate latest FMCO research papers
- **Features:**
  - ArXiv paper fetching
  - Automated summarization
  - Knowledge base updates
- **Reason:** UI does not pass `fmco_features` parameter
- **Requirements:** Pinecone API key, ArXiv API access
- **Note:** Used in `SessionAwareOrchestrator._integrate_latest_papers()` but feature not enabled

#### 12. `fmco_resource_manager.py` (204 lines)
- **Status:** ⚠️ **DORMANT** - Feature detection only
- **Date Archived:** October 28, 2025
- **Purpose:** Manage GPU/Pinecone resource availability
- **Features:**
  - GPU detection (CUDA/MPS)
  - Pinecone connectivity check
  - Feature availability reporting
- **Reason:** UI does not pass `fmco_features` parameter
- **Note:** Used in `SessionAwareOrchestrator` but fmco_features never passed from UI

---

### **Solver Selection**

#### 13. `solver_selector.py` (475 lines) + `tools_modules/solver_selector.py` (86 lines)
- **Status:** ❌ **DEPRECATED** - No longer needed
- **Date Archived:** October 28, 2025
- **Purpose:** Intelligent solver selection based on problem type and size
- **Features:**
  - Multi-solver support (HiGHS, GLOP, GLPK, SCIP, PDLP, etc.)
  - Performance-based selection
  - Problem size heuristics
  - Fallback options
- **Reason:** DcisionAI now uses HiGHS as primary solver with OR-Tools as backup (hardcoded)
- **Why Deprecated:**
  - UI doesn't use solver selection
  - OptimizationSolver ignores solver_selection parameter
  - HiGHS is 6-7x faster than alternatives
  - Simplified architecture: one solver, one backup
- **Note:** Still exposed as MCP tool but not used by workflow orchestrator

---

## 🎯 Primary Tools (Active in Parent Directory)

### **Core Tools:**
1. ✅ **`model_builder.py`** - FMCO-based (promoted from garage) - 7.2/10 quality
2. ✅ **`intent_classifier.py`** - 9.5/10 quality
3. ✅ **`data_analyzer.py`** - 9.0/10 quality
4. ✅ **`optimization_solver.py`** - 8.5/10 quality (HiGHS primary, OR-Tools backup)
5. ✅ **`validation_tool.py`** - 8.5/10 quality
6. ✅ **`critique_tool.py`** - 8.0/10 quality
7. ✅ **`workflow_validator.py`** - 8.0/10 quality
8. ✅ **`explainability.py`** - 7.0/10 quality
9. ✅ **`simulation.py`** - 7.0/10 quality

---

## 📊 Model Builder Evolution

### **Timeline:**

```
Phase 1: Original model_builder.py
├── Issues: Syntax errors, incomplete
├── Status: Broken
└── Quality: 4.0/10

Phase 2: FMCO model_builder
├── Implementation: Foundation Models for CO patterns
├── Testing: Comprehensive quality tests
├── Scores: Manufacturing (82.5%), Finance (76%), Retail (60%)
└── Quality: 7.2/10 average

Phase 3: FMCO → Primary (October 28, 2025)
├── Promoted: fmco_model_builder.py → model_builder.py
├── Status: Active in production
└── Next: OptLLM enhancements planned
```

---

## 🔄 Restoration Instructions

If you need to restore any of these tools:

### **Restore Old Model Builder:**
```bash
# WARNING: Has syntax errors!
cp garage/model_builder_old.py ../model_builder.py
```

### **Restore FMCO Original:**
```bash
# Already active as primary model_builder.py
# This is just a backup
cp garage/fmco_model_builder_original.py ../model_builder.py
```

### **Restore Benchmarker:**
```bash
# Add back to active tools
cp garage/model_benchmarker.py ../model_benchmarker.py

# Update __init__.py
# Add: from .model_benchmarker import ModelBenchmarker
```

---

## 📝 Notes

### **Why FMCO Was Chosen:**

1. **Quality Test Results:**
   - Manufacturing: 82.5% (Best among core domains)
   - Finance: 76% (Good)
   - Retail: 60% (Needs improvement but functional)

2. **Features:**
   - Domain-specific adapters (Manufacturing, Retail, Finance)
   - Realistic variable naming (no x1, x2, x3)
   - FMCO patterns from latest research
   - Extensible architecture

3. **Comparison to Old Builder:**
   - Old: Syntax errors, not functional
   - FMCO: Tested, working, scored

### **Future Enhancements:**

See `docs/OPTLLM_ENHANCEMENT_PLAN.md` for planned improvements based on OptLLM research:
- Enhanced NL processing
- Intelligent constraint discovery
- Smart objective functions
- Code generation
- Interactive refinement

---

## 🗄️ Related Archives

- **Orchestrators:** `archive/obsolete_orchestrators/`
  - `tool_orchestrator.py` (legacy)
  - `workflow_orchestrator.py` (old Pinecone version)

- **AWS/Bedrock:** `archive/aws/bedrock/`
  - `bedrock_client.py` (not used, we use OpenAI/Anthropic)

- **FMCO Phase 2:** (Still in parent directory but inactive)
  - `fmco_model_finetuning.py` (GPU required)
  - `fmco_hyperparameter_tuning.py` (GPU required)
  - `fmco_multitask.py` (GPU required)
  - `fmco_benchmarking.py` (GPU required)
  - `fmco_paper_integration.py` (Pinecone required)
  - `fmco_llm_solvers.py` (experimental)
  - `fmco_resource_manager.py` (GPU management)

---

**Status:** 🗄️ Archived and Documented  
**Last Updated:** October 28, 2025  
**Maintainer:** DcisionAI Team

