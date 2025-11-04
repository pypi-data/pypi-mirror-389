#!/usr/bin/env python3
"""
DcisionAI MCP Server V2 - Production FastMCP Cloud Deployment
=============================================================

Single-tool MCP server exposing only the DcisionAI V2 solver.

TOOL (1 production tool):
- dcisionai_solve - Universal optimization solver with V2 architecture
  - Supabase domain configs
  - Synthetic data generation  
  - LLM-driven narratives
  - Mathematical proof validation
  - 8 domain types supported

Entry Point: dcisionai_mcp_server/mcp_server_v2.py:mcp
"""

import asyncio
import json
import logging
from typing import Any, Dict
from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP(
    name="DcisionAI",
    instructions="""
    DcisionAI provides AI-powered optimization for Manufacturing, Retail, Finance, and more.
    
    Use the dcisionai_solve tool to optimize any business problem:
    - Store layout optimization
    - Vehicle routing (VRP)
    - Workforce scheduling
    - Maintenance scheduling
    - Portfolio rebalancing
    - Promotion scheduling
    - Trading schedule
    - Job shop scheduling
    
    Just describe your problem in natural language, and DcisionAI will:
    1. Classify the problem type
    2. Extract relevant data (or simulate if needed)
    3. Build and solve an optimization model
    4. Provide structured results with mathematical proof
    5. Generate prescriptive business recommendations
    """
)

@mcp.tool()
async def dcisionai_solve(
    problem_description: str,
    validation_mode: str = "auto"
) -> Dict[str, Any]:
    """
    🎯 DcisionAI - AI-Powered Optimization Solver
    
    Solves any optimization problem using LLM-enhanced evolutionary algorithms.
    Automatically classifies problem type, extracts data, builds models, and
    provides prescriptive recommendations with mathematical validation.
    
    NEW: Parallel Solver Validation
    --------------------------------
    For LP/MIP problems, DcisionAI can run both exact (HiGHS) and heuristic (LMEA)
    solvers in parallel to cross-validate results and boost trust scores.
    
    Supported Problem Types:
    - Retail: Store layout, promotion scheduling
    - Logistics: Vehicle routing (VRP), delivery optimization
    - Workforce: Scheduling, rostering, shift planning
    - Maintenance: Equipment scheduling, predictive maintenance
    - Finance: Portfolio rebalancing, trading schedules
    - Manufacturing: Job shop scheduling, resource allocation
    
    Args:
        problem_description (str): Natural language description of your optimization problem.
            Example: "Optimize layout for grocery store with 50 products across 8 shelves"
        
        validation_mode (str): Solver validation strategy (default: "auto"):
            - "auto": Smart routing (LP/MIP → parallel validation, complex → LMEA only)
            - "parallel": Always run both solvers for cross-validation (slower but higher trust)
            - "fast": Use fastest solver only, no validation overhead (quickest results)
            - "exact": HiGHS only (fails if not LP/MIP, provably optimal)
            - "heuristic": LMEA only (works for all problems, near-optimal)
    
    Returns:
        dict: Structured optimization results including:
            - status: "success" or "error"
            - domain_id: Identified problem type
            - domain_name: Human-readable problem type
            - intent_reasoning: Why this problem type was chosen
            - data_provenance: Data quality and sources
            - structured_results: Complete solution with 7 substeps:
                * a_model_development: Approach and reasoning
                * b_mathematical_formulation: Variables, constraints, objectives
                * c_solver_steps: Algorithm execution details
                * d_constraint_sensitivity: How constraints affect solution
                * e_solve_results: Final solution with metrics
                * f_mathematical_proof: Validation and trust score
                * g_visualization_data: Data for interactive visualizations
            - objective_value: Final objective function value
            - generations_run: Number of evolutionary iterations
            - duration_seconds: Solve time
            - mathematical_proof: Proof suite (constraint verification, Monte Carlo, etc.)
            - trust_score: Solution confidence (0.0-1.0)
            - certification: "VERIFIED", "PARTIAL", or "UNVERIFIED"
            - evolution_history: Fitness progression over generations
    
    Example Usage:
        ```
        result = await dcisionai_solve(
            "Optimize delivery routes for 20 customers with 3 trucks"
        )
        print(f"Solution: {result['structured_results']['e_solve_results']['narrative']}")
        print(f"Trust Score: {result['trust_score']}")
        ```
    
    Notes:
        - First solve may take 30-60 seconds (LLM parsing + optimization)
        - Subsequent similar problems are faster (cached configs)
        - If data is missing, DcisionAI will simulate realistic data
        - All simulated data is disclosed in data_provenance
        - Mathematical proof validates solution quality and feasibility
    """
    try:
        logger.info(f"📝 Solving optimization problem: {problem_description[:100]}...")
        logger.info(f"🔧 Validation mode: {validation_mode}")
        
        # Import V2 solver
        from .tools_modules.dcisionai_tool import dcisionai_solve as v2_solve
        
        # Call V2 solver with validation mode
        result = await v2_solve(problem_description, validation_mode=validation_mode)
        
        logger.info(f"✅ Optimization complete: {result.get('status')} ({result.get('domain_name')})")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error in dcisionai_solve: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__,
            "message": "Optimization failed. Please check your problem description and try again."
        }


