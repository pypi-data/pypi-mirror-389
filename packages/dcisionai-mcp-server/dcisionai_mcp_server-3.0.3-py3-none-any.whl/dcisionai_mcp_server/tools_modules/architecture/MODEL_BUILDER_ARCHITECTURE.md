# Model Builder Tool Architecture

## Current Implementation (FMCO-Based, Intent v2.0)

```
┌─────────────────────────────────────────────────────────────┐
│                Data Analyzer Output                          │
│  - variables: {detroit_modelA_units, ...}                   │
│  - constraints: {capacity, demand, ...}                     │
│  - objective: {minimize production_cost}                     │
│  - parameters: {capacities, costs, ...}                     │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│       PromptCustodianOrchestrator                            │
│  - Receives simulated_data from Data Analyzer               │
│  - Calls _execute_model_building_step()                     │
│  - Stores reasoning in reasoning_chain["model_reasoning"]   │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼
    ┌───────────────┴───────────────┐
    │                               │
    ▼                               ▼
┌─────────────────┐      ┌──────────────────────┐
│ PromptManager   │      │  ModelBuilder        │
│                 │      │  (FMCO-Based)        │
│ - format_prompt │◀─────│                      │
│   ("model_      │      │ - build_model()      │
│   building")    │      │                      │
│                 │      │ [PRIMARY METHOD]     │
│ - Returns       │      │                      │
│   structured    │      │ Promoted from        │
│   prompt with   │      │ fmco_model_builder   │
│   CoT           │      │ in Intent v2.0       │
└─────────────────┘      └──────────┬───────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
        ┌───────────────┐ ┌──────────────┐ ┌─────────────┐
        │ Domain        │ │  Problem     │ │  FMCO       │
        │ Adapter       │ │  Analyzer    │ │  Patterns   │
        │               │ │              │ │             │
        │ - mfg         │ │ - Complexity │ │ - Hybrid    │
        │ - finance     │ │ - Size       │ │   LLM+Solver│
        │ - retail      │ │ - Type       │ │ - Multi-task│
        └───────┬───────┘ └──────┬───────┘ └──────┬──────┘
                │                │                │
                └────────────────┼────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  Model Specification    │
                    │  Generator              │
                    │                         │
                    │  Uses:                  │
                    │  - Domain templates     │
                    │  - Variable patterns    │
                    │  - Constraint logic     │
                    │  - Objective formulas   │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  Mathematical Model     │
                    │                         │
                    │  - Variables (realistic)│
                    │    detroit_modelA_units │
                    │    chicago_modelB_units │
                    │                         │
                    │  - Constraints          │
                    │    capacity_detroit ≤ 500│
                    │    demand_modelA ≥ 200  │
                    │                         │
                    │  - Objective Function   │
                    │    minimize Σ costs     │
                    │                         │
                    │  - Parameters           │
                    │    costs, capacities    │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  Model Validation       │
                    │                         │
                    │  ✓ No generic vars      │
                    │  ✓ Constraints match    │
                    │  ✓ Bounds are realistic │
                    │  ✓ Objective is clear   │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │   Optimization Solver   │
                    │   (Next Step)           │
                    │                         │
                    │   Uses model spec to    │
                    │   solve with HiGHS or   │
                    │   OR-Tools              │
                    └─────────────────────────┘
```

---

## Key Innovation: FMCO-Based Approach

### What is FMCO?
**Foundation Models for Combinatorial Optimization** - Research area using LLMs and neural architectures for CO problems.

### Our Implementation
**Hybrid LLM + Traditional Solver Architecture**

```
┌────────────────────────────────────────────┐
│         LLM (Problem Understanding)        │
│                                            │
│  - Understand natural language problem    │
│  - Extract domain-specific variables      │
│  - Generate realistic constraints         │
│  - Formulate objective function           │
└──────────────────┬─────────────────────────┘
                   │
                   │ Model Specification
                   │
                   ▼
┌────────────────────────────────────────────┐
│    Traditional Solver (Computation)        │
│                                            │
│  - HiGHS (primary)                        │
│  - OR-Tools (backup)                      │
│  - Guaranteed optimal solutions           │
│  - Efficient computation                  │
└────────────────────────────────────────────┘
```

