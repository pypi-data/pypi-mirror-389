"""
Domain-Specific HiGHS Adapters

Adapt parsed problem data into HiGHS-solvable models for specific domains.
Based on working examples from highs_usecases.py
"""

import logging
import time
from typing import Dict, Any, List
from .highs_solver import HiGHSSolver, HiGHSSolution

logger = logging.getLogger(__name__)


class PortfolioHiGHSAdapter:
    """Adapter for portfolio optimization problems"""
    
    def __init__(self):
        self.solver = HiGHSSolver()
    
    async def solve(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Solve portfolio optimization using HiGHS
        
        Expected parsed_data:
        {
            'assets': List of asset names,
            'returns': List of expected returns,
            'budget': Total budget,
            'max_allocation': Optional max per asset
        }
        """
        logger.info("🎯 Portfolio optimization with HiGHS")
        
        try:
            # Extract data
            assets = parsed_data.get('assets', [])
            returns = parsed_data.get('returns', parsed_data.get('expected_returns', []))
            budget = parsed_data.get('budget', parsed_data.get('total_capital', 0))
            
            if not returns or not budget:
                raise ValueError("Missing returns or budget")
            
            # Solve using HiGHS
            result = await self.solver.solve_portfolio(
                returns=returns,
                budget=budget
            )
            
            # Format results
            if result.status == "optimal":
                allocations = [
                    {
                        'asset': assets[i] if i < len(assets) else f"Asset {i}",
                        'allocation': result.variables[f"asset_{i}"],
                        'return': returns[i]
                    }
                    for i in range(len(returns))
                    if result.variables.get(f"asset_{i}", 0) > 0.01
                ]
                
                return {
                    'status': 'success',
                    'solver': 'highs',
                    'objective_value': result.objective_value,
                    'expected_return': result.objective_value,
                    'fitness': result.objective_value,
                    'allocations': allocations,
                    'solve_time': result.solve_time,
                    'iterations': result.iterations,
                    'optimality': 'optimal',
                    'solution': {
                        'allocations': [result.variables.get(f"asset_{i}", 0) for i in range(len(returns))]
                    }
                }
            else:
                return {
                    'status': 'error',
                    'error': f"HiGHS returned {result.status}",
                    'solver_output': result.solver_output
                }
                
        except Exception as e:
            logger.error(f"❌ Portfolio HiGHS adapter failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }


class StoreLayoutHiGHSAdapter:
    """Adapter for store layout optimization (assignment problem)"""
    
    def __init__(self):
        self.solver = HiGHSSolver()
    
    async def solve(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Solve store layout optimization using HiGHS
        
        Expected parsed_data:
        {
            'products': List of product names,
            'slots': List of slot names,
            'profit_scores': Matrix [product][slot] -> score
        }
        """
        logger.info("🎯 Store layout optimization with HiGHS")
        
        try:
            import highspy
            
            products = parsed_data.get('products', [])
            slots = parsed_data.get('slots', [])
            scores = parsed_data.get('profit_scores', parsed_data.get('scores', []))
            
            if not products or not slots or not scores:
                raise ValueError("Missing products, slots, or scores")
            
            n_products = len(products)
            n_slots = len(slots)
            
            # Create HiGHS model
            h = highspy.Highs()
            h.setOptionValue("output_flag", False)
            
            # Variables: x[p,s] = 1 if product p in slot s
            for p in range(n_products):
                for s in range(n_slots):
                    var_idx = h.addVar(0, 1)
                    h.changeColIntegrality(var_idx, highspy.HighsVarType.kInteger)
            
            # Constraint 1: Each product in exactly 1 slot
            for p in range(n_products):
                indices = [p * n_slots + s for s in range(n_slots)]
                coeffs = [1.0] * n_slots
                h.addRow(1, 1, n_slots, indices, coeffs)
            
            # Constraint 2: Each slot has at most 1 product
            for s in range(n_slots):
                indices = [p * n_slots + s for p in range(n_products)]
                coeffs = [1.0] * n_products
                h.addRow(0, 1, n_products, indices, coeffs)
            
            # Objective: maximize profit
            h.changeObjectiveSense(highspy.ObjSense.kMaximize)
            for p in range(n_products):
                for s in range(n_slots):
                    var_idx = p * n_slots + s
                    # Get score from matrix or dict
                    if isinstance(scores, list) and isinstance(scores[p], list):
                        score = scores[p][s]
                    else:
                        # Dict format: scores[product_name][slot_name]
                        score = scores.get(products[p], {}).get(slots[s], 0)
                    h.changeColCost(var_idx, score)
            
            # Solve
            start = time.time()
            h.run()
            solve_time = time.time() - start
            
            # Extract solution
            sol = h.getSolution()
            info = h.getInfo()
            status = h.getModelStatus()
            
            if status == highspy.HighsModelStatus.kOptimal:
                # Extract assignments
                assignments = []
                for p in range(n_products):
                    for s in range(n_slots):
                        var_idx = p * n_slots + s
                        if sol.col_value[var_idx] > 0.5:
                            # Get score from matrix or dict
                            if isinstance(scores, list) and isinstance(scores[p], list):
                                score = scores[p][s]
                            else:
                                # Dict format: scores[product_name][slot_name]
                                score = scores.get(products[p], {}).get(slots[s], 0)
                            assignments.append({
                                'product': products[p],
                                'slot': slots[s],
                                'score': score
                            })
                
                return {
                    'status': 'success',
                    'solver': 'highs',
                    'objective_value': info.objective_function_value,
                    'expected_revenue': info.objective_function_value,
                    'fitness': info.objective_function_value,
                    'assignments': assignments,
                    'solve_time': solve_time,
                    'optimality': 'optimal',
                    'solution': {
                        'assignments': assignments
                    }
                }
            else:
                return {
                    'status': 'error',
                    'error': f"HiGHS returned {h.modelStatusToString(status)}"
                }
                
        except Exception as e:
            logger.error(f"❌ Store layout HiGHS adapter failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'error',
                'error': str(e)
            }


# Factory function to get the right adapter
def get_highs_adapter(domain_id: str):
    """Get domain-specific HiGHS adapter"""
    adapters = {
        'portfolio': PortfolioHiGHSAdapter,
        'portfolio_rebalancing': PortfolioHiGHSAdapter,
        'retail_layout': StoreLayoutHiGHSAdapter,
        'store_layout': StoreLayoutHiGHSAdapter,
    }
    
    adapter_class = adapters.get(domain_id)
    if adapter_class:
        return adapter_class()
    return None

