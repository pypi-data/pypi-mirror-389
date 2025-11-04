#!/usr/bin/env python3
"""
DcisionAI MCP Server - FastMCP Implementation (Secure)
=====================================================

This module provides a FastMCP server implementation following the official
MCP documentation patterns for optimal compatibility.

Provides comprehensive optimization capabilities:

TOOLS (11 core tools):
1. classify_intent_tool - Intent classification for optimization requests
2. analyze_data_tool - Data analysis and preprocessing
3. select_solver_tool - Intelligent solver selection based on problem type
4. build_model_tool - Mathematical model building with Qwen 30B
5. solve_optimization_tool - Optimization solving and results
6. explain_optimization_tool - Business-facing explainability and insights
7. simulate_scenarios_tool - Scenario simulation and risk assessment
8. critique_response_tool - Truth validation for any tool response
9. critique_intent_classification_tool - Specialized critique for intent results
10. critique_data_analysis_tool - Specialized critique for data analysis results
11. execute_optimization_workflow_tool - Complete workflow orchestrator with intelligent gating

RESOURCES (2 resources):
1. dcisionai://knowledge-base - Secure knowledge base metadata (proprietary data protected)
2. dcisionai://workflow-templates - Industry workflow templates

PROMPTS (2 prompts):
1. optimization_analysis_prompt - Template for problem analysis
2. model_building_guidance_prompt - Template for model building guidance
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP

from .tools import (
    classify_intent,
    analyze_data,
    build_model,
    solve_optimization,
    explain_optimization,
    simulate_scenarios,
    validate_tool_output,
    validate_complete_workflow,
    critique_response,
    critique_intent_classification,
    critique_data_analysis,
    execute_optimization_workflow,
    execute_complete_workflow
)
from .config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("dcisionai-optimization")

@mcp.tool()
async def dcisionai_tool(problem_description: str) -> Dict[str, Any]:
    """
    🎯 DcisionAI - Single Entry Point for All Optimization
    
    This is the PRIMARY tool for optimization. It automatically:
    1. Classifies your problem type
    2. Routes to the best LMEA solver
    3. Returns structured results with Intent, Data, and Results (7 substeps)
    
    Args:
        problem_description: Natural language description of your optimization problem
        
    Returns:
        Structured response with:
        - intent: Problem classification + business reasoning
        - data: Data provenance (required/provided/simulated/usage)
        - results: Complete solution with 7 substeps (model dev, math formulation, 
                   solver steps, sensitivity, solve results, proof, visualization data)
    """
    try:
        from .tools_modules.dcisionai_tool import dcisionai_solve
        result = await dcisionai_solve(problem_description)
        return result
    except Exception as e:
        logger.error(f"Error in dcisionai_tool: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}

@mcp.tool()
async def classify_intent_tool(problem_description: str, context: Optional[str] = None) -> Dict[str, Any]:
    """Classify user intent for optimization requests.
    
    Args:
        problem_description: The user's optimization request or problem description
        context: Optional context about the business domain
    
    Returns:
        Dictionary with intent classification results
    """
    try:
        result = await classify_intent(problem_description, context)
        return result
    except Exception as e:
        logger.error(f"Error in classify_intent: {e}")
        return {"error": str(e)}

@mcp.tool()
async def analyze_data_tool(problem_description: str, intent_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Analyze and preprocess data for optimization.
    
    Args:
        problem_description: Description of the optimization problem
        intent_data: Intent classification results as dictionary object
    
    Returns:
        Dictionary with data analysis results
    """
    try:
        # Handle intent_data parameter - ensure it's a dict
        if intent_data is None:
            intent_data = {}
        elif isinstance(intent_data, str):
            # If it's a string, try to parse it as JSON
            try:
                import json
                intent_data = json.loads(intent_data)
            except:
                logger.warning(f"Could not parse intent_data as JSON: {intent_data}")
                intent_data = {}
        elif not isinstance(intent_data, dict):
            logger.warning(f"intent_data is not a dict: {type(intent_data)}")
            intent_data = {}
        
        result = await analyze_data(problem_description, intent_data)
        return result
    except Exception as e:
        logger.error(f"Error in analyze_data: {e}")
        return {"error": str(e)}