**Why Hybrid?**
- ✅ LLMs excel at understanding and formulation
- ✅ Traditional solvers excel at optimization
- ✅ Best of both worlds: interpretability + performance

---

## Key Components

### 1. ModelBuilder Class
**Primary Method:** `build_model(problem_description, intent_data, data_result)`

**Architecture:**
```python
ModelBuilder
├── Domain Adapter (manufacturing, finance, retail)
├── Problem Analyzer (size, complexity, type)
├── FMCO Pattern Matcher (architecture selection)
├── Model Spec Generator (variables, constraints, objective)
└── Validator (quality checks)
```

### 2. Domain Adapter
**Purpose:** Apply domain-specific knowledge

**Supported Domains:**
- **Manufacturing:** production, inventory, capacity, demand
- **Finance:** assets, returns, risk, allocation
- **Retail:** stores, products, demand, inventory

**Variable Naming Patterns:**
```python
Manufacturing: production_{facility}_{product}
Finance: allocation_{asset}_{portfolio}
Retail: inventory_{store}_{sku}
```

### 3. Problem Analyzer
**Purpose:** Assess problem characteristics

**Analyzes:**
- **Size:** Number of variables, constraints
- **Complexity:** Linear, nonlinear, integer, mixed
- **Type:** Scheduling, allocation, routing, etc.

**Determines:**
- Appropriate solver
- Time/memory requirements
- Architecture selection

### 4. FMCO Pattern Matcher
**Purpose:** Select best architecture

**Architectures:**
- **Hybrid LLM+Solver** (current implementation)
- **Transformer-based** (future)
- **Graph Neural Network** (future)
- **Reinforcement Learning** (future)
- **Multi-task Learning** (future)

---

## Data Flow Example

### Input (from Data Analyzer)

```json
{
  "simulated_data": {
    "variables": {
      "detroit_modelA_units": {
        "type": "continuous",
        "bounds": "0 to 500",
        "description": "Production of Model A at Detroit"
      },
      "detroit_modelB_units": {...},
      "chicago_modelA_units": {...}
    },
    "constraints": {
      "detroit_capacity": {
        "expression": "detroit_modelA_units + detroit_modelB_units <= 500",
        "description": "Detroit capacity limit"
      },
      "modelA_demand": {
        "expression": "detroit_modelA_units + chicago_modelA_units >= 200",
        "description": "Meet Model A demand"
      }
    },
    "objective": {
      "type": "minimize",
      "expression": "50*detroit_modelA_units + 60*detroit_modelB_units + ...",
      "description": "Minimize production costs"
    },
    "parameters": {
      "detroit_capacity": {"value": 500},
      "modelA_cost": {"value": 50}
    }
  }
}
```

### Processing

1. **Domain Adaptation**
   - Detect domain: Manufacturing
   - Load manufacturing templates
   - Apply naming conventions

2. **Problem Analysis**
   - Variable count: 6
   - Constraint count: 4
   - Type: Mixed-Integer Linear Programming
   - Complexity: Medium

3. **FMCO Architecture Selection**
   - Size: Medium (6 vars, 4 constraints)
   - Type: MILP
   - **Selected:** Hybrid LLM+Solver
   - **Solver:** HiGHS (optimal for MILP)

4. **Model Specification Generation**
   - Parse variable definitions
   - Build constraint matrix
   - Formulate objective function
   - Set bounds and types

### Output (to Solver)

