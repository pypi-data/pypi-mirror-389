#!/usr/bin/env python3
"""
LMEA Express Orchestrator - MVP Architecture
Single LLM call does everything: classify, parse, solve
"""

import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class LMEAExpressOrchestrator:
    """
    Streamlined orchestrator for MVP - LMEA does everything
    
    Flow:
        Problem → LMEA → Solution
        
    No intermediate steps, no redundant LLM calls
    """
    
    def __init__(self):
        from ..models.hybrid_solver import HybridSolver
        self.hybrid_solver = HybridSolver()
        logger.info("✅ LMEA Express Orchestrator initialized")
    
    async def solve(
        self,
        problem_description: str,
        max_generations: int = 100
    ) -> Dict[str, Any]:
        """
        Solve optimization problem in one shot with LMEA
        
        Args:
            problem_description: Natural language problem description
            max_generations: Max evolutionary generations for LMEA
            
        Returns:
            Complete solution with metadata
        """
        start_time = datetime.now()
        
        try:
            logger.info("🚀 LMEA Express Mode - Single-shot optimization")
            logger.info(f"📝 Problem: {problem_description[:100]}...")
            
            # LMEA will:
            # 1. Classify problem type from description
            # 2. Parse problem into structured data
            # 3. Solve with appropriate LMEA algorithm
            # All in one go!
            
            result = await self.hybrid_solver.solve_express(
                problem_description=problem_description,
                max_generations=max_generations
            )
            
            # Add metadata
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            result['metadata'] = {
                'orchestrator': 'lmea_express',
                'mode': 'single_shot',
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': duration,
                'llm_calls': 1  # Only one LLM call!
            }
            
            logger.info(f"✅ Solution found in {duration:.1f}s")
            return result
            
        except Exception as e:
            logger.error(f"❌ LMEA Express failed: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                'status': 'error',
                'error': str(e),
                'metadata': {
                    'orchestrator': 'lmea_express',
                    'mode': 'single_shot',
                    'duration_seconds': (datetime.now() - start_time).total_seconds()
                }
            }

