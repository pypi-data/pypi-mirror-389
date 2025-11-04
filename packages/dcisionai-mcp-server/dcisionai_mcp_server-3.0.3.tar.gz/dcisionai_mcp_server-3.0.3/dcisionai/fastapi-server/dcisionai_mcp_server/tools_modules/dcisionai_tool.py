"""
DcisionAI Tool - Single Entry Point for All Optimization
This is the ONLY tool users interact with. It:
1. Classifies the problem
2. Routes to the appropriate DAME solver
3. Returns structured response with Intent, Data, Results
"""

import logging
from typing import Dict, Any
from ..models.hybrid_solver import HybridSolver

logger = logging.getLogger(__name__)


async def dcisionai_solve(
    problem_description: str,
    validation_mode: str = "auto"
) -> Dict[str, Any]:
    """
    Single entry point for DcisionAI optimization.
    
    Args:
        problem_description: Natural language description of the optimization problem
        validation_mode: Solver validation strategy ("auto", "parallel", "fast", "exact", "heuristic")
        
    Returns:
        Structured response with 3 sections:
        - intent: Problem classification + business reasoning
        - data: Data provenance (required/provided/simulated/usage)
        - results: Complete solution with 7 substeps
    """
    try:
        logger.info(f"🎯 DcisionAI Tool called with problem: {problem_description[:100]}...")
        logger.info(f"🔧 Validation mode: {validation_mode}")
        
        # TODO: Pass validation_mode to solver when HybridSolver supports it
        # For now, log it for visibility
        
        # Initialize hybrid solver (routes to appropriate DAME solver)
        solver = HybridSolver()
        
        # Solve using Express Mode (single call, structured response)
        result = await solver.solve_express(problem_description)
        
        if result.get('status') == 'error':
            return {
                'status': 'error',
                'error': result.get('error', 'Unknown error'),
                'message': 'Optimization failed'
            }
        
        # Structure the response for UI
        structured_response = {
            'status': 'success',
            'metadata': {
                'orchestrator': 'dcisionai_tool',
                'mode': 'single_entry',
                'timestamp': result.get('metadata', {}).get('end_time'),
                'duration_seconds': result.get('metadata', {}).get('duration_seconds')
            },
            # Intent Section (from DAME solver)
            'intent': {
                'status': 'success',
                'result': {
                    'problem_type': result.get('solver_type', 'optimization'),
                    'industry': result.get('industry', 'General'),
                    'matched_use_case': result.get('solver_type', 'optimization'),
                    'confidence': 1.0,
                    'reasoning': result.get('intent_reasoning', 'Optimization problem detected'),
                    'optimization_type': 'evolutionary_algorithm',
                    'complexity': 'medium'
                }
            },
            # Data Section (from DAME solver's data_provenance)
            'data': {
                'status': 'success',
                'result': result  # Full result includes data_provenance
            },
            # Results Section (full optimization results)
            'results': result
        }
        
        logger.info(f"✅ DcisionAI Tool completed successfully")
        return structured_response
        
    except Exception as e:
        logger.error(f"❌ DcisionAI Tool error: {str(e)}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e),
            'message': 'Optimization failed due to internal error'
        }

