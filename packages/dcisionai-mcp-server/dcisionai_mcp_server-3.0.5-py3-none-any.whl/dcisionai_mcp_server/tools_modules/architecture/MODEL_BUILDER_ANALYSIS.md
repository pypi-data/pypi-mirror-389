# Model Builder - Deep Analysis & Research

**Date:** October 29, 2025  
**Status:** Critical Review  
**Current Version:** FMCO-based (promoted in Intent v2.0)

---

## 🚨 Critical Issue Discovered

### **Problem: Model Builder Ignores Data Analyzer Output**

```python
async def build_model(self, problem_description: str, intent_data: Dict[str, Any], data_result: Dict[str, Any]):
    # ❌ data_result parameter is received but NEVER USED!
    
    # Instead, it generates its own data:
    variables = adapter.generate_realistic_variables(problem_size)  # ← Generates new!
    constraints = adapter.generate_realistic_constraints(problem_size)  # ← Generates new!
    objective = adapter.generate_realistic_objective()  # ← Generates new!
```

**Impact:**
- Data Analyzer generates variables: `FactoryA_Product1`, `FactoryB_Product2`
- Model Builder ignores them and generates: `production_Facility1_SKU1`, `production_Facility2_SKU2`
- **Result:** Mismatch between Data and Model steps!

---

## Current Architecture

### File Structure
```
model_builder.py (934 lines)
├── OptimizationType (Enum)
├── ArchitectureType (Enum)
├── ProblemConfig (Dataclass)
├── ModelConfig (Dataclass)
├── SolverConfig (Dataclass)
├── DomainAdapter (Class) - Domain-specific templates
├── ArchitectureSelector (Class) - FMCO architecture selection
└── ModelBuilder (Class) - Main model builder
```

### Key Components

#### 1. **DomainAdapter** (Lines 64-442)
**Purpose:** Generate domain-specific variables, constraints, objectives

**Domains Supported:**
- Manufacturing
- Retail
- Finance
- Healthcare
- Logistics
- Energy
- Supply Chain

**Methods:**
- `_get_variable_templates()` - Domain-specific variable naming patterns
- `_get_constraint_templates()` - Domain-specific constraint types
- `_get_objective_templates()` - Domain-specific objectives
- `generate_realistic_variables()` - Generate variables from templates
- `generate_realistic_constraints()` - Generate constraints from templates
- `generate_realistic_objective()` - Generate objective from templates

**Variable Templates (Manufacturing Example):**
```python
"production_{facility}_{product}",
"inventory_{facility}_{sku}",
"capacity_{facility}",
"demand_{customer}_{sku}",
"setup_{facility}_{product}",
"overtime_{facility}",
"backorder_{customer}_{sku}"
```

#### 2. **ArchitectureSelector** (Lines 443-574)
**Purpose:** Select optimal FMCO architecture based on problem characteristics

**Architectures:**
- TRANSFORMER_BASED - For sequence-based problems
- GRAPH_NEURAL_NETWORK - For graph-structured problems
- REINFORCEMENT_LEARNING - For dynamic decision-making
- HYBRID_LLM_SOLVER - For complex reasoning + optimization
- MULTI_TASK_LEARNING - For related problem families

**Selection Logic:**
```python
def select_architecture(self, problem_config: ProblemConfig) -> ArchitectureType:
    num_vars = problem_config.complexity_indicators.get("num_variables", 0)
    
    if num_vars > 1000:
        return ArchitectureType.GRAPH_NEURAL_NETWORK
    elif "routing" in problem_config.problem_type.value:
        return ArchitectureType.REINFORCEMENT_LEARNING
    else:
        return ArchitectureType.HYBRID_LLM_SOLVER  # Default
```

#### 3. **ModelBuilder** (Lines 575-935)
**Purpose:** Main orchestrator for model building

**Methods:**
- `build_model()` - Primary entry point
- `_get_domain_adapter()` - Get adapter for domain
- `_determine_optimization_type()` - Classify optimization problem
- `_estimate_problem_size()` - Estimate variables/constraints count
- `_generate_solver_config()` - Generate solver configuration
- `_generate_code_templates()` - Generate PyTorch/RL4CO code

**Current Flow:**
```
1. Extract domain from intent_data
2. Determine optimization type
3. Get domain adapter
4. Estimate problem size
5. Generate variables (❌ ignores data_result)
6. Generate constraints (❌ ignores data_result)
7. Generate objective (❌ ignores data_result)
8. Select FMCO architecture
9. Generate solver config
10. Generate code templates
11. Return model specification
```

---

## Quality Assessment

### Strengths ✅

1. **FMCO-Inspired Architecture**
   - Implements hybrid LLM + traditional solver approach
   - Multiple architecture types supported
   - Domain adapters for industry-specific patterns