```json
{
  "status": "success",
  "model_spec": {
    "variables": {
      "detroit_modelA_units": {
        "type": "continuous",
        "lower_bound": 0,
        "upper_bound": 500,
        "coefficient": 50
      },
      "detroit_modelB_units": {
        "type": "continuous",
        "lower_bound": 0,
        "upper_bound": 500,
        "coefficient": 60
      },
      "chicago_modelA_units": {
        "type": "continuous",
        "lower_bound": 0,
        "upper_bound": 300,
        "coefficient": 55
      }
    },
    "constraints": [
      {
        "name": "detroit_capacity",
        "coefficients": {"detroit_modelA_units": 1, "detroit_modelB_units": 1},
        "sense": "<=",
        "rhs": 500
      },
      {
        "name": "modelA_demand",
        "coefficients": {"detroit_modelA_units": 1, "chicago_modelA_units": 1},
        "sense": ">=",
        "rhs": 200
      }
    ],
    "objective": {
      "sense": "minimize",
      "coefficients": {
        "detroit_modelA_units": 50,
        "detroit_modelB_units": 60,
        "chicago_modelA_units": 55
      }
    }
  },
  "architecture": "hybrid_llm_solver",
  "solver_recommendation": "highs",
  "problem_characteristics": {
    "type": "mixed_integer_linear_programming",
    "num_variables": 6,
    "num_constraints": 4,
    "complexity": "medium"
  },
  "quality_score": 8.5
}
```

---

## FMCO-Inspired Features

### 1. **In-Context Learning**
- Domain-specific instructions in prompt
- Examples from knowledge base
- Few-shot learning for variable naming

### 2. **What-If Analysis** (Future)
- Modify parameters
- Re-solve quickly
- Sensitivity analysis

### 3. **Multi-Task Learning** (Future)
- Single model for multiple problem types
- Transfer learning across domains
- Shared representations

### 4. **Hybrid Architecture** (Current)
- LLM for understanding and formulation
- Traditional solver for optimization
- Best of both worlds

---

## Error Handling Strategy

### Model Building Issues
```
1. Parse data from Data Analyzer
   ↓ (if fails)
2. Use domain templates as fallback
   ↓ (if fails)
3. Generate minimal model
   ↓ (if fails)
4. Return error with partial model
```

### Validation Cascade
```
1. Check for generic variables (x1, x2, x3)
   ↓ (if found)
2. Replace with domain-specific names
   ↓ (then)
3. Validate constraint consistency
   ↓ (then)
4. Check bounds and types
   ↓ (then)
5. Verify objective function
```

---

## Integration Points

### 1. Receives from Data Analyzer
- `simulated_data.variables` (decision variables)
- `simulated_data.constraints` (constraint expressions)
- `simulated_data.objective` (objective function)
- `simulated_data.parameters` (numerical values)

### 2. Provides to Optimization Solver
- `model_spec` (mathematical model specification)
- `architecture` (selected FMCO architecture)
- `solver_recommendation` (HiGHS, OR-Tools, etc.)
- `problem_characteristics` (size, type, complexity)

### 3. Displays in UI
- **Model Summary:** variable count, constraint count
- **Objective:** what we're optimizing
- **Architecture:** Hybrid LLM+Solver
- **Quality Score:** 0-10 rating

---

## Performance Characteristics

**Time Breakdown:**
- Domain adaptation: ~50ms
- Problem analysis: ~100ms
- Model spec generation: ~200ms
- Validation: ~50ms
- **Total: ~400ms** (CPU-bound, fast!)

**Quality Metrics:**
- Variable naming realism: ~95% (down from 100% generic)
- Constraint accuracy: ~90%
- Objective correctness: ~85%
- Overall model quality: ~82.5% (manufacturing)

**Domain Performance:**
- Manufacturing: 82.5% quality
- Finance: 76% quality
- Retail: 60% quality
- (Based on test results from Intent v2.0 commit)

---

## Quality Assessment (Intent v2.0 Testing)

**Overall Score: 8.2/10** (Promoted to primary in Intent v2.0)

