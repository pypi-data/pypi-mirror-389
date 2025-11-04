"""
Solvers Module - Exact Optimization Solvers

Provides interfaces to various optimization solvers:
- HiGHS: Open-source LP/MIP solver (MIT license)
- Future: CBC, SCIP, Gurobi, CPLEX
"""

from .highs_solver import HiGHSSolver

__all__ = ['HiGHSSolver']