2. **Domain-Specific Templates**
   - Manufacturing: production, inventory, capacity
   - Finance: investment, portfolio, risk
   - Retail: stock, reorder, demand
   - Good variable naming patterns

3. **Architecture Selection Logic**
   - Problem size-aware
   - Domain-aware
   - Complexity-aware

4. **Code Generation**
   - PyTorch model templates
   - RL4CO integration templates
   - Solver configuration

### Weaknesses ⚠️

1. **❌ CRITICAL: Ignores Data Analyzer Output**
   - `data_result` parameter unused
   - Regenerates all variables/constraints
   - Creates mismatch in workflow

2. **Domain Detection Issues**
   - Uses `intent_data.get("domain")` but intent returns "industry"
   - Fallback to "manufacturing" may be incorrect

3. **Problem Size Estimation**
   - Uses regex parsing of problem description
   - Fragile, error-prone
   - Should use data_result counts instead

4. **No Variable Validation**
   - Doesn't check if variables are realistic
   - No validation against data_result
   - Can generate generic variables

5. **Hardcoded Logic**
   - Fixed problem size estimates
   - Hardcoded template selection
   - Not data-driven

6. **No LLM Usage**
   - Pure template-based generation
   - No intelligent adaptation
   - Limited flexibility

---

## Test Results (from Intent v2.0)

### Manufacturing Domain
```
Quality Score: 82.5%
Variables Generated: Realistic (production_X_Y pattern)
Constraints: Basic (capacity, demand)
Issue: Ignores data_result variables
```

### Finance Domain
```
Quality Score: 76%
Variables Generated: Realistic (investment_X pattern)
Constraints: Portfolio-specific
Issue: Ignores data_result variables
```

### Retail Domain
```
Quality Score: 60%
Variables Generated: Less realistic
Constraints: Generic
Issue: Weaker domain support + ignores data_result
```

---

## Integration Analysis

### Current Workflow
```
Step 1: Intent Classification
   ↓
   intent: "manufacturing_production_planning"
   industry: "MANUFACTURING"
   
Step 2: Data Analysis
   ↓
   variables: {
     "FactoryA_Product1": {...},
     "FactoryB_Product2": {...}
   }
   
Step 3: Model Building  ❌ BROKEN
   ↓
   ❌ Ignores data_result
   ❌ Regenerates variables: {
     "production_Facility1_SKU1": {...},
     "production_Facility2_SKU2": {...}
   }
```

**Result:** Variable mismatch between Data and Model steps!

### Expected Workflow
```
Step 1: Intent Classification
   ↓
Step 2: Data Analysis
   ↓
   variables: {
     "FactoryA_Product1": {...}
   }
   ↓
Step 3: Model Building  ✅ SHOULD USE DATA
   ↓
   ✅ Uses data_result.simulated_data.variables
   ✅ Adds domain-specific metadata
   ✅ Validates variable naming
   ✅ Generates model specification
```

---

## Recommended Fixes

### Priority 1: Critical Fixes

#### 1. Use Data Analyzer Output
```python
async def build_model(self, problem_description: str, intent_data: Dict[str, Any], data_result: Dict[str, Any]):
    # ✅ Extract variables from data_result
    simulated_data = data_result.get('simulated_data', {})
    variables = simulated_data.get('variables', {})
    constraints = simulated_data.get('constraints', {})
    objective = simulated_data.get('objective', {})
    
    # ✅ Use these instead of generating new ones!
    if not variables:
        # Only generate if data_result is empty
        variables = adapter.generate_realistic_variables(problem_size)
```

#### 2. Fix Domain Extraction
```python
# ❌ Current (broken)
domain = intent_data.get("domain", "manufacturing")

# ✅ Fixed
domain = intent_data.get("industry", "MANUFACTURING").lower()
# or better:
result = intent_data.get("result", {})
domain = result.get("industry", "MANUFACTURING").lower()
```

#### 3. Use Data Counts for Problem Size
```python
# ✅ Get actual counts from data_result
problem_size = {
    "facilities": len(simulated_data.get('extracted_entities', {}).get('facilities', [])),
    "products": len(simulated_data.get('extracted_entities', {}).get('products', [])),
    "total_variables": len(variables),
    "total_constraints": len(constraints)
}
```

### Priority 2: Quality Improvements

#### 4. Add Variable Validation
```python
def _validate_variables(self, variables: Dict[str, Any]) -> Dict[str, Any]:
    """Validate variables from data_result"""
    issues = []
    
    # Check for generic names
    for var_name in variables.keys():
        if re.match(r'^x\d+$', var_name):
            issues.append(f"Generic variable name: {var_name}")
    
    # Check for proper structure
    for var_name, var_data in variables.items():
        if 'type' not in var_data:
            issues.append(f"Missing type for {var_name}")
        if 'bounds' not in var_data:
            issues.append(f"Missing bounds for {var_name}")
    
    return {
        "is_valid": len(issues) == 0,
        "issues": issues,
        "variable_count": len(variables)
    }
```

