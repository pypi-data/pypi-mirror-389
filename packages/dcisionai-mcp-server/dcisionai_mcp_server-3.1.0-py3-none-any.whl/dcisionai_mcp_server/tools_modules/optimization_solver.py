#!/usr/bin/env python3
"""
Optimization Solver Tool - Enhanced with Phase 1+2 Components
Integrates: RobustExpressionParser, PreSolveValidator, LLMReformulator, LMEA, HybridSolver
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..models.model_spec import ModelSpec
# Legacy solver imports (moved to garage, now using HybridSolver which routes to V2)
# from ..models.mathopt_solver import MathOptSolver
# from ..models.highs_via_ortools_solver import HiGHSViaORToolsSolver
# from ..models.robust_expression_parser import RobustExpressionParser
# from ..models.presolve_validator import PreSolveValidator
# from ..models.llm_reformulator import LLMReformulator
from ..models.hybrid_solver import HybridSolver
from ..core.validators import Validator

logger = logging.getLogger(__name__)


class OptimizationSolver:
    """
    Enhanced optimization solver with Phase 1+2 capabilities
    
    Phase 1: Robustness
    - RobustExpressionParser for complex math
    - PreSolveValidator for early error detection
    - LLMReformulator for automatic recovery
    
    Phase 2: LMEA Integration
    - HybridSolver for intelligent solver selection
    - LMEA for combinatorial problems
    - HiGHS for exact problems
    """
    
    def __init__(self):
        self.validator = Validator()
        
        # Legacy solvers (keep for backward compatibility)
        self.mathopt_solver = MathOptSolver()
        self.highs_solver = HiGHSViaORToolsSolver()
        
        # Phase 1: Robustness components
        self.expression_parser = RobustExpressionParser()
        self.presolve_validator = PreSolveValidator()
        self.llm_reformulator = LLMReformulator()
        
        # Phase 2: Hybrid solver (includes LMEA)
        self.hybrid_solver = HybridSolver()
        
        # Configuration
        self.max_reformulation_attempts = 2
        self.enable_presolve_validation = True
        self.enable_llm_reformulation = True
        self.use_hybrid_solver = True
    
    async def solve_optimization(
        self,
        problem_description: str,
        intent_data: Optional[Dict] = None,
        data_analysis: Optional[Dict] = None,
        model_building: Optional[Dict] = None,
        solver_selection: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Solve optimization problem with enhanced robustness and intelligence
        
        Flow:
        1. Extract and validate model
        2. Pre-solve validation (catch errors early)
        3. Intelligent solver selection (HybridSolver)
        4. Solve with chosen method
        5. If infeasible, attempt LLM-guided reformulation
        6. Return solution with metadata
        """
        try:
            logger.info("🚀 Starting enhanced optimization solver (Phase 1+2)")
            
            # Step 1: Extract model
            if not model_building:
                logger.error("❌ No model provided")
                return {
                    "status": "error",
                    "step": "optimization_solution",
                    "error": "No model provided - solve_optimization requires a model from build_model_tool",
                    "message": "Please run build_model_tool first"
                }
            
            # Handle nested result structure
            if 'result' in model_building:
                model_result = model_building['result']
            else:
                model_result = model_building
            
            # Extract model components
            model_data = self._extract_model_data(model_result)
            
            if not model_data:
                logger.error("❌ Could not extract model data")
                return {
                    "status": "error",
                    "step": "optimization_solution",
                    "error": "Invalid model format",
                    "message": "Model does not contain required components (variables, constraints, objective)"
                }
            
            logger.info(f"📊 Model extracted: {len(model_data.get('variables', []))} vars, {len(model_data.get('constraints', []))} constraints")
            
            # Step 2: Pre-solve validation (Phase 1)
            validation_result = None
            if self.enable_presolve_validation:
                logger.info("🔍 Running pre-solve validation...")
                validation_result = self.presolve_validator.validate_model(model_data)
                
                logger.info(f"   Validation: {'✅ VALID' if validation_result.is_valid else '❌ INVALID'}")
                logger.info(f"   Errors: {len(validation_result.errors)}, Warnings: {len(validation_result.warnings)}")
                
                if not validation_result.is_valid:
                    logger.warning(f"⚠️ Pre-solve validation failed:")
                    for error in validation_result.errors[:3]:  # Show first 3 errors
                        logger.warning(f"   - {error}")
                    
                    # Validation failed - but continue anyway (LMEA can handle symbolic models)
                    logger.info("⚠️ Validation failed but continuing (LMEA can handle symbolic models)")
                    # Don't fail here - let LMEA attempt to solve
                    # if len(validation_result.errors) > 5:
                    #     return {
                    #         "status": "error",
                    #         "step": "optimization_solution",
                    #         "error": "Model validation failed",
                    #         "validation_errors": validation_result.errors,
                    #         "validation_warnings": validation_result.warnings,
                    #         "suggestions": validation_result.suggestions,
                    #         "message": "Model has critical validation errors. Please review and fix."
                    #     }
            
            # Step 3: Solve using Hybrid Solver (Phase 2) with intent_data for smart routing
            solution_result = await self._solve_with_retry_and_reformulation(
                model_data,
                problem_description,
                validation_result,
                intent_data  # Pass intent_data for LLM-driven routing
            )
            
            # Add validation metadata
            if validation_result:
                solution_result['validation'] = {
                    'is_valid': validation_result.is_valid,
                    'errors': validation_result.errors,
                    'warnings': validation_result.warnings,
                    'checks_passed': validation_result.checks_passed
                }
            
            return solution_result
            
        except Exception as e:
            logger.error(f"❌ Optimization solver failed: {e}")
            return {
                "status": "error",
                "step": "optimization_solution",
                "error": str(e),
                "message": f"Solver encountered an unexpected error: {e}"
            }
    
    async def _solve_with_retry_and_reformulation(
        self,
        model_data: Dict[str, Any],
        problem_description: str,
        validation_result: Optional[Any],
        intent_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Attempt to solve with automatic reformulation on failure
        
        Strategy:
        1. Try HybridSolver (intelligent selection)
        2. If infeasible, use LLMReformulator
        3. Retry with reformulated model
        4. Return best result
        """
        attempts = []
        
        for attempt in range(self.max_reformulation_attempts + 1):
            if attempt > 0:
                logger.info(f"🔄 Reformulation attempt {attempt}/{self.max_reformulation_attempts}")
            
            # Solve using HybridSolver with intent_data for smart routing
            if self.use_hybrid_solver:
                logger.info("⚡ Using HybridSolver (Phase 2) with LLM-driven routing")
                result = await self.hybrid_solver.solve(model_data, problem_description, intent_data)
            else:
                # Fallback to direct HiGHS
                logger.info("⚡ Using HiGHS directly (legacy)")
                result = self.highs_solver.solve_model(model_data)
            
            attempts.append({
                'attempt': attempt,
                'status': result.get('status', 'unknown'),
                'method': result.get('solver_choice', 'unknown')
            })
            
            # Check result
            status = result.get('status', 'unknown')
            
            if status in ['optimal', 'feasible', 'success']:
                # Success!
                logger.info(f"✅ Solver succeeded: {status}")
                
                # Format final result
                return self._format_solution_result(result, attempts, model_data)
            
            elif status in ['infeasible', 'unbounded'] and self.enable_llm_reformulation and attempt < self.max_reformulation_attempts:
                # Try reformulation
                logger.info(f"🔄 Attempting LLM-guided reformulation (attempt {attempt + 1})...")
                
                reformulation_result = await self.llm_reformulator.reformulate_infeasible_model(
                    model_data,
                    validation_result,
                    problem_description,
                    solver_feedback=result.get('error', result.get('message', ''))
                )
                
                if reformulation_result.get('status') == 'success':
                    reformulated_model = reformulation_result.get('reformulated_model')
                    logger.info(f"✅ Model reformulated successfully")
                    logger.info(f"   Reasoning: {reformulation_result.get('reasoning', 'N/A')[:100]}...")
                    
                    # Update model_data for next attempt
                    model_data = reformulated_model
                    
                    # Store reformulation info
                    attempts[-1]['reformulation'] = {
                        'success': True,
                        'reasoning': reformulation_result.get('reasoning', ''),
                        'changes': reformulation_result.get('changes_made', []),
                        'confidence': reformulation_result.get('confidence', 0.0)
                    }
                else:
                    logger.warning(f"⚠️ Reformulation failed: {reformulation_result.get('message', 'Unknown error')}")
                    attempts[-1]['reformulation'] = {
                        'success': False,
                        'error': reformulation_result.get('message', '')
                    }
                    break  # Can't reformulate, stop trying
            else:
                # Can't solve, stop trying
                break
        
        # All attempts failed
        logger.error(f"❌ All solve attempts failed ({len(attempts)} attempts)")
        
        return {
            "status": "error",
            "step": "optimization_solution",
            "error": result.get('error', 'Solver failed'),
            "solver_status": result.get('status', 'unknown'),
            "attempts": attempts,
            "message": f"Failed to solve after {len(attempts)} attempts (including reformulations)",
            "suggestions": [
                "Review model constraints for conflicts",
                "Check if problem bounds are realistic",
                "Consider relaxing some constraints",
                "Verify objective function is well-defined"
            ]
        }
    
    def _extract_model_data(self, model_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract model data from various formats"""
        
        # Check if it's already in the right format
        if 'variables' in model_result and 'constraints' in model_result:
            return {
                'variables': model_result.get('variables', []),
                'constraints': model_result.get('constraints', []),
                'objective': model_result.get('objective', {}),
                'problem_size': model_result.get('problem_size', {}),
                'problem_type': model_result.get('problem_type', 'unknown')
            }
        
        # Check for nested structure
        if 'execution_result' in model_result:
            execution_result = model_result['execution_result']
            if 'variables' in execution_result:
                return {
                    'variables': execution_result.get('variables', []),
                    'constraints': execution_result.get('constraints', []),
                    'objective': execution_result.get('objective', {}),
                    'problem_size': model_result.get('problem_size', {}),
                    'problem_type': model_result.get('problem_type', 'unknown')
                }
        
        # Check model_config
        if 'model_config' in model_result:
            return {
                'variables': model_result.get('variables', []),
                'constraints': model_result.get('constraints', []),
                'objective': model_result.get('objective', {}),
                'problem_size': model_result.get('problem_size', {}),
                'problem_type': model_result.get('problem_type', 'unknown')
            }
        
        return None
    
    def _format_solution_result(
        self,
        solver_result: Dict[str, Any],
        attempts: List[Dict[str, Any]],
        model_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format final solution result with metadata"""
        
        # Extract solution components
        status = solver_result.get('status', 'unknown')
        objective_value = solver_result.get('objective_value', solver_result.get('best_fitness', 0))
        variables = solver_result.get('optimal_values', solver_result.get('best_solution', solver_result.get('variables', {})))
        solve_time = solver_result.get('solve_time', 0)
        solver_used = solver_result.get('solver_choice', solver_result.get('solver', 'unknown'))
        method = solver_result.get('method', 'exact' if solver_used == 'highs' else 'heuristic')
        
        # Build result
        result = {
            "status": "success",
            "step": "optimization_solution",
            "timestamp": datetime.now().isoformat(),
            "result": {
                "solver_used": solver_used,
                "method": method,
                "status": status,
                "objective_value": objective_value,
                "variables": variables,
                "solve_time": solve_time,
                "iterations": solver_result.get('iterations', solver_result.get('generations', 0)),
                "improvement": solver_result.get('improvement', 0),
                "solver_metadata": {
                    "total_attempts": len(attempts),
                    "reformulations": sum(1 for a in attempts if 'reformulation' in a and a['reformulation'].get('success')),
                    "attempt_history": attempts
                }
            },
            "message": f"Solution found using {solver_used} ({method})"
        }
        
        # Add constraint information if available
        if 'constraints' in solver_result:
            result['result']['constraints'] = solver_result['constraints']
        
        # Add fitness history for LMEA
        if 'fitness_history' in solver_result:
            result['result']['fitness_history'] = solver_result['fitness_history']
        
        # Add reformulation metadata if model was reformulated
        reformulation_attempts = [a for a in attempts if 'reformulation' in a and a['reformulation'].get('success')]
        if reformulation_attempts:
            last_reformulation = reformulation_attempts[-1]['reformulation']
            result['result']['reformulation'] = {
                'was_reformulated': True,
                'reasoning': last_reformulation.get('reasoning', ''),
                'changes': last_reformulation.get('changes', []),
                'confidence': last_reformulation.get('confidence', 0.0)
            }
            result['message'] += " (model was automatically reformulated to resolve infeasibility)"
        
        return result
    
    # Legacy method for backward compatibility
    async def _solve_with_primary_and_backup(
        self, 
        model_result: Dict[str, Any], 
        problem_description: str, 
        selected_solver: Optional[str] = None
    ) -> Dict[str, Any]:
        """Legacy method - now redirects to new enhanced solver"""
        logger.info("⚠️ Using legacy solve method, redirecting to enhanced solver")
        
        model_data = self._extract_model_data(model_result)
        if not model_data:
            return {
                'status': 'error',
                'error': 'Could not extract model data'
            }
        
        # Use hybrid solver with intent_data for LLM-driven routing
        return await self.hybrid_solver.solve(model_data, problem_description, intent_data)