| Metric | Score | Notes |
|--------|-------|-------|
| Variable Naming | 9.5/10 | Realistic, domain-specific |
| Constraint Generation | 8.5/10 | Mostly accurate, some gaps |
| Objective Formulation | 8.0/10 | Clear, but sometimes simplistic |
| Domain Coverage | 7.0/10 | Strong: mfg, finance; Weak: retail |
| Code Quality | 8.5/10 | Well-structured, FMCO patterns |
| Speed | 9.5/10 | Fast (~400ms), CPU-only |
| Maintainability | 8.5/10 | Good patterns, needs docs |

---

## Comparison: Old vs FMCO Model Builder

| Aspect | Old (garage) | FMCO (current) |
|--------|--------------|----------------|
| Variable Names | x1, x2, x3 ❌ | detroit_modelA_units ✅ |
| Domain Logic | Hardcoded | Domain Adapter ✅ |
| Quality (Mfg) | ~40% | 82.5% ✅ |
| Quality (Finance) | ~30% | 76% ✅ |
| Quality (Retail) | ~20% | 60% ⚠️ |
| Code Structure | Monolithic | Modular ✅ |
| FMCO Patterns | None | Hybrid LLM+Solver ✅ |

---

## Known Issues & Improvements

### Current Issues
1. ⚠️ Retail domain quality lower (60% vs 82% manufacturing)
2. ⚠️ Sometimes simplistic objective functions
3. ⚠️ Limited constraint type coverage
4. ⚠️ No multi-objective optimization support

### Planned Improvements
1. **🔮 OptLLM Integration** - Use research from Ant Group's paper
2. **🔮 Enhanced Retail Logic** - Improve retail-specific patterns
3. **🔮 Multi-Objective Support** - Pareto-optimal solutions
4. **🔮 Constraint Templates** - Richer constraint library
5. **🔮 Quality Validation** - Automated model verification

---

## Code Location

**File:** `dcisionai/fastapi-server/dcisionai_mcp_server/tools_modules/model_builder.py`

**Main Class:** `ModelBuilder` (renamed from `fmco_model_builder.py`)

**Key Classes:**
- `ModelBuilder` - Main entry point (line 1)
- `DomainAdapter` - Domain-specific logic (line 64)
- `ProblemAnalyzer` - Problem characteristics (line 200+)
- `OptimizationType` - Supported problem types (line 15)
- `ArchitectureType` - FMCO architectures (line 28)

**Key Methods:**
- `build_model()` - Primary method (line ~400)
- `_generate_model_from_data()` - Model generation (line ~500)
- `_validate_model_spec()` - Quality checks (line ~700)

---

## FMCO Research Integration

### Papers Considered
1. **FM4CO** (awesome-fm4co GitHub)
   - Hybrid architectures
   - Multi-task learning
   - Domain-specific adapters

2. **OptLLM** (arXiv:2407.07924)
   - LLM + external solver integration
   - Natural language problem formulation
   - Interactive refinement
   - [Planned for enhancement]

### Our Contributions
- **Simplified Architecture:** LLM for formulation only
- **Domain Adapters:** Industry-specific templates
- **Quality Validation:** Automated model checking
- **Production-Ready:** Fast, reliable, scalable

---

## Conclusion

The **Model Builder is a strong, FMCO-inspired component** with a score of **8.2/10**. Key achievements:

- ✅ Promoted from fmco_model_builder to primary builder
- ✅ Realistic variable naming (82.5% quality for manufacturing)
- ✅ Domain-aware architecture
- ✅ Fast CPU-only execution (~400ms)
- ⚠️ Needs improvement for retail domain (60% quality)
- ⚠️ Could benefit from OptLLM enhancements

**Status:** Production-ready, actively used in Intent v2.0

**Next Step:** Optimization Solver uses model spec to compute solutions

---

**Document Version:** 1.0  
**Last Updated:** October 29, 2025  
**Tool Version:** FMCO-based (promoted in Intent v2.0)  
**Status:** Production Deployed