@mcp.tool()
async def select_solver_tool(
    optimization_type: str = "linear_programming",
    problem_size: Optional[Dict[str, Any]] = None,
    performance_requirement: str = "balanced"
) -> Dict[str, Any]:
    """Select the best available solver for optimization problems.
    
    Args:
        optimization_type: Type of optimization problem (linear_programming, quadratic_programming, etc.)
        problem_size: Problem size information as dictionary object (num_variables, num_constraints, etc.)
        performance_requirement: Performance requirement (speed, accuracy, or balanced)
    
    Returns:
        Dictionary with solver selection results
    """
    try:
        # Solver selection is now handled automatically by HybridSolver
        # This tool is deprecated but kept for backwards compatibility
        return {
            "status": "success",
            "message": "Solver selection is now automatic via HybridSolver",
            "recommended_solver": "HybridSolver with LMEA for combinatorial problems",
            "optimization_type": optimization_type,
            "note": "No manual solver selection needed - HybridSolver intelligently routes based on problem type"
        }
    except Exception as e:
        logger.error(f"Error in select_solver_tool: {e}")
        return {"error": str(e)}

@mcp.tool()
async def build_model_tool(
    problem_description: str,
    intent_data: Optional[Dict[str, Any]] = None,
    data_analysis: Optional[Dict[str, Any]] = None,
    solver_selection: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Build mathematical optimization model using Qwen 30B.
    
    Args:
        problem_description: Detailed problem description
        intent_data: Intent classification results as dictionary object
        data_analysis: Results from data analysis step as dictionary object
        solver_selection: Results from solver selection step as dictionary object
    
    Returns:
        Dictionary with model building results
    """
    try:
        logger.info("Starting build_model_tool")
        
        # Handle parameters - ensure they're dicts
        def ensure_dict(param, param_name):
            if param is None:
                return {}
            elif isinstance(param, str):
                try:
                    import json
                    return json.loads(param)
                except:
                    logger.warning(f"Could not parse {param_name} as JSON: {param}")
                    return {}
            elif not isinstance(param, dict):
                logger.warning(f"{param_name} is not a dict: {type(param)}")
                return {}
            return param
        
        intent_data = ensure_dict(intent_data, "intent_data")
        data_analysis = ensure_dict(data_analysis, "data_analysis")
        solver_selection = ensure_dict(solver_selection, "solver_selection")
        
        result = await build_model(
            problem_description,
            intent_data,
            data_analysis,
            solver_selection
        )
        
        logger.info(f"build_model returned result type: {type(result)}")
        logger.info(f"Returning result directly to FastMCP for serialization")
        
        # Return the dict directly - FastMCP will handle JSON serialization
        return result
    except Exception as e:
        logger.error(f"Error in build_model: {e}", exc_info=True)
        return {"error": str(e)}

@mcp.tool()
async def solve_optimization_tool(
    problem_description: str,
    intent_data: Optional[Dict[str, Any]] = None,
    data_analysis: Optional[Dict[str, Any]] = None,
    model_building: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Solve the optimization problem and generate results.
    
    Args:
        problem_description: Problem description
        intent_data: Intent classification results as dictionary object
        data_analysis: Data analysis results as dictionary object
        model_building: Model building results as dictionary object
    
    Returns:
        Dictionary with optimization solution results
    """
    try:
        # Handle parameters - ensure they're dicts
        def ensure_dict(param, param_name):
            if param is None:
                return {}
            elif isinstance(param, str):
                try:
                    import json
                    return json.loads(param)
                except:
                    logger.warning(f"Could not parse {param_name} as JSON: {param}")
                    return {}
            elif not isinstance(param, dict):
                logger.warning(f"{param_name} is not a dict: {type(param)}")
                return {}
            return param
        
        intent_data = ensure_dict(intent_data, "intent_data")
        data_analysis = ensure_dict(data_analysis, "data_analysis")
        model_building = ensure_dict(model_building, "model_building")
        
        result = await solve_optimization(
            problem_description,
            intent_data,
            data_analysis,
            model_building
        )
        return result
    except Exception as e:
        logger.error(f"Error in solve_optimization: {e}")
        return {"error": str(e)}

@mcp.tool()
async def explain_optimization_tool(
    problem_description: str,
    intent_data: Optional[Dict[str, Any]] = None,
    data_analysis: Optional[Dict[str, Any]] = None,
    model_building: Optional[Dict[str, Any]] = None,
    optimization_solution: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Provide business-facing explainability for optimization results.
    
    Args:
        problem_description: Original problem description
        intent_data: Intent classification results as dictionary object
        data_analysis: Data analysis results as dictionary object
        model_building: Model building results as dictionary object
        optimization_solution: Optimization solution results as dictionary object
    
    Returns:
        Dictionary with explainability results
    """
    try:
        result = await explain_optimization(
            problem_description,
            intent_data or {},
            data_analysis or {},
            model_building or {},
            optimization_solution or {}
        )
        return result
    except Exception as e:
        logger.error(f"Error in explain_optimization: {e}")
        return {"error": str(e)}

@mcp.tool()
async def simulate_scenarios_tool(
    problem_description: str,
    optimization_solution: Optional[Dict[str, Any]] = None,
    scenario_parameters: Optional[Dict[str, Any]] = None,
    simulation_type: str = "monte_carlo",
    num_trials: int = 10000
) -> Dict[str, Any]:
    """Simulate different scenarios for optimization analysis and risk assessment.
    
    Args:
        problem_description: Description of the optimization problem
        optimization_solution: Results from optimization solving as dictionary object
        scenario_parameters: Parameters for scenario simulation as dictionary object
        simulation_type: Type of simulation (monte_carlo, discrete_event, agent_based, etc.)
        num_trials: Number of simulation trials
    
    Returns:
        Dictionary with simulation results
    """
    try:
        result = await simulate_scenarios(
            problem_description,
            optimization_solution,
            scenario_parameters,
            simulation_type,
            num_trials
        )
        return result
    except Exception as e:
        logger.error(f"Error in simulate_scenarios: {e}")
        return {"error": str(e)}

@mcp.tool()
async def validate_tool_output_tool(
    problem_description: str,
    tool_name: str,
    tool_output: Dict[str, Any],
    model_spec: Optional[Dict[str, Any]] = None,
    validation_type: str = "comprehensive"
) -> Dict[str, Any]:
    """Validate any tool's output for correctness and business logic.
    
    Args:
        problem_description: Original problem description
        tool_name: Name of the tool that generated the output
        tool_output: The tool's output to validate as dictionary object
        model_spec: Model specification as dictionary object (if available)
        validation_type: Type of validation (mathematical, business, comprehensive)
    
    Returns:
        Dictionary with validation results and trust score
    """
    try:
        result = await validate_tool_output(
            problem_description,
            tool_name,
            tool_output,
            model_spec,
            validation_type
        )
        return result
    except Exception as e:
        logger.error(f"Error in validate_tool_output: {e}")
        return {"error": str(e)}

@mcp.tool()
async def validate_complete_workflow_tool(
    problem_description: str,
    workflow_results: Dict[str, Any],
    model_spec: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Validate a complete optimization workflow for quality and trust.
    
    Args:
        problem_description: Original problem description
        workflow_results: Dictionary of tool_name -> tool_output from the workflow
        model_spec: Model specification as dictionary object (if available)
    
    Returns:
        Dictionary with complete workflow validation results and trust scores
    """
    try:
        result = await validate_complete_workflow(
            problem_description, workflow_results, model_spec
        )
        return result
    except Exception as e:
        logger.error(f"Error in validate_complete_workflow: {e}")
        return {"error": str(e)}

@mcp.tool()
async def critique_response_tool(
    problem_description: str,
    tool_name: str,
    tool_output: Dict[str, Any],
    context: Optional[str] = None
) -> Dict[str, Any]:
    """Critique and validate any tool's response for truth and accuracy.
    
    Args:
        problem_description: Original problem description
        tool_name: Name of the tool that generated the response
        tool_output: The tool's response to critique
        context: Additional context for critique
    
    Returns:
        Dictionary with critique results including truth score, accuracy issues, and final verdict
    """
    try:
        return await critique_response(problem_description, tool_name, tool_output, context)
    except Exception as e:
        logger.error(f"Error in critique_response: {e}")
        return {"error": str(e)}

@mcp.tool()
async def critique_intent_classification_tool(
    problem_description: str,
    intent_result: Dict[str, Any],
    kb_response: Optional[str] = None
) -> Dict[str, Any]:
    """Specialized critique for intent classification results.
    
    Args:
        problem_description: Original problem description
        intent_result: Intent classification result to critique
        kb_response: Knowledge base response (if available)
    
    Returns:
        Dictionary with intent critique results including accuracy scores and recommendations
    """
    try:
        return await critique_intent_classification(problem_description, intent_result, kb_response)
    except Exception as e:
        logger.error(f"Error in critique_intent_classification: {e}")
        return {"error": str(e)}

@mcp.tool()
async def critique_data_analysis_tool(
    problem_description: str,
    data_result: Dict[str, Any],
    intent_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Specialized critique for data analysis results.
    
    Args:
        problem_description: Original problem description
        data_result: Data analysis result to critique
        intent_data: Intent classification data (if available)
    
    Returns:
        Dictionary with data critique results including quality scores and recommendations
    """
    try:
        return await critique_data_analysis(problem_description, data_result, intent_data)
    except Exception as e:
        logger.error(f"Error in critique_data_analysis: {e}")
        return {"error": str(e)}

@mcp.tool()
async def execute_complete_workflow_tool(
    problem_description: str,
    model_preference: str = "fine-tuned",
    tools_to_call: Optional[List[str]] = None,
    fmco_features: Optional[Dict[str, Any]] = None,
    architecture: str = "auto",
    tuning_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Execute the complete optimization workflow with session management and FMCO features.
    
    This is the main entry point for the optimization workflow with full configurability.
    
    Args:
        problem_description: Description of the optimization problem
        model_preference: LLM model preference (default: "fine-tuned")
        tools_to_call: List of tools to execute (e.g., ['intent', 'data', 'model', 'solver', 'optimization'])
        fmco_features: Optional FMCO configuration
        architecture: Architecture selection (default: "auto")
        tuning_config: Optional tuning configuration
        
    Returns:
        Dictionary with complete workflow results
    """
    try:
        return await execute_complete_workflow(
            problem_description=problem_description,
            model_preference=model_preference,
            tools_to_call=tools_to_call,
            fmco_features=fmco_features,
            architecture=architecture,
            tuning_config=tuning_config
        )
    except Exception as e:
        logger.error(f"Error in execute_complete_workflow: {e}")
        return {"error": str(e)}

@mcp.tool()
async def execute_optimization_workflow_tool(problem_description: str) -> Dict[str, Any]:
    """Execute the complete optimization workflow using the tool orchestrator.
    
    This is the main entry point for the optimization workflow that orchestrates
    all tools with intelligent gating and data flow management.
    
    Args:
        problem_description: Description of the optimization problem
        
    Returns:
        Dictionary with complete workflow results including:
        - status: success/partial_success/failed/roadmap/unmatched
        - workflow_id: Unique identifier for this workflow execution
        - duration_seconds: Total execution time
        - completed_steps: List of successfully completed steps
        - failed_steps: List of failed steps
        - warnings: List of warnings encountered
        - errors: List of errors encountered
        - results: Dictionary with results from each tool
        - summary: Human-readable workflow summary
    """
    try:
        return await execute_optimization_workflow(problem_description)
    except Exception as e:
        logger.error(f"Error in execute_optimization_workflow: {e}")
        return {"error": str(e)}

@mcp.tool()
async def benchmark_models_tool(
    models: List[str] = ["fine-tuned", "gpt-4o", "claude-3-5-sonnet"],
    test_cases: Optional[List[Dict]] = None
) -> Dict[str, Any]:
    """Benchmark different LLM models across various metrics
    
    Args:
        models: List of model names to benchmark
        test_cases: Optional custom test cases (uses default if not provided)
    
    Returns:
        Dictionary with benchmark results and comparison report
    """
    try:
        from .tools_modules.model_benchmarker import ModelBenchmarker
        
        logger.info(f"🔍 Starting model benchmark for: {models}")
        
        benchmarker = ModelBenchmarker()
        result = await benchmarker.compare_models(models, test_cases)
        
        logger.info(f"✅ Model benchmark completed for {len(models)} models")
        return result
        
    except Exception as e:
        logger.error(f"❌ Model benchmark failed: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }

@mcp.tool()
async def get_version_tool() -> Dict[str, Any]:
    """Get the current version of the DcisionAI MCP Server.
    
    Returns:
        Dictionary with version information
    """
    try:
        from . import __version__
        return {
            "version": __version__,
            "package": "dcisionai-mcp-server",
            "description": "DcisionAI MCP Server v2.5 - Enhanced with KB Integration, Retry Mechanism, and 3-Industry Wedge Focus",
            "features": [
                "Modular Architecture",
                "OR-Tools MathOpt Integration",
                "Enhanced JSON Serialization",
                "Complete Optimization Workflow",
                "Knowledge Base Integration",
                "Retry Mechanism",
                "Validation Feedback",
                "3-Industry Wedge Focus",
                "Multi-stage Classification",
                "Enhanced Model Building",
                "Enhanced Solver Selection"
            ]
        }
    except Exception as e:
        logger.error(f"Error getting version: {e}")
        return {"error": str(e)}




# Resources
@mcp.resource("dcisionai://knowledge-base")
async def knowledge_base_resource() -> str:
    """Optimization Knowledge Base - Secure access to optimization examples and patterns.
    
    This resource provides metadata about the knowledge base without exposing proprietary data.
    Use the search_knowledge_base tool to query for specific optimization examples.
    """
    try:
        from .tools import DcisionAITools
        tools_instance = DcisionAITools()
        
        # Only return metadata, not the actual proprietary data
        kb_metadata = {
            "name": "DcisionAI Optimization Knowledge Base",
            "description": "Comprehensive database of optimization examples and patterns",
            "total_examples": len(tools_instance.kb.knowledge_base_data.get('examples', [])),
            "categories": list(tools_instance.kb.knowledge_base_data.get('categories', {}).keys()),
            "last_updated": tools_instance.kb.knowledge_base_data.get('metadata', {}).get('created_at', 'Unknown'),
            "access_method": "Use search_knowledge_base tool to query for specific examples",
            "security_note": "Proprietary data protected - only search results are returned"
        }
        
        return json.dumps(kb_metadata, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to load knowledge base metadata: {e}"}, indent=2)

@mcp.resource("dcisionai://workflow-templates")
async def workflow_templates_resource() -> str:
    """Industry Workflow Templates - Predefined optimization workflows for different industries."""
    try:
        result = await get_workflow_templates()
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to load workflow templates: {e}"}, indent=2)

# Prompts
@mcp.prompt()
async def optimization_analysis_prompt(
    problem_type: str,
    industry: Optional[str] = None
) -> str:
    """Template for optimization problem analysis.
    
    Args:
        problem_type: Type of optimization problem (e.g., portfolio, production, scheduling)
        industry: Industry context (e.g., finance, manufacturing, healthcare)
    """
    industry = industry or "general"
    return f"""You are an expert optimization analyst. Analyze this {problem_type} optimization problem in the {industry} industry.

**Analysis Framework:**
1. **Problem Classification**: Identify the optimization type (linear, integer, quadratic, etc.)
2. **Decision Variables**: Define what decisions need to be made
3. **Constraints**: Identify limitations and requirements
4. **Objective**: Determine the optimization goal
5. **Complexity Assessment**: Evaluate problem size and computational requirements
6. **Solution Approach**: Recommend appropriate solving methods

**Industry Context**: {industry}
**Problem Type**: {problem_type}

Provide a structured analysis following this framework."""

@mcp.prompt()
async def model_building_guidance_prompt(complexity: str) -> str:
    """Template for mathematical model building guidance.
    
    Args:
        complexity: Problem complexity level (simple, medium, complex)
    """
    return f"""You are a mathematical optimization expert. Provide guidance for building a {complexity} complexity optimization model.

**Model Building Process:**
1. **Variable Definition**: Create decision variables with proper bounds and types
2. **Constraint Formulation**: Express limitations as mathematical constraints
3. **Objective Function**: Define the optimization goal mathematically
4. **Model Validation**: Ensure mathematical correctness and feasibility
5. **Solver Selection**: Choose appropriate solving algorithm

**Complexity Level**: {complexity}

Provide detailed guidance for each step, including examples and best practices."""

def main():
    """Initialize and run the FastMCP server."""
    logger.info("Starting DcisionAI MCP Server with FastMCP")
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