# Optional: Add a health check tool for monitoring
@mcp.tool()
async def health_check() -> Dict[str, Any]:
    """
    🏥 Health Check
    
    Verifies that DcisionAI MCP server is running and all dependencies are available.
    
    Returns:
        dict: Server health status including:
            - status: "healthy" or "unhealthy"
            - version: Server version
            - dependencies: Status of key dependencies (Supabase, Anthropic, etc.)
    """
    try:
        import os
        
        # Check critical dependencies
        dependencies = {
            "supabase": bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_API_KEY")),
            "anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
            "v2_solver": False,
        }
        
        # Try importing V2 solver
        try:
            from .tools_modules.dcisionai_tool import dcisionai_solve
            from .models.dcisionai_solver_v2 import DcisionAISolverV2
            dependencies["v2_solver"] = True
        except ImportError:
            pass
        
        all_healthy = all(dependencies.values())
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "version": "2.0.0",
            "solver": "DcisionAI V2 (LMEA + Supabase)",
            "dependencies": dependencies,
            "supported_domains": [
                "retail_layout",
                "vrp",
                "workforce",
                "maintenance",
                "store_promotion",
                "portfolio_rebalancing",
                "trading_schedule",
                "job_shop"
            ]
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# Resources for documentation
@mcp.resource("dcisionai://docs/solver-guide")
def get_solver_guide() -> str:
    """
    📚 DcisionAI Solver Guide
    
    Comprehensive guide for using the DcisionAI optimization solver.
    """
    return """
# DcisionAI Optimization Solver Guide

## Quick Start

```python
# Simple store layout optimization
result = await dcisionai_solve(
    "Optimize layout for grocery store with 50 products across 8 shelves"
)

# Vehicle routing problem
result = await dcisionai_solve(
    "Optimize delivery routes for 20 customers with 3 trucks. "
    "Total capacity 100 packages per truck."
)

# Workforce scheduling
result = await dcisionai_solve(
    "Schedule 15 workers across 7 days with varying demand. "
    "Each worker can work max 40 hours/week."
)
```

## Supported Problem Types

1. **Retail Layout** - Product placement, shelf optimization
2. **Vehicle Routing (VRP)** - Delivery routes, logistics
3. **Workforce Scheduling** - Shift planning, rostering
4. **Maintenance Scheduling** - Equipment maintenance, technician allocation
5. **Store Promotion** - Promotion timing, product selection
6. **Portfolio Rebalancing** - Asset allocation, risk management
7. **Trading Schedule** - Order execution, market impact
8. **Job Shop Scheduling** - Manufacturing, resource allocation

## How It Works

1. **Problem Classification**: LLM analyzes your description
2. **Data Extraction**: Extracts entities (products, vehicles, workers, etc.)
3. **Synthetic Data**: Generates realistic data if missing
4. **Optimization**: Runs LMEA (LLM-Enhanced Evolutionary Algorithm)
5. **Validation**: Mathematical proof of solution quality
6. **Narrative**: LLM generates prescriptive business recommendations

## Response Structure

```json
{
  "status": "success",
  "domain_name": "Store Layout Optimization",
  "intent_reasoning": "Why this problem type...",
  "data_provenance": {
    "data_required": [...],
    "data_provided": [...],
    "data_simulated": [...]
  },
  "structured_results": {
    "a_model_development": "Approach and reasoning",
    "b_mathematical_formulation": "Math model details",
    "c_solver_steps": "Algorithm execution",
    "d_constraint_sensitivity": "Constraint analysis",
    "e_solve_results": {
      "narrative": "DcisionAI recommends...",
      "metrics": {...}
    },
    "f_mathematical_proof": "Validation results",
    "g_visualization_data": "Interactive viz data"
  },
  "trust_score": 0.85,
  "certification": "VERIFIED"
}
```

## Best Practices

1. **Be Specific**: Include numbers, constraints, objectives
   - ❌ "Optimize my store"
   - ✅ "Optimize layout for 50 products, 8 shelves, maximize revenue"

2. **Mention Constraints**: Tell us what's required
   - "Must consider foot traffic"
   - "Trucks have 100 package capacity"
   - "Workers can work max 40 hours/week"

3. **Describe Goals**: What are you optimizing for?
   - "Maximize revenue"
   - "Minimize travel distance"
   - "Balance workload across staff"

4. **Trust the Simulation**: If data is missing, we'll simulate realistic values
   - All simulations are disclosed in data_provenance
   - You can always provide real data for better accuracy

## Tips for Different Domains

### Retail Layout
- Specify: # products, # shelves, product categories
- Mention: High-margin items, foot traffic, refrigeration needs

### Vehicle Routing
- Specify: # customers, # vehicles, capacities, distances
- Mention: Time windows, priority customers, vehicle types

### Workforce Scheduling
- Specify: # workers, # shifts, demand per shift
- Mention: Skills, availability, labor laws, preferences

### Finance
- Specify: # assets, target allocation, constraints
- Mention: Risk tolerance, rebalancing costs, tax considerations
"""


