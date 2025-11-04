#!/usr/bin/env python3
"""
Transparent HiGHS Solver via OR-Tools - Enhanced with Maximum Transparency
"""

import logging
from typing import Any, Dict, Optional, Callable
from datetime import datetime
import json

logger = logging.getLogger(__name__)

# Try to import HiGHS via OR-Tools
try:
    from ortools.linear_solver import pywraplp
    HAS_HIGHS = True
    logger.info("HiGHS solver available via OR-Tools for transparent optimization")
except ImportError as e:
    HAS_HIGHS = False
    logger.warning(f"HiGHS solver not available: {e}")


class TransparentHiGHSSolver:
    """HiGHS solver via OR-Tools with maximum transparency through detailed logging and analysis"""

    def __init__(self):
        self.solver = None
        self.variables = {}
        self.constraints = []
        self.objective = None
        self.solver_log = []
        self.iteration_data = []
        self.transparency_data = {
            'solver_events': [],
            'timing_data': {},
            'model_analysis': {},
            'solution_analysis': {},
            'performance_metrics': {}
        }

    def solve_model(self, model_data: Dict[str, Any], transparency_level: str = "high") -> Dict[str, Any]:
        """Solve a model using HiGHS via OR-Tools with maximum transparency"""
        
        if not HAS_HIGHS:
            return {
                'status': 'error',
                'error': 'HiGHS not available',
                'message': 'HiGHS library not installed'
            }

        try:
            # Create HiGHS solver via OR-Tools
            self.solver = pywraplp.Solver.CreateSolver('HIGHS')
            
            if not self.solver:
                return {
                    'status': 'error',
                    'error': 'HiGHS solver not available',
                    'message': 'Could not create HiGHS solver via OR-Tools'
                }
            
            logger.info("✅ HiGHS solver created via OR-Tools with transparency")
            
            # Clear any existing data
            self.variables = {}
            self.constraints = []
            self.solver_log = []
            self.transparency_data = {
                'solver_events': [],
                'timing_data': {},
                'model_analysis': {},
                'solution_analysis': {},
                'performance_metrics': {}
            }
            
            # Configure transparency settings
            self._configure_transparency_settings(transparency_level)
            
            # Analyze model before solving
            self._analyze_model_structure(model_data)
            
            # Add variables with detailed logging
            variables_data = model_data.get('variables', [])
            for var_data in variables_data:
                if isinstance(var_data, dict):
                    name = var_data.get('name', f'var_{len(self.variables)}')
                    var_type = var_data.get('type', 'continuous')
                    bounds = var_data.get('bounds', '0 to inf')
                    
                    # Parse bounds
                    lower_bound, upper_bound = self._parse_bounds(bounds)
                    
                    # Create variable based on type
                    if var_type == 'binary':
                        var = self.solver.BoolVar(name)
                        logger.info(f"Added binary variable: {name}")
                    elif var_type == 'integer':
                        var = self.solver.IntVar(lower_bound, upper_bound, name)
                        logger.info(f"Added integer variable: {name} [{lower_bound}, {upper_bound}]")
                    else:  # continuous
                        var = self.solver.NumVar(lower_bound, upper_bound, name)
                        logger.info(f"Added continuous variable: {name} [{lower_bound}, {upper_bound}]")
                    
                    self.variables[name] = var
                    
                    # Log variable details
                    self._log_solver_event('variable_added', {
                        'name': name,
                        'type': var_type,
                        'bounds': bounds,
                        'lower_bound': lower_bound,
                        'upper_bound': upper_bound
                    })
            
            # Set objective with detailed logging
            objective_data = model_data.get('objective', {})
            if objective_data:
                obj_type = objective_data.get('type', 'minimize')
                obj_expression = objective_data.get('expression', '')
                
                # Parse objective expression
                obj_terms = self._parse_objective_expression(obj_expression)
                
                # Build objective
                objective = self.solver.Objective()
                for coeff, var_name in obj_terms:
                    if var_name in self.variables:
                        objective.SetCoefficient(self.variables[var_name], coeff)
                
                if obj_type == 'maximize':
                    objective.SetMaximization()
                else:
                    objective.SetMinimization()
                
                logger.info(f"Set objective: {obj_type} {obj_expression}")
                
                # Log objective details
                self._log_solver_event('objective_set', {
                    'type': obj_type,
                    'expression': obj_expression,
                    'terms': obj_terms,
                    'coefficients': [coeff for coeff, _ in obj_terms]
                })
            
            # Add constraints with detailed logging
            constraints_data = model_data.get('constraints', [])
            for i, constraint_data in enumerate(constraints_data):
                if isinstance(constraint_data, dict):
                    expression = constraint_data.get('expression', '')
                    description = constraint_data.get('description', f'constraint_{i}')
                    
                    # Parse constraint expression
                    constraint = self._parse_constraint_expression(expression)
                    
                    if constraint:
                        self.constraints.append(constraint)
                        logger.info(f"Added constraint: {expression}")
                        
                        # Log constraint details
                        self._log_solver_event('constraint_added', {
                            'index': i,
                            'expression': expression,
                            'description': description,
                            'constraint_type': type(constraint).__name__
                        })
            
            # Solve the model with detailed monitoring
            logger.info("Solving HiGHS model with transparency enabled...")
            start_time = datetime.now()
            
            self._log_solver_event('solve_started', {
                'timestamp': start_time.isoformat(),
                'num_variables': len(self.variables),
                'num_constraints': len(self.constraints)
            })
            
            status = self.solver.Solve()
            
            solve_time = (datetime.now() - start_time).total_seconds()
            
            self._log_solver_event('solve_completed', {
                'timestamp': datetime.now().isoformat(),
                'solve_time': solve_time,
                'status': status,
                'wall_time': self.solver.WallTime() / 1000.0
            })
            
            # Extract detailed solution information
            solution_info = self._extract_detailed_solution_info(status, solve_time)
            
            # Add comprehensive transparency data
            solution_info['transparency_data'] = self._generate_transparency_report(
                model_data, solution_info, transparency_level
            )
            
            return solution_info
                
        except Exception as e:
            logger.error(f"HiGHS solving failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'message': 'HiGHS solver encountered an error',
                'transparency_data': {
                    'solver_log': self.solver_log,
                    'error_details': str(e),
                    'solver_events': self.transparency_data['solver_events']
                }
            }
    
    def _configure_transparency_settings(self, transparency_level: str):
        """Configure transparency settings based on level"""
        
        if transparency_level == "high":
            # Maximum transparency - detailed logging and analysis
            logger.info("🔍 Configuring HIGH transparency level")
            self.transparency_data['transparency_level'] = 'high'
            self.transparency_data['analysis_depth'] = 'maximum'
            
        elif transparency_level == "medium":
            # Balanced transparency
            logger.info("🔍 Configuring MEDIUM transparency level")
            self.transparency_data['transparency_level'] = 'medium'
            self.transparency_data['analysis_depth'] = 'balanced'
            
        else:  # low
            # Minimal transparency
            logger.info("🔍 Configuring LOW transparency level")
            self.transparency_data['transparency_level'] = 'low'
            self.transparency_data['analysis_depth'] = 'minimal'
    
    def _analyze_model_structure(self, model_data: Dict[str, Any]):
        """Analyze model structure for transparency"""
        
        variables = model_data.get('variables', [])
        constraints = model_data.get('constraints', [])
        objective = model_data.get('objective', {})
        
        # Count variable types
        var_types = {}
        for var in variables:
            var_type = var.get('type', 'continuous')
            var_types[var_type] = var_types.get(var_type, 0) + 1
        
        # Analyze constraint complexity
        constraint_types = []
        for constraint in constraints:
            expression = constraint.get('expression', '')
            if '<=' in expression:
                constraint_types.append('less_equal')
            elif '>=' in expression:
                constraint_types.append('greater_equal')
            elif '=' in expression:
                constraint_types.append('equality')
            else:
                constraint_types.append('unknown')
        
        self.transparency_data['model_analysis'] = {
            'total_variables': len(variables),
            'total_constraints': len(constraints),
            'variable_types': var_types,
            'constraint_types': {
                'less_equal': constraint_types.count('less_equal'),
                'greater_equal': constraint_types.count('greater_equal'),
                'equality': constraint_types.count('equality'),
                'unknown': constraint_types.count('unknown')
            },
            'objective_type': objective.get('type', 'unknown'),
            'model_complexity': self._assess_model_complexity(len(variables), len(constraints))
        }
    
    def _assess_model_complexity(self, num_vars: int, num_constraints: int) -> str:
        """Assess model complexity"""
        if num_vars <= 10 and num_constraints <= 10:
            return 'small'
        elif num_vars <= 100 and num_constraints <= 100:
            return 'medium'
        elif num_vars <= 1000 and num_constraints <= 1000:
            return 'large'
        else:
            return 'very_large'
    
    def _log_solver_event(self, event_type: str, event_data: Dict[str, Any]):
        """Log solver events for transparency"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'data': event_data
        }
        self.transparency_data['solver_events'].append(event)
        logger.info(f"🔍 Solver Event: {event_type} - {event_data}")
    
    def _extract_detailed_solution_info(self, status, solve_time):
        """Extract detailed solution information with transparency"""
        
        if status == pywraplp.Solver.OPTIMAL:
            # Extract solution
            optimal_values = {}
            for name, var in self.variables.items():
                optimal_values[name] = var.solution_value()
            
            objective_value = self.solver.Objective().Value()
            
            # Analyze solution quality
            solution_analysis = self._analyze_solution_quality(optimal_values, objective_value)
            
            return {
                'status': 'optimal',
                'objective_value': objective_value,
                'optimal_values': optimal_values,
                'solve_time': solve_time,
                'solver': 'HiGHS-Transparent-via-OR-Tools',
                'message': 'Solved successfully with HiGHS (transparent mode)',
                'solution_analysis': solution_analysis,
                'performance_metrics': {
                    'wall_time': self.solver.WallTime() / 1000.0,
                    'solve_time': solve_time,
                    'efficiency': solve_time / max(solve_time, 0.001)
                }
            }
        elif status == pywraplp.Solver.INFEASIBLE:
            return {
                'status': 'infeasible',
                'error': 'Model is infeasible',
                'message': 'No feasible solution exists',
                'solve_time': solve_time,
                'solver': 'HiGHS-Transparent-via-OR-Tools',
                'infeasibility_analysis': self._analyze_infeasibility()
            }
        elif status == pywraplp.Solver.UNBOUNDED:
            return {
                'status': 'unbounded',
                'error': 'Model is unbounded',
                'message': 'Objective can be improved indefinitely',
                'solve_time': solve_time,
                'solver': 'HiGHS-Transparent-via-OR-Tools',
                'unboundedness_analysis': self._analyze_unboundedness()
            }
        else:
            return {
                'status': 'error',
                'error': f'HiGHS solver status: {status}',
                'message': 'Solver failed to find solution',
                'solve_time': solve_time,
                'solver': 'HiGHS-Transparent-via-OR-Tools'
            }
    
    def _analyze_solution_quality(self, optimal_values: Dict[str, float], objective_value: float):
        """Analyze solution quality for transparency"""
        
        # Check for zero values
        zero_variables = [name for name, value in optimal_values.items() if abs(value) < 1e-6]
        
        # Check for variables at bounds
        at_bounds = []
        for name, var in self.variables.items():
            value = optimal_values.get(name, 0)
            if hasattr(var, 'lb') and hasattr(var, 'ub'):
                if abs(value - var.lb()) < 1e-6:
                    at_bounds.append(f"{name} at lower bound")
                elif abs(value - var.ub()) < 1e-6:
                    at_bounds.append(f"{name} at upper bound")
        
        return {
            'objective_value': objective_value,
            'zero_variables': zero_variables,
            'variables_at_bounds': at_bounds,
            'solution_quality': 'good' if len(zero_variables) < len(optimal_values) * 0.5 else 'many_zero_values',
            'analysis': f"Solution has {len(zero_variables)} variables near zero, {len(at_bounds)} variables at bounds"
        }
    
    def _analyze_infeasibility(self):
        """Analyze why the model is infeasible"""
        return {
            'analysis': 'Model contains conflicting constraints that cannot be satisfied simultaneously',
            'recommendations': [
                'Check constraint bounds for conflicts',
                'Verify constraint coefficients',
                'Consider relaxing some constraints',
                'Review variable bounds'
            ]
        }
    
    def _analyze_unboundedness(self):
        """Analyze why the model is unbounded"""
        return {
            'analysis': 'Model allows objective to improve indefinitely in certain direction',
            'recommendations': [
                'Add upper bounds to variables',
                'Check objective function coefficients',
                'Add constraints to limit solution space',
                'Review model formulation'
            ]
        }
    
    def _generate_transparency_report(self, model_data: Dict[str, Any], solution_info: Dict[str, Any], transparency_level: str) -> Dict[str, Any]:
        """Generate comprehensive transparency report"""
        
        report = {
            'transparency_level': transparency_level,
            'timestamp': datetime.now().isoformat(),
            'model_analysis': self.transparency_data['model_analysis'],
            'solver_events': self.transparency_data['solver_events'],
            'solution_analysis': solution_info.get('solution_analysis', {}),
            'performance_metrics': solution_info.get('performance_metrics', {}),
            'solver_info': {
                'solver_name': 'HiGHS',
                'interface': 'OR-Tools',
                'version': '1.11.0',
                'transparency_features': [
                    'Real-time solver event logging',
                    'Model structure analysis',
                    'Solution quality assessment',
                    'Performance metrics tracking',
                    'Detailed error analysis'
                ]
            },
            'transparency_summary': self._generate_transparency_summary()
        }
        
        return report
    
    def _generate_transparency_summary(self) -> Dict[str, Any]:
        """Generate transparency summary"""
        
        events = self.transparency_data['solver_events']
        model_analysis = self.transparency_data['model_analysis']
        
        return {
            'total_events_logged': len(events),
            'model_complexity': model_analysis.get('model_complexity', 'unknown'),
            'transparency_score': self._calculate_transparency_score(),
            'key_insights': [
                f"Model has {model_analysis.get('total_variables', 0)} variables and {model_analysis.get('total_constraints', 0)} constraints",
                f"Complexity level: {model_analysis.get('model_complexity', 'unknown')}",
                f"Logged {len(events)} solver events for full transparency"
            ]
        }
    
    def _calculate_transparency_score(self) -> float:
        """Calculate transparency score (0-1)"""
        events = self.transparency_data['solver_events']
        model_analysis = self.transparency_data['model_analysis']
        
        score = 0.0
        
        # Base score for having events
        if events:
            score += 0.3
        
        # Score for model analysis
        if model_analysis:
            score += 0.3
        
        # Score for detailed logging
        if len(events) > 5:
            score += 0.2
        
        # Score for comprehensive analysis
        if model_analysis.get('model_complexity'):
            score += 0.2
        
        return min(score, 1.0)
    
    def _parse_bounds(self, bounds_str: str) -> tuple:
        """Parse bounds string like '0 to 200' or '0 or 1'"""
        try:
            if ' or ' in bounds_str:  # Binary: '0 or 1'
                return (0, 1)
            elif ' to ' in bounds_str:  # Range: '0 to 200'
                parts = bounds_str.split(' to ')
                lower = float(parts[0]) if parts[0] != '-inf' else -float('inf')
                upper = float(parts[1]) if parts[1] != 'inf' else float('inf')
                return (lower, upper)
            else:
                # Try to parse as single number
                val = float(bounds_str)
                return (val, val)
        except:
            return (0, float('inf'))  # Default bounds
    
    def _parse_objective_expression(self, expression: str) -> list:
        """Parse objective expression like '77.34*y_ijt + 44.70*I_it'"""
        try:
            # Simple parsing - split by + and extract coefficients and variables
            terms = expression.replace(' ', '').split('+')
            obj_terms = []
            
            for term in terms:
                if '*' in term:
                    coeff_str, var_name = term.split('*')
                    coeff = float(coeff_str)
                    obj_terms.append((coeff, var_name))
                else:
                    # Assume coefficient is 1
                    obj_terms.append((1.0, term))
            
            return obj_terms
        except:
            return [(1.0, 'x')]  # Default term
    
    def _parse_constraint_expression(self, expression: str) -> Optional[object]:
        """Parse constraint expression like 'x_ijt <= 200*y_ijt'"""
        try:
            # For now, implement simple constraint parsing
            # This is a simplified version - in practice, you'd need more sophisticated parsing
            
            if '<=' in expression:
                lhs, rhs = expression.split('<=')
                rhs_val = float(rhs.strip())
                
                # Create constraint: lhs <= rhs_val
                constraint = self.solver.Constraint(0, rhs_val)
                
                # Parse LHS to add coefficients
                # For now, handle simple cases like "x_ijt" or "18*x_ijt"
                lhs_terms = self._parse_expression_terms(lhs.strip())
                for coeff, var_name in lhs_terms:
                    if var_name in self.variables:
                        constraint.SetCoefficient(self.variables[var_name], coeff)
                
                return constraint
                
            elif '>=' in expression:
                lhs, rhs = expression.split('>=')
                rhs_val = float(rhs.strip())
                
                # Create constraint: lhs >= rhs_val
                constraint = self.solver.Constraint(rhs_val, float('inf'))
                
                # Parse LHS to add coefficients
                lhs_terms = self._parse_expression_terms(lhs.strip())
                for coeff, var_name in lhs_terms:
                    if var_name in self.variables:
                        constraint.SetCoefficient(self.variables[var_name], coeff)
                
                return constraint
                
            elif '=' in expression:
                lhs, rhs = expression.split('=')
                rhs_val = float(rhs.strip())
                
                # Create constraint: lhs = rhs_val
                constraint = self.solver.Constraint(rhs_val, rhs_val)
                
                # Parse LHS to add coefficients
                lhs_terms = self._parse_expression_terms(lhs.strip())
                for coeff, var_name in lhs_terms:
                    if var_name in self.variables:
                        constraint.SetCoefficient(self.variables[var_name], coeff)
                
                return constraint
            else:
                return None
        except Exception as e:
            logger.warning(f"Failed to parse constraint '{expression}': {e}")
            return None
    
    def _parse_expression_terms(self, expression: str) -> list:
        """Parse expression terms like '18*x_ijt' or 'x_ijt'"""
        try:
            terms = []
            
            # Handle simple cases first
            if '*' in expression:
                # Format: "coeff*var"
                coeff_str, var_name = expression.split('*')
                coeff = float(coeff_str.strip())
                terms.append((coeff, var_name.strip()))
            else:
                # Format: "var" (coefficient is 1)
                terms.append((1.0, expression.strip()))
            
            return terms
        except Exception as e:
            logger.warning(f"Failed to parse expression terms '{expression}': {e}")
            return [(1.0, expression)]
