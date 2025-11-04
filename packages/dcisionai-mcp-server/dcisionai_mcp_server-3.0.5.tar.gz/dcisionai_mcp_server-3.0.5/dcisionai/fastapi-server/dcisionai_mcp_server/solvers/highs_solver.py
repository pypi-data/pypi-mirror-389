"""
HiGHS Solver Integration for DcisionAI Platform

HiGHS: High-performance open-source LP/MIP solver
- License: MIT (free for commercial use)
- Performance: Competitive with Gurobi/CPLEX
- Supports: LP, MIP, QP
- Website: https://highs.dev

Extracted from POC and enhanced for production use.
"""

import logging
import time
import subprocess
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class HiGHSSolution:
    """Result from HiGHS solver"""
    status: str  # "optimal", "infeasible", "unbounded", "timeout", "error"
    objective_value: float
    variables: Dict[str, float]  # variable_name -> value
    solve_time: float
    iterations: int
    gap: Optional[float] = None  # For MIP: optimality gap
    solver_output: Optional[str] = None  # Debug info


class HiGHSSolver:
    """
    Production HiGHS Solver Manager
    
    Handles LP and MIP problems with automatic installation and error handling.
    
    Example:
        solver = HiGHSSolver()
        result = await solver.solve_portfolio(
            returns=[0.08, 0.12, 0.10],
            budget=10000
        )
    """
    
    def __init__(self, auto_install: bool = True):
        """
        Initialize HiGHS solver
        
        Args:
            auto_install: Automatically install highspy if missing
        """
        self.logger = logging.getLogger(__name__)
        self.has_highs = False
        
        if auto_install:
            self.has_highs = self._ensure_highs_installed()
        else:
            self.has_highs = self._check_highs_available()
    
    def _check_highs_available(self) -> bool:
        """Check if HiGHS is already installed"""
        try:
            import highspy
            self.logger.info("✅ HiGHS solver available")
            return True
        except ImportError:
            self.logger.warning("⚠️ HiGHS not installed")
            return False
    
    def _ensure_highs_installed(self) -> bool:
        """
        Check if HiGHS is installed, install if missing
        
        Returns:
            True if HiGHS is available, False otherwise
        """
        if self._check_highs_available():
            return True
        
        # Try to install
        self.logger.info("📦 Installing HiGHS solver...")
        try:
            subprocess.check_call(
                ["pip", "install", "-q", "highspy>=1.7.0"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Check if installation succeeded
            if self._check_highs_available():
                self.logger.info("✅ HiGHS installed successfully")
                return True
            else:
                self.logger.error("❌ HiGHS installation failed")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Failed to install HiGHS: {e}")
            return False
    
    def can_solve_problem(self, problem_type: str) -> bool:
        """
        Check if HiGHS can solve this problem type
        
        Args:
            problem_type: Type of optimization problem
        
        Returns:
            True if HiGHS can handle this problem type
        """
        if not self.has_highs:
            return False
        
        # HiGHS supports: LP, MIP, QP
        supported_types = [
            "linear_programming",
            "mixed_integer_programming",
            "quadratic_programming",
            "portfolio",
            "resource_allocation",
            "production_planning"
        ]
        
        return problem_type.lower() in supported_types
    
    async def solve_portfolio(
        self,
        returns: List[float],
        budget: float,
        min_allocation: float = 0.0,
        max_allocation: Optional[float] = None,
        time_limit: Optional[float] = 30.0
    ) -> HiGHSSolution:
        """
        Solve portfolio optimization problem
        
        maximize: sum(returns[i] * allocation[i])
        subject to:
          - sum(allocation[i]) <= budget
          - min_allocation <= allocation[i] <= max_allocation
        
        Args:
            returns: Expected return for each asset
            budget: Total budget to allocate
            min_allocation: Minimum allocation per asset
            max_allocation: Maximum allocation per asset (or budget if None)
            time_limit: Maximum solve time in seconds
        
        Returns:
            HiGHSSolution with results
        """
        if not self.has_highs:
            return HiGHSSolution(
                status="error",
                objective_value=0.0,
                variables={},
                solve_time=0.0,
                iterations=0,
                solver_output="HiGHS not available"
            )
        
        import highspy
        
        start_time = time.time()
        
        try:
            # Create HiGHS model
            h = highspy.Highs()
            h.setOptionValue("output_flag", False)  # Quiet mode
            
            if time_limit:
                h.setOptionValue("time_limit", time_limit)
            
            n_assets = len(returns)
            max_alloc = max_allocation if max_allocation else budget
            
            # Add variables (allocations for each asset)
            # IMPORTANT: addVar() returns status, not index!
            # Variables are implicitly indexed 0, 1, 2, ... in creation order
            for i in range(n_assets):
                h.addVar(min_allocation, max_alloc)
            
            # Variable indices are just 0, 1, 2, ..., n-1
            var_indices = list(range(n_assets))
            
            # Add budget constraint: sum(allocations) <= budget
            coeffs = [1.0] * n_assets
            h.addRow(0, budget, n_assets, var_indices, coeffs)
            
            # Set objective sense first
            h.changeObjectiveSense(highspy.ObjSense.kMaximize)
            
            # Set objective coefficients: maximize sum(returns[i] * allocation[i])
            for i, var_idx in enumerate(var_indices):
                h.changeColCost(var_idx, returns[i])
            
            # Solve
            self.logger.info(f"🔧 Solving portfolio optimization with HiGHS ({n_assets} assets)")
            h.run()
            
            # Extract solution
            status = h.getModelStatus()
            info = h.getInfo()
            solution_data = h.getSolution()
            
            # Map status
            status_map = {
                highspy.HighsModelStatus.kOptimal: "optimal",
                highspy.HighsModelStatus.kInfeasible: "infeasible",
                highspy.HighsModelStatus.kUnbounded: "unbounded",
                highspy.HighsModelStatus.kTimeLimit: "timeout",
            }
            
            status_str = status_map.get(status, "unknown")
            
            # Extract allocations
            allocations = {f"asset_{i}": solution_data.col_value[i] for i in range(n_assets)}
            
            solve_time = time.time() - start_time
            
            self.logger.info(
                f"✅ HiGHS solved in {solve_time:.3f}s: {status_str}, "
                f"objective=${info.objective_function_value:,.2f}"
            )
            
            return HiGHSSolution(
                status=status_str,
                objective_value=info.objective_function_value,
                variables=allocations,
                solve_time=solve_time,
                iterations=info.simplex_iteration_count
            )
            
        except Exception as e:
            solve_time = time.time() - start_time
            self.logger.error(f"❌ HiGHS solve failed: {e}")
            
            return HiGHSSolution(
                status="error",
                objective_value=0.0,
                variables={},
                solve_time=solve_time,
                iterations=0,
                solver_output=str(e)
            )
    
    async def solve_generic_lp(
        self,
        objective_coeffs: List[float],
        constraint_matrix: List[List[float]],
        constraint_bounds: List[Tuple[float, float]],
        variable_bounds: List[Tuple[float, float]],
        sense: str = "maximize",
        time_limit: Optional[float] = 30.0
    ) -> HiGHSSolution:
        """
        Solve generic LP problem
        
        optimize: sum(objective_coeffs[i] * x[i])
        subject to:
          - constraint_matrix @ x in constraint_bounds
          - x[i] in variable_bounds[i]
        
        Args:
            objective_coeffs: Objective function coefficients
            constraint_matrix: Constraint matrix (rows = constraints, cols = variables)
            constraint_bounds: (lower, upper) bounds for each constraint
            variable_bounds: (lower, upper) bounds for each variable
            sense: "maximize" or "minimize"
            time_limit: Maximum solve time in seconds
        
        Returns:
            HiGHSSolution with results
        """
        if not self.has_highs:
            return HiGHSSolution(
                status="error",
                objective_value=0.0,
                variables={},
                solve_time=0.0,
                iterations=0,
                solver_output="HiGHS not available"
            )
        
        import highspy
        
        start_time = time.time()
        
        try:
            h = highspy.Highs()
            h.setOptionValue("output_flag", False)
            
            if time_limit:
                h.setOptionValue("time_limit", time_limit)
            
            n_vars = len(objective_coeffs)
            n_constraints = len(constraint_matrix)
            
            # Add variables
            for lb, ub in variable_bounds:
                h.addVar(lb, ub)
            
            var_indices = list(range(n_vars))
            
            # Add constraints
            for i, row in enumerate(constraint_matrix):
                lower, upper = constraint_bounds[i]
                # Find non-zero entries
                nonzero_indices = [j for j, val in enumerate(row) if val != 0]
                nonzero_coeffs = [row[j] for j in nonzero_indices]
                
                if nonzero_indices:  # Only add if non-empty
                    h.addRow(lower, upper, len(nonzero_indices), nonzero_indices, nonzero_coeffs)
            
            # Set objective
            if sense.lower() == "maximize":
                h.changeObjectiveSense(highspy.ObjSense.kMaximize)
            else:
                h.changeObjectiveSense(highspy.ObjSense.kMinimize)
            
            for i, coeff in enumerate(objective_coeffs):
                h.changeColCost(i, coeff)
            
            # Solve
            self.logger.info(f"🔧 Solving LP with HiGHS ({n_vars} vars, {n_constraints} constraints)")
            h.run()
            
            # Extract solution
            status = h.getModelStatus()
            info = h.getInfo()
            solution_data = h.getSolution()
            
            status_map = {
                highspy.HighsModelStatus.kOptimal: "optimal",
                highspy.HighsModelStatus.kInfeasible: "infeasible",
                highspy.HighsModelStatus.kUnbounded: "unbounded",
                highspy.HighsModelStatus.kTimeLimit: "timeout",
            }
            
            status_str = status_map.get(status, "unknown")
            
            variables = {f"x{i}": solution_data.col_value[i] for i in range(n_vars)}
            
            solve_time = time.time() - start_time
            
            self.logger.info(
                f"✅ HiGHS solved in {solve_time:.3f}s: {status_str}, "
                f"objective={info.objective_function_value:.4f}"
            )
            
            return HiGHSSolution(
                status=status_str,
                objective_value=info.objective_function_value,
                variables=variables,
                solve_time=solve_time,
                iterations=info.simplex_iteration_count
            )
            
        except Exception as e:
            solve_time = time.time() - start_time
            self.logger.error(f"❌ HiGHS solve failed: {e}")
            
            return HiGHSSolution(
                status="error",
                objective_value=0.0,
                variables={},
                solve_time=solve_time,
                iterations=0,
                solver_output=str(e)
            )


# Quick test/example
if __name__ == "__main__":
    import asyncio
    
    async def test():
        solver = HiGHSSolver()
        
        if not solver.has_highs:
            print("❌ HiGHS not available")
            return
        
        print("Testing HiGHS solver...")
        
        # Simple portfolio
        returns = [0.08, 0.12, 0.10, 0.15, 0.09]
        budget = 10000.0
        
        result = await solver.solve_portfolio(returns, budget)
        
        print(f"\nStatus: {result.status}")
        print(f"Objective: ${result.objective_value:,.2f}")
        print(f"Solve time: {result.solve_time:.3f}s")
        print(f"Allocations:")
        for var, val in result.variables.items():
            print(f"  {var}: ${val:,.2f}")
        
        if result.status == "optimal":
            print("\n✅ HiGHS solver working in production!")
    
    asyncio.run(test())