@mcp.resource("dcisionai://docs/api-examples")
def get_api_examples() -> str:
    """
    💡 DcisionAI API Examples
    
    Real-world examples for different problem types.
    """
    return """
# DcisionAI API Examples

## 1. Retail Store Layout

```python
result = await dcisionai_solve(
    "Optimize layout for grocery store with 50 products across 8 shelf sections. "
    "High-margin items include coffee, snacks, and cereal. "
    "Must consider foot traffic patterns and refrigeration needs."
)

# Access results
narrative = result['structured_results']['e_solve_results']['narrative']
print(narrative)  # "DcisionAI recommends placing coffee at eye level..."

# Check solution quality
trust_score = result['trust_score']
print(f"Trust Score: {trust_score * 100}%")  # "Trust Score: 85%"
```

## 2. Vehicle Routing Problem

```python
result = await dcisionai_solve(
    "Optimize delivery routes for 20 customers with 3 trucks. "
    "Each truck has 100 package capacity. "
    "Must complete all deliveries within 8 hours. "
    "Minimize total distance traveled."
)

# Access route details
routes = result['structured_results']['e_solve_results']['solution_details']
total_distance = result['objective_value']
```

## 3. Workforce Scheduling

```python
result = await dcisionai_solve(
    "Schedule 15 workers across 7 days with demand of 5, 8, 12, 15, 18, 10, 6 workers per day. "
    "Each worker can work max 40 hours/week, 8 hours/day. "
    "Minimize overtime while meeting demand."
)

# Check schedule
schedule = result['structured_results']['e_solve_results']['solution_details']
certification = result['certification']  # "VERIFIED" if all constraints met
```

## 4. Portfolio Rebalancing

```python
result = await dcisionai_solve(
    "Rebalance portfolio of 10 stocks to target 60/40 stocks/bonds allocation. "
    "Current value: $1,000,000. "
    "Minimize transaction costs while staying within 5% of target."
)

# Access trade recommendations
trades = result['structured_results']['e_solve_results']['solution_details']
expected_impact = result['structured_results']['e_solve_results']['metrics']
```

## 5. Checking Solution Quality

```python
result = await dcisionai_solve("Your problem...")

# Check if solution is trustworthy
if result['certification'] == 'VERIFIED':
    print("✅ High-confidence solution")
    print(f"Trust Score: {result['trust_score']}")
    
    # Access mathematical proof
    proof = result['mathematical_proof']
    print(f"Constraints satisfied: {proof['constraint_verification']}")
    print(f"Monte Carlo trials: {proof['monte_carlo_simulation']}")
    
elif result['certification'] == 'PARTIAL':
    print("⚠️ Solution found, but some proofs unavailable")
    
else:
    print("❌ Low confidence, review results carefully")
```

## 6. Using Visualization Data

```python
result = await dcisionai_solve("Your problem...")

# Get visualization data for plotting
viz_data = result['structured_results']['g_visualization_data']

# Evolution timeline (for animations)
evolution = result['evolution_history']
for gen in evolution:
    print(f"Generation {gen['generation']}: Fitness {gen['best_fitness']}")

# Plot fitness progression
import matplotlib.pyplot as plt
generations = [g['generation'] for g in evolution]
fitness = [g['best_fitness'] for g in evolution]
plt.plot(generations, fitness)
plt.xlabel('Generation')
plt.ylabel('Fitness')
plt.title('Solution Evolution')
plt.show()
```
"""


# Entry point for FastMCP Cloud
# Note: FastMCP Cloud imports the 'mcp' object directly and manages its own event loop
# The mcp.run() call is only for local testing with stdio transport

# For local testing only (not used by FastMCP Cloud):
# if __name__ == "__main__":
#     logger.info("🚀 DcisionAI MCP Server V2 starting...")
#     logger.info("📍 Entry point: mcp_server_v2.py:mcp")
#     logger.info("🔧 Exposing 1 production tool: dcisionai_solve")
#     mcp.run()