#### 5. Add Constraint Validation
```python
def _validate_constraints(self, constraints: Dict[str, Any], variables: Dict[str, Any]) -> Dict[str, Any]:
    """Validate constraints reference valid variables"""
    issues = []
    
    for const_name, const_data in constraints.items():
        expr = const_data.get('expression', '')
        
        # Check if constraint references existing variables
        for var_name in variables.keys():
            if var_name in expr:
                break
        else:
            issues.append(f"Constraint {const_name} doesn't reference known variables")
    
    return {
        "is_valid": len(issues) == 0,
        "issues": issues
    }
```

#### 6. Add Domain-Specific Enrichment
```python
def _enrich_with_domain_knowledge(self, variables: Dict, constraints: Dict, domain: str) -> Tuple[Dict, Dict]:
    """Add domain-specific metadata to variables/constraints"""
    
    adapter = self._get_domain_adapter(domain)
    
    # Add domain-specific metadata
    for var_name, var_data in variables.items():
        var_data['domain'] = domain
        var_data['template_pattern'] = adapter._match_template(var_name)
    
    for const_name, const_data in constraints.items():
        const_data['domain'] = domain
        const_data['constraint_type'] = adapter._classify_constraint(const_data)
    
    return variables, constraints
```

### Priority 3: Architecture Improvements

#### 7. Use LLM for Model Refinement (Optional)
```python
async def _refine_model_with_llm(self, variables: Dict, constraints: Dict, objective: Dict) -> Dict:
    """Use LLM to refine and validate model structure"""
    
    # Use Claude/GPT-4 to:
    # 1. Check for missing constraints
    # 2. Validate mathematical consistency
    # 3. Suggest improvements
    # 4. Ensure domain-specific best practices
    
    pass  # Future enhancement
```

---

## Comparison: Old vs FMCO Model Builder

| Aspect | Old (garage) | FMCO (current) | Recommended |
|--------|--------------|----------------|-------------|
| Uses data_result | ❌ No | ❌ No | ✅ Yes |
| Domain templates | ❌ Limited | ✅ Good | ✅ Excellent |
| Variable naming | ❌ Generic (x1, x2) | ✅ Realistic | ✅ Use data_result |
| FMCO patterns | ❌ None | ✅ Yes | ✅ Enhanced |
| Validation | ❌ None | ❌ None | ✅ Yes |
| Quality (Mfg) | 40% | 82.5% | 90%+ target |
| Quality (Finance) | 30% | 76% | 90%+ target |
| Quality (Retail) | 20% | 60% | 90%+ target |

---

## Next Steps

### Immediate Actions
1. **Fix data_result integration** - Use variables from Data Analyzer
2. **Fix domain extraction** - Use "industry" not "domain"
3. **Use actual counts** - Get problem size from data_result
4. **Add validation** - Validate data_result variables/constraints

### Testing Plan
1. Test with manufacturing problem (Intent + Data + Model)
2. Verify variable consistency across steps
3. Test with finance problem
4. Test with retail problem
5. Validate model specification quality

### Future Enhancements
1. LLM-based model refinement
2. Multi-objective optimization support
3. Advanced FMCO architectures (GNN, RL)
4. Model performance prediction
5. Automated hyperparameter tuning

---

## Research Integration

### FMCO Research Papers
- FM4CO (awesome-fm4co GitHub) - Implemented: Hybrid LLM+Solver
- OptLLM (arXiv:2407.07924) - Planned for enhancement

### Key Concepts Implemented
- ✅ Hybrid LLM + Traditional Solver
- ✅ Domain-Specific Adapters
- ✅ Architecture Selection
- ⚠️ In-Context Learning (partial)
- ❌ Multi-Task Learning (not implemented)
- ❌ What-If Analysis (not implemented)

---

## Conclusion

**Current Status:** Model Builder is well-structured with FMCO patterns but has a **critical bug** - it ignores the Data Analyzer output.

**Quality Score:** 8.2/10 → Could be 9.5/10 with fixes

**Key Issues:**
1. ❌ Doesn't use `data_result` parameter
2. ❌ Domain extraction broken (uses "domain" instead of "industry")
3. ❌ No validation of data_result
4. ⚠️ Template-based only (no LLM refinement)

**Recommended Action:** Fix the data integration first (Priority 1), then add validation (Priority 2), then enhance with LLM refinement (Priority 3).

**Impact:** Once fixed, the Model Builder will create consistent, validated models that flow seamlessly from Data Analysis to Solver.

---

**Document Version:** 1.0  
**Last Updated:** October 29, 2025  
**Status:** Critical Issues Identified - Fixes Required

