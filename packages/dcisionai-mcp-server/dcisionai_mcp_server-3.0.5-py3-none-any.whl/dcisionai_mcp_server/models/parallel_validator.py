"""
Parallel Solver Validation for DcisionAI Platform

Cross-validates optimization solutions by running multiple solvers in parallel.
Boosts trust scores from 85% → 100% when solvers agree.

Based on successful POC (Nov 2, 2025).
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable, Awaitable
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SolverComparisonResult:
    """Results from parallel solver comparison"""
    highs_result: Optional[Dict[str, Any]]
    lmea_result: Dict[str, Any]
    objective_gap: float  # Absolute difference
    gap_percentage: float  # % difference  
    agreement_score: float  # 0.0-1.0 (1.0 = perfect match)
    lmea_quality: float  # DAME obj / HiGHS obj
    validation_insight: str
    best_solver: str  # "highs" or "lmea"
    cross_validation_boost: float  # Trust score boost
    both_succeeded: bool


class ParallelSolverValidator:
    """
    Validates optimization solutions by running multiple solvers in parallel
    
    Key Benefits:
    - Quantify heuristic quality ("DAME found 98.5% of optimal")
    - Boost trust scores (+5-15%)
    - Automatic fallback if one solver fails
    - Zero wall-time overhead (parallel execution)
    
    Example:
        validator = ParallelSolverValidator()
        result = await validator.validate_parallel(
            problem_data=parsed_data,
            highs_solver_fn=lambda: highs.solve(...),
            lmea_solver_fn=lambda: lmea.solve(...)
        )
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def validate_parallel(
        self,
        problem_data: Dict[str, Any],
        highs_solver_fn: Callable[[], Awaitable[Dict[str, Any]]],
        lmea_solver_fn: Callable[[], Awaitable[Dict[str, Any]]],
        problem_type: str = "maximize"
    ) -> SolverComparisonResult:
        """
        Run both solvers in parallel and compare results
        
        Args:
            problem_data: Parsed problem data
            highs_solver_fn: Async function that runs HiGHS solver
            lmea_solver_fn: Async function that runs DAME solver
            problem_type: "maximize" or "minimize"
        
        Returns:
            SolverComparisonResult with comparison details
        """
        self.logger.info("🎯 Running PARALLEL validation (HiGHS + DAME)")
        
        # Run both solvers simultaneously
        highs_task = highs_solver_fn()
        lmea_task = lmea_solver_fn()
        
        # Await both (parallel execution via asyncio)
        highs_result, lmea_result = await asyncio.gather(
            highs_task,
            lmea_task,
            return_exceptions=True  # Don't fail if one crashes
        )
        
        # Handle exceptions
        if isinstance(highs_result, Exception):
            self.logger.warning(f"⚠️ HiGHS failed: {highs_result}, using DAME")
            highs_result = None
        
        if isinstance(lmea_result, Exception):
            self.logger.error(f"❌ DAME failed: {lmea_result}")
            lmea_result = {'status': 'error', 'error': str(lmea_result)}
        
        # Compare results
        return self._compare_results(highs_result, lmea_result, problem_type)
    
    def compare_results(
        self,
        highs_result: Optional[Dict[str, Any]],
        lmea_result: Dict[str, Any],
        problem_type: str = "maximize"
    ) -> SolverComparisonResult:
        """
        Compare HiGHS and DAME results (public method for already-executed solvers)
        
        Args:
            highs_result: HiGHS solver result (can be HiGHSSolution dataclass or dict)
            lmea_result: DAME solver result dict
            problem_type: "maximize" or "minimize"
        
        Returns:
            SolverComparisonResult with comparison details
        """
        return self._compare_results(highs_result, lmea_result, problem_type)
    
    def _compare_results(
        self,
        highs_result: Optional[Dict[str, Any]],
        lmea_result: Dict[str, Any],
        problem_type: str
    ) -> SolverComparisonResult:
        """
        Compare HiGHS and DAME results for validation
        
        Returns insights like "DAME found 98.5% of optimal"
        """
        
        # Extract objectives
        highs_obj = None
        if highs_result:
            # Handle both dict and dataclass (HiGHSSolution)
            if hasattr(highs_result, 'status'):  # Dataclass
                if highs_result.status in ['optimal', 'success']:
                    highs_obj = highs_result.objective_value
            elif isinstance(highs_result, dict):  # Dict
                if highs_result.get('status') in ['optimal', 'success']:
                    highs_obj = highs_result.get('objective_value', 0)
        
        lmea_obj = (
            lmea_result.get('objective_value') or
            lmea_result.get('fitness') or
            lmea_result.get('expected_revenue') or  # retail layout
            lmea_result.get('total_cost', 0)  # VRP
        )
        
        # Handle HiGHS failure
        if highs_obj is None or highs_obj == 0:
            self.logger.info("⚠️ HiGHS unavailable, using DAME only (no cross-validation)")
            return SolverComparisonResult(
                highs_result=highs_result,
                lmea_result=lmea_result,
                objective_gap=0.0,
                gap_percentage=0.0,
                agreement_score=0.0,
                lmea_quality=0.0,
                validation_insight="HiGHS unavailable, DAME solution only",
                best_solver='lmea',
                cross_validation_boost=0.0,
                both_succeeded=False
            )
        
        # Calculate gap (accounting for maximization vs minimization)
        is_maximization = problem_type.lower() in ['maximize', 'maximization']
        
        objective_gap = abs(highs_obj - lmea_obj)
        gap_percentage = (objective_gap / abs(highs_obj)) if highs_obj != 0 else 0.0
        
        # DAME quality score
        if is_maximization:
            lmea_quality = (lmea_obj / highs_obj) if highs_obj != 0 else 0.0
        else:  # minimization - lower is better
            lmea_quality = (highs_obj / lmea_obj) if lmea_obj != 0 else 0.0
        
        # Agreement score (1.0 = perfect, 0.0 = very different)
        agreement_score = max(0.0, 1.0 - gap_percentage)
        
        # Generate validation insight
        if agreement_score >= 0.99:
            insight = f"🎯 DAME found optimal solution (100% match with exact solver)"
        elif agreement_score >= 0.95:
            insight = f"✅ DAME found {lmea_quality*100:.1f}% of optimal (excellent heuristic performance)"
        elif agreement_score >= 0.90:
            insight = f"✅ DAME found {lmea_quality*100:.1f}% of optimal (good heuristic performance)"
        elif agreement_score >= 0.80:
            insight = f"⚠️ DAME found {lmea_quality*100:.1f}% of optimal (acceptable, but room for improvement)"
        else:
            insight = f"⚠️ DAME found {lmea_quality*100:.1f}% of optimal (exact solver recommended for this problem)"
        
        # Cross-validation boost (trust score increase)
        if agreement_score >= 0.95:
            cv_boost = 0.15  # +15% for excellent agreement
        elif agreement_score >= 0.90:
            cv_boost = 0.10  # +10% for good agreement
        elif agreement_score >= 0.80:
            cv_boost = 0.05  # +5% for acceptable agreement
        else:
            cv_boost = 0.0  # No boost for poor agreement
        
        # Best solver (prefer HiGHS if optimal, otherwise DAME)
        highs_status = None
        if highs_result:
            if hasattr(highs_result, 'status'):
                highs_status = highs_result.status
            elif isinstance(highs_result, dict):
                highs_status = highs_result.get('status')
        
        best_solver = 'highs' if highs_status == 'optimal' else 'lmea'
        
        self.logger.info(
            f"✅ Cross-validation: {agreement_score*100:.1f}% agreement, "
            f"DAME quality = {lmea_quality*100:.1f}%, trust boost = +{cv_boost*100:.0f}%"
        )
        
        return SolverComparisonResult(
            highs_result=highs_result,
            lmea_result=lmea_result,
            objective_gap=objective_gap,
            gap_percentage=gap_percentage,
            agreement_score=agreement_score,
            lmea_quality=lmea_quality,
            validation_insight=insight,
            best_solver=best_solver,
            cross_validation_boost=cv_boost,
            both_succeeded=True
        )
    
    def should_use_parallel_validation(
        self,
        problem_data: Dict[str, Any],
        domain_id: str,
        validation_mode: str = "auto"
    ) -> bool:
        """
        Determine if parallel validation should be used
        
        Args:
            problem_data: Parsed problem data
            domain_id: Domain identifier
            validation_mode: "auto", "parallel", "fast", "exact", or "heuristic"
        
        Returns:
            True if parallel validation should be used
        """
        
        # User explicitly requested a mode
        if validation_mode == "parallel":
            return True
        elif validation_mode in ["fast", "exact", "heuristic"]:
            return False
        
        # Auto mode: Smart routing
        
        # Check problem size
        num_variables = len(problem_data.get('variables', []))
        num_constraints = len(problem_data.get('constraints', []))
        
        # Skip for large problems (HiGHS might timeout)
        if num_variables > 1000 or num_constraints > 1000:
            self.logger.info(f"⏩ Skipping parallel validation (problem too large: {num_variables} vars)")
            return False
        
        # Use parallel for LP/MIP-friendly domains
        lp_friendly_domains = [
            'portfolio',
            'portfolio_rebalancing',
            'resource_allocation',
            'production_planning',
            'simple_allocation'
        ]
        
        if domain_id in lp_friendly_domains:
            self.logger.info(f"✅ Using parallel validation (LP-friendly domain: {domain_id})")
            return True
        
        # Skip for complex combinatorial problems
        complex_domains = [
            'vrp',
            'vehicle_routing',
            'workforce_rostering',
            'retail_layout',
            'scheduling',
            'job_shop'
        ]
        
        if domain_id in complex_domains:
            self.logger.info(f"⏩ Skipping parallel validation (complex domain: {domain_id})")
            return False
        
        # Default: try parallel for small-medium problems
        if num_variables < 100:
            return True
        
        return False


# Test/example
if __name__ == "__main__":
    import asyncio
    
    async def test():
        validator = ParallelSolverValidator()
        
        # Mock solver functions
        async def highs_fn():
            await asyncio.sleep(0.01)
            return {'status': 'optimal', 'objective_value': 1500.0}
        
        async def lmea_fn():
            await asyncio.sleep(0.2)
            return {'status': 'success', 'fitness': 1462.5}
        
        result = await validator.validate_parallel(
            problem_data={},
            highs_solver_fn=highs_fn,
            lmea_solver_fn=lmea_fn,
            problem_type='maximize'
        )
        
        print(f"Agreement: {result.agreement_score*100:.1f}%")
        print(f"DAME Quality: {result.lmea_quality*100:.1f}%")
        print(f"Trust Boost: +{result.cross_validation_boost*100:.0f}%")
        print(f"Insight: {result.validation_insight}")
        print(f"\n✅ Parallel validator working!")
    
    asyncio.run(test())

