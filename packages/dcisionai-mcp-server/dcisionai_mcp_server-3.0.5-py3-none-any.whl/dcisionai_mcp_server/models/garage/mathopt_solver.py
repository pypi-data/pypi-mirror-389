#!/usr/bin/env python3
"""
MathOpt Solver - Real OR-Tools MathOpt Implementation
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Try to import OR-Tools MathOpt components
try:
    from ortools.math_opt.python import model
    from ortools.math_opt.python import solve
    from ortools.math_opt.python.parameters import SolverType
    HAS_MATHOPT = True
    logger.info("OR-Tools MathOpt available for solving")
except ImportError as e:
    HAS_MATHOPT = False
    logger.warning(f"OR-Tools MathOpt not available: {e}")


class MathOptSolver:
    """Real MathOpt solver using OR-Tools MathOpt API"""

    def __init__(self):
        self.model = None
        self.variables = {}
        self.constraints = []
        self.objective = None

    def solve_model(self, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """Solve a model using real OR-Tools MathOpt"""
        if not HAS_MATHOPT:
            return {
                'status': 'error',
                'error': 'OR-Tools MathOpt not available',
                'message': 'OR-Tools MathOpt library not installed'
            }

        try:
            # Create a new MathOpt model
            self.model = model.Model()
            self.variables = {}
            self.constraints = []
            
            # Add variables
            variables_data = model_data.get('variables', [])
            for var_data in variables_data:
                if isinstance(var_data, dict):
                    name = var_data.get('name', f'x{len(self.variables)}')
                    var_type = var_data.get('type', 'continuous')
                    bounds = var_data.get('bounds', '0 to inf')
                    
                    # Parse bounds
                    lower, upper = self._parse_bounds(bounds)
                    
                    # Create variable based on type
                    if var_type == 'binary':
                        var = self.model.add_binary_variable(name=name)
                    elif var_type == 'integer':
                        var = self.model.add_integer_variable(lb=lower, ub=upper, name=name)
                    else:  # continuous
                        var = self.model.add_variable(lb=lower, ub=upper, name=name)
                    
                    self.variables[name] = var
                    logger.info(f"Added variable: {name} ({var_type}) [{lower}, {upper}]")
            
            # Add objective
            objective_data = model_data.get('objective', {})
            if objective_data:
                obj_type = objective_data.get('type', 'maximize')
                obj_expression = objective_data.get('expression', '')
                
                # Parse objective expression
                obj_expr = self._parse_expression(obj_expression)
                if obj_expr is not None:
                    if obj_type == 'maximize':
                        self.model.maximize(obj_expr)
                    else:
                        self.model.minimize(obj_expr)
                    logger.info(f"Set objective: {obj_type} {obj_expression}")
            
            # Add constraints
            constraints_data = model_data.get('constraints', [])
            for i, constraint_data in enumerate(constraints_data):
                if isinstance(constraint_data, dict):
                    expression = constraint_data.get('expression', '')
                    description = constraint_data.get('description', f'Constraint {i+1}')
                    
                    # Parse constraint expression
                    constraint = self._parse_constraint(expression)
                    if constraint is not None:
                        self.model.add_linear_constraint(constraint)
                        self.constraints.append(constraint)
                        logger.info(f"Added constraint: {expression}")
            
            # Solve the model - use appropriate solver based on model type
            has_integer_vars = any(var_data.get('type') in ['integer', 'binary'] for var_data in model_data.get('variables', []))
            model_type = model_data.get('model_type', 'linear_programming')
            
            # Select solver based on model type
            if has_integer_vars or 'mixed_integer' in model_type.lower():
                solver_type = SolverType.CP_SAT
                logger.info("Using CP_SAT for mixed integer programming")
            elif 'quadratic' in model_type.lower():
                # For quadratic programming, use GLOP as fallback since OSQP may not be available
                # TODO: Add proper OSQP support when available in OR-Tools
                solver_type = SolverType.GLOP
                logger.warning("Using GLOP for quadratic programming (OSQP not available in this OR-Tools installation)")
            else:
                solver_type = SolverType.GLOP
                logger.info("Using GLOP for linear programming")
            
            logger.info(f"Solving MathOpt model with {solver_type}...")
            result = solve.solve(self.model, solver_type)
            
            # Check if solution is optimal
            termination_reason = str(result.termination.reason)
            if 'OPTIMAL' in termination_reason:
                # Extract solution
                optimal_values = {}
                for name, var in self.variables.items():
                    optimal_values[name] = result.variable_values().get(var, 0.0)
                
                objective_value = result.objective_value()
                
                # Handle solve time - it might be a function or a timedelta
                solve_time = 0.0
                try:
                    if hasattr(result.solve_time, 'total_seconds'):
                        solve_time = result.solve_time.total_seconds()
                    elif callable(result.solve_time):
                        solve_time = result.solve_time()
                    else:
                        solve_time = float(result.solve_time)
                except:
                    solve_time = 0.0
                
                return {
                    'status': 'optimal',
                    'objective_value': objective_value,
                    'optimal_values': optimal_values,
                    'solve_time': solve_time,
                    'solver': 'OR-Tools MathOpt',
                    'message': 'Solved successfully with OR-Tools MathOpt'
                }
            else:
                return {
                    'status': 'error',
                    'error': f'Solver terminated with reason: {result.termination.reason}',
                    'message': 'MathOpt solver could not find optimal solution'
                }
                
        except Exception as e:
            logger.error(f"MathOpt solving failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'message': 'Failed to solve with OR-Tools MathOpt'
            }

    def _parse_bounds(self, bounds_str: str) -> tuple:
        """Parse bounds string to (lower, upper) tuple"""
        bounds_str = bounds_str.lower().strip()
        
        if 'to' in bounds_str:
            parts = bounds_str.split('to')
            lower = float(parts[0].strip()) if parts[0].strip() != '-inf' else float('-inf')
            upper = float(parts[1].strip()) if parts[1].strip() != 'inf' else float('inf')
        elif bounds_str == 'binary':
            return (0, 1)
        else:
            # Default bounds
            lower, upper = 0, float('inf')
        
        return (lower, upper)

    def _parse_expression(self, expr: str):
        """Parse mathematical expression into MathOpt expression"""
        try:
            # For now, handle simple linear expressions
            # This is a simplified parser - in production, you'd want a more robust one
            
            # Handle simple cases like "25*x1 + 60*x2 + 120*x3"
            if '+' in expr or '-' in expr:
                # Split by + and - operators
                import re
                terms = re.split(r'[+\-]', expr)
                operators = re.findall(r'[+\-]', expr)
                
                result = None
                for i, term in enumerate(terms):
                    term = term.strip()
                    if not term:
                        continue
                    
                    # Parse coefficient and variable
                    coeff, var_name = self._parse_term(term)
                    if coeff is not None and var_name in self.variables:
                        var = self.variables[var_name]
                        term_expr = coeff * var
                        
                        if result is None:
                            result = term_expr
                        else:
                            # Apply operator
                            if i > 0 and operators[i-1] == '-':
                                result = result - term_expr
                            else:
                                result = result + term_expr
                    else:
                        # Variable not found - this is a constraint parsing issue
                        logger.warning(f"Variable '{var_name}' not found in variables dict for expression '{expr}'")
                        return None
                
                return result
            else:
                # Single term
                coeff, var_name = self._parse_term(expr)
                if coeff is not None and var_name in self.variables:
                    return coeff * self.variables[var_name]
                else:
                    # Variable not found - this is a constraint parsing issue
                    logger.warning(f"Variable '{var_name}' not found in variables dict for expression '{expr}'")
                    return None
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to parse expression '{expr}': {e}")
            return None

    def _parse_term(self, term: str):
        """Parse a single term like '25*x1' into (coefficient, variable_name)"""
        try:
            import re
            
            # Pattern for coefficient*variable
            match = re.match(r'([\d.]+)\s*\*\s*([a-zA-Z_][a-zA-Z0-9_]*)', term)
            if match:
                coeff = float(match.group(1))
                var_name = match.group(2)
                return coeff, var_name
            
            # Pattern for just variable (coefficient = 1)
            match = re.match(r'([a-zA-Z_][a-zA-Z0-9_]*)', term)
            if match:
                var_name = match.group(1)
                return 1.0, var_name
            
            return None, None
            
        except Exception as e:
            logger.warning(f"Failed to parse term '{term}': {e}")
            return None, None

    def _parse_constraint(self, expr: str):
        """Parse constraint expression into MathOpt constraint"""
        try:
            # Handle ellipsis expressions first
            expr = self._expand_ellipsis(expr)
            
            # Handle indexed constraints like "chairs_day[i] <= 200 for all i"
            if ' for all ' in expr:
                expr = expr.split(' for all ')[0].strip()
            
            # Handle sum constraints like "sum(chairs_day[i])"
            if 'sum(' in expr and ')' in expr:
                expr = self._expand_sum_expression(expr)
            
            # Handle range constraints like "3000 <= chairs_day1 + ... + chairs_day30 <= 5000"
            if ' <= ' in expr and expr.count(' <= ') == 2:
                parts = expr.split(' <= ')
                if len(parts) == 3:
                    lower_bound = float(parts[0].strip())
                    middle_expr = parts[1].strip()
                    upper_bound = float(parts[2].strip())
                    
                    middle_parsed = self._parse_expression(middle_expr)
                    if middle_parsed is not None:
                        # Create two separate constraints
                        lower_constraint = middle_parsed >= lower_bound
                        upper_constraint = middle_parsed <= upper_bound
                        
                        # Add both constraints to the model
                        self.model.add_linear_constraint(lower_constraint)
                        self.model.add_linear_constraint(upper_constraint)
                        logger.info(f"Added range constraint: {lower_bound} <= {middle_expr} <= {upper_bound}")
                        return lower_constraint  # Return one of them for the constraint list
            
            # Handle simple constraints like "x1 + x2 <= 100"
            elif '<=' in expr:
                left, right = expr.split('<=', 1)
                left_expr = self._parse_expression(left.strip())
                
                # Check if right side is a numeric value or an expression
                try:
                    right_val = float(right.strip())
                    # Simple numeric constraint
                    if left_expr is not None:
                        return left_expr <= right_val
                except ValueError:
                    # Right side is an expression (mixed-integer constraint)
                    right_expr = self._parse_expression(right.strip())
                    if left_expr is not None and right_expr is not None:
                        return left_expr <= right_expr
                    else:
                        logger.warning(f"Failed to parse mixed-integer constraint: {expr}")
                        return None
            
            elif '>=' in expr:
                left, right = expr.split('>=', 1)
                left_expr = self._parse_expression(left.strip())
                
                # Check if right side is a numeric value or an expression
                try:
                    right_val = float(right.strip())
                    # Simple numeric constraint
                    if left_expr is not None:
                        return left_expr >= right_val
                except ValueError:
                    # Right side is an expression (mixed-integer constraint)
                    right_expr = self._parse_expression(right.strip())
                    if left_expr is not None and right_expr is not None:
                        return left_expr >= right_expr
                    else:
                        logger.warning(f"Failed to parse mixed-integer constraint: {expr}")
                        return None
            
            elif '==' in expr or '=' in expr:
                left, right = expr.split('==' if '==' in expr else '=', 1)
                left_expr = self._parse_expression(left.strip())
                right_val = float(right.strip())
                
                if left_expr is not None:
                    return left_expr == right_val
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to parse constraint '{expr}': {e}")
            return None

    def _expand_ellipsis(self, expr: str) -> str:
        """Expand ellipsis expressions like 'chairs_day1 + ... + chairs_day30'"""
        try:
            import re
            
            # Handle ellipsis expressions like "chairs_day1+...+chairs_day30"
            ellipsis_pattern = r'([a-zA-Z_]+day\d+)\+\.\.\.\+([a-zA-Z_]+day\d+)'
            ellipsis_match = re.search(ellipsis_pattern, expr)
            if ellipsis_match:
                start_var = ellipsis_match.group(1)
                end_var = ellipsis_match.group(2)
                
                # Extract base name and day numbers
                start_base = re.match(r'([a-zA-Z_]+)day(\d+)', start_var)
                end_base = re.match(r'([a-zA-Z_]+)day(\d+)', end_var)
                
                if start_base and end_base and start_base.group(1) == end_base.group(1):
                    base_name = start_base.group(1)
                    start_day = int(start_base.group(2))
                    end_day = int(end_base.group(2))
                    
                    # Generate all variables in the range that exist
                    all_vars = []
                    for day in range(start_day, end_day + 1):
                        var_name = f"{base_name}day{day}"
                        if var_name in self.variables:
                            all_vars.append(var_name)
                    
                    if all_vars:
                        # Replace ellipsis with actual variable list
                        ellipsis_replacement = ' + '.join(all_vars)
                        expr = expr.replace(ellipsis_match.group(0), ellipsis_replacement)
                        logger.info(f"Expanded ellipsis: {ellipsis_match.group(0)} -> {ellipsis_replacement}")
                    else:
                        # No variables exist in the range - this is a model design issue
                        # For now, use the first available variable of this type
                        matching_vars = [var for var in self.variables.keys() if var.startswith(base_name)]
                        if matching_vars:
                            # Use the first variable and scale by the number of days
                            num_days = end_day - start_day + 1
                            expr = expr.replace(ellipsis_match.group(0), f"{num_days} * {matching_vars[0]}")
                            logger.warning(f"No variables in range {start_day}-{end_day}, using scaled single variable: {num_days} * {matching_vars[0]}")
                        else:
                            # No variables of this type exist - use 0
                            logger.warning(f"No variables of type {base_name} exist, using 0")
                            expr = expr.replace(ellipsis_match.group(0), "0")
            
            return expr
            
        except Exception as e:
            logger.warning(f"Failed to expand ellipsis in '{expr}': {e}")
            return expr
    
    def _expand_sum_expression(self, expr: str) -> str:
        """Expand sum expressions like 'sum(chairs_day[i])'"""
        try:
            import re
            
            # Handle sum expressions like "sum(chairs_day[i])"
            sum_pattern = r'sum\(([^)]+)\)'
            sum_match = re.search(sum_pattern, expr)
            
            if sum_match:
                inner_expr = sum_match.group(1)
                
                # If it's an indexed variable like "chairs_day[i]"
                if '[' in inner_expr and ']' in inner_expr:
                    var_base = inner_expr.split('[')[0]
                    
                    # Find all variables that match this pattern
                    matching_vars = [var for var in self.variables.keys() if var.startswith(var_base)]
                    
                    if matching_vars:
                        # Replace sum with actual variable list
                        sum_replacement = ' + '.join(matching_vars)
                        expr = expr.replace(sum_match.group(0), sum_replacement)
                        logger.info(f"Expanded sum: {sum_match.group(0)} -> {sum_replacement}")
                    else:
                        # No matching variables - use a single variable if available
                        if var_base in self.variables:
                            expr = expr.replace(sum_match.group(0), var_base)
                            logger.warning(f"No indexed variables found, using single variable: {var_base}")
                        else:
                            # No variables of this type exist
                            logger.warning(f"No variables of type {var_base} exist, using 0")
                            expr = expr.replace(sum_match.group(0), "0")
            
            return expr
            
        except Exception as e:
            logger.warning(f"Failed to expand sum expression in '{expr}': {e}")
            return expr
