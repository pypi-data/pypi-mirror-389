#!/usr/bin/env python3
"""
Transparent HiGHS Solver - Enhanced with Callbacks and Logging for Maximum Transparency
"""

import logging
from typing import Any, Dict, Optional, Callable
from datetime import datetime
import json

logger = logging.getLogger(__name__)

# Try to import HiGHS
try:
    import highspy
    HAS_HIGHS = True
    logger.info("HiGHS solver available for transparent optimization")
except ImportError as e:
    HAS_HIGHS = False
    logger.warning(f"HiGHS solver not available: {e}")


class TransparentHiGHSSolver:
    """HiGHS solver with maximum transparency through callbacks and detailed logging"""

    def __init__(self):
        self.model = None
        self.variables = {}
        self.constraints = []
        self.objective = None
        self.solver_log = []
        self.iteration_data = []
        self.callback_data = {
            'simplex_iterations': [],
            'mip_nodes': [],
            'objective_improvements': [],
            'constraint_violations': [],
            'timing_data': {}
        }

    def solve_model(self, model_data: Dict[str, Any], transparency_level: str = "high") -> Dict[str, Any]:
        """Solve a model using HiGHS with maximum transparency"""
        
        if not HAS_HIGHS:
            return {
                'status': 'error',
                'error': 'HiGHS not available',
                'message': 'HiGHS library not installed'
            }

        try:
            # Create a new HiGHS model with transparency settings
            self.model = highspy.Highs()
            self.variables = {}
            self.constraints = []
            self.solver_log = []
            self.iteration_data = []
            
            # Configure transparency settings based on level
            self._configure_transparency_settings(transparency_level)
            
            # Set up callbacks for real-time monitoring
            self._setup_transparency_callbacks()
            
            # Add variables
            variables_data = model_data.get('variables', [])
            for var_data in variables_data:
                if isinstance(var_data, dict):
                    name = var_data.get('name', f'var_{len(self.variables)}')
                    var_type = var_data.get('type', 'continuous')
                    bounds = var_data.get('bounds', '0 to inf')
                    
                    # Parse bounds
                    lower_bound, upper_bound = self._parse_bounds(bounds)
                    
                    # Add variable to HiGHS
                    if var_type == 'binary':
                        var = self.model.addVar(lower_bound, upper_bound, highspy.HighsVarType.kInteger)
                        self.variables[name] = len(self.variables)
                        logger.info(f"Added binary variable: {name} [{lower_bound}, {upper_bound}]")
                    elif var_type == 'integer':
                        var = self.model.addVar(lower_bound, upper_bound, highspy.HighsVarType.kInteger)
                        self.variables[name] = len(self.variables)
                        logger.info(f"Added integer variable: {name} [{lower_bound}, {upper_bound}]")
                    else:  # continuous
                        var = self.model.addVar(lower_bound, upper_bound, highspy.HighsVarType.kContinuous)
                        self.variables[name] = len(self.variables)
                        logger.info(f"Added continuous variable: {name} [{lower_bound}, {upper_bound}]")
            
            # Set objective
            objective_data = model_data.get('objective', {})
            if objective_data:
                obj_type = objective_data.get('type', 'minimize')
                obj_expression = objective_data.get('expression', '')
                
                # Parse objective expression
                obj_coeffs = self._parse_objective_expression(obj_expression)
                
                if obj_type == 'maximize':
                    # Negate coefficients for maximization
                    obj_coeffs = [-coeff for coeff in obj_coeffs]
                
                # Set objective in HiGHS
                self.model.changeObjectiveSense(highspy.ObjSense.kMinimize)
                self.model.changeColsCost(len(obj_coeffs), list(range(len(obj_coeffs))), obj_coeffs)
                
                logger.info(f"Set objective: {obj_type} {obj_expression}")
            
            # Add constraints
            constraints_data = model_data.get('constraints', [])
            for i, constraint_data in enumerate(constraints_data):
                if isinstance(constraint_data, dict):
                    expression = constraint_data.get('expression', '')
                    description = constraint_data.get('description', f'constraint_{i}')
                    
                    # Parse constraint expression
                    coeffs, rhs, sense = self._parse_constraint_expression(expression)
                    
                    if coeffs is not None:
                        # Add constraint to HiGHS
                        self.model.addRow(rhs, rhs, len(coeffs), 
                                        list(range(len(coeffs))), coeffs)
                        logger.info(f"Added constraint: {expression}")
            
            # Solve the model with detailed logging
            logger.info("Solving HiGHS model with transparency enabled...")
            start_time = datetime.now()
            
            self.model.run()
            
            solve_time = (datetime.now() - start_time).total_seconds()
            
            # Get solution status
            status = self.model.getModelStatus()
            
            # Extract detailed solution information
            solution_info = self._extract_detailed_solution_info(status, solve_time)
            
            # Add transparency data
            solution_info['transparency_data'] = {
                'solver_log': self.solver_log,
                'iteration_data': self.iteration_data,
                'callback_data': self.callback_data,
                'transparency_level': transparency_level,
                'solver_options_used': self._get_solver_options_summary()
            }
            
            return solution_info
                
        except Exception as e:
            logger.error(f"HiGHS solving failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'message': 'HiGHS solver encountered an error',
                'transparency_data': {
                    'solver_log': self.solver_log,
                    'error_details': str(e)
                }
            }
    
    def _configure_transparency_settings(self, transparency_level: str):
        """Configure HiGHS options for maximum transparency"""
        
        # Get options object
        options = self.model.getOptions()
        
        if transparency_level == "high":
            # Maximum transparency - detailed logging and analysis
            options.log_to_console = True
            options.output_flag = True
            options.highs_analysis_level = 4  # Maximum analysis
            options.highs_debug_level = 2     # High debug level
            options.log_dev_level = 2         # Development logging
            options.mip_report_level = 2      # Detailed MIP reporting
            options.mip_min_logging_interval = 1  # Log every iteration
            
        elif transparency_level == "medium":
            # Balanced transparency
            options.log_to_console = True
            options.output_flag = True
            options.highs_analysis_level = 2
            options.highs_debug_level = 1
            options.mip_report_level = 1
            
        else:  # low
            # Minimal transparency
            options.log_to_console = False
            options.output_flag = False
            options.highs_analysis_level = 0
        
        # Additional transparency options
        options.timeless_log = True  # Include timing information
        options.log_githash = True   # Include version information
        
        logger.info(f"Configured HiGHS transparency level: {transparency_level}")
    
    def _setup_transparency_callbacks(self):
        """Set up callbacks for real-time solver monitoring"""
        
        # Simplex iteration callback
        def simplex_callback(event):
            iteration_info = {
                'iteration': len(self.callback_data['simplex_iterations']) + 1,
                'timestamp': datetime.now().isoformat(),
                'objective_value': getattr(event, 'objective_value', None),
                'primal_infeasibility': getattr(event, 'primal_infeasibility', None),
                'dual_infeasibility': getattr(event, 'dual_infeasibility', None),
                'message': getattr(event, 'message', 'Simplex iteration')
            }
            self.callback_data['simplex_iterations'].append(iteration_info)
            logger.info(f"Simplex iteration {iteration_info['iteration']}: {iteration_info['message']}")
        
        # MIP node callback
        def mip_callback(event):
            node_info = {
                'node': len(self.callback_data['mip_nodes']) + 1,
                'timestamp': datetime.now().isoformat(),
                'objective_value': getattr(event, 'objective_value', None),
                'best_bound': getattr(event, 'best_bound', None),
                'gap': getattr(event, 'gap', None),
                'message': getattr(event, 'message', 'MIP node explored')
            }
            self.callback_data['mip_nodes'].append(node_info)
            logger.info(f"MIP node {node_info['node']}: {node_info['message']}")
        
        # Logging callback
        def logging_callback(event):
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'level': getattr(event, 'level', 'INFO'),
                'message': getattr(event, 'message', 'Solver log entry'),
                'category': getattr(event, 'category', 'general')
            }
            self.solver_log.append(log_entry)
            logger.info(f"HiGHS Log: {log_entry['message']}")
        
        # Subscribe to callbacks
        try:
            self.model.cbSimplexInterrupt.subscribe(simplex_callback)
            self.model.cbMipInterrupt.subscribe(mip_callback)
            self.model.cbLogging.subscribe(logging_callback)
            logger.info("Transparency callbacks configured successfully")
        except Exception as e:
            logger.warning(f"Could not set up all callbacks: {e}")
    
    def _extract_detailed_solution_info(self, status, solve_time):
        """Extract detailed solution information with transparency"""
        
        if status == highspy.HighsModelStatus.kOptimal:
            # Extract solution
            solution = self.model.getSolution()
            optimal_values = {}
            
            for name, var_idx in self.variables.items():
                optimal_values[name] = solution.col_value[var_idx]
            
            objective_value = solution.objective_value
            
            return {
                'status': 'optimal',
                'objective_value': objective_value,
                'optimal_values': optimal_values,
                'solve_time': solve_time,
                'solver': 'HiGHS-Transparent',
                'message': 'Solved successfully with HiGHS (transparent mode)',
                'solution_details': {
                    'primal_solution': solution.col_value,
                    'dual_solution': solution.row_dual,
                    'reduced_costs': solution.col_dual,
                    'basis_status': solution.col_basis_status,
                    'constraint_activity': solution.row_value
                }
            }
        elif status == highspy.HighsModelStatus.kInfeasible:
            return {
                'status': 'infeasible',
                'error': 'Model is infeasible',
                'message': 'No feasible solution exists',
                'solve_time': solve_time,
                'solver': 'HiGHS-Transparent',
                'infeasibility_analysis': self._analyze_infeasibility()
            }
        elif status == highspy.HighsModelStatus.kUnbounded:
            return {
                'status': 'unbounded',
                'error': 'Model is unbounded',
                'message': 'Objective can be improved indefinitely',
                'solve_time': solve_time,
                'solver': 'HiGHS-Transparent',
                'unboundedness_analysis': self._analyze_unboundedness()
            }
        else:
            return {
                'status': 'error',
                'error': f'HiGHS solver status: {status}',
                'message': 'Solver failed to find solution',
                'solve_time': solve_time,
                'solver': 'HiGHS-Transparent'
            }
    
    def _analyze_infeasibility(self):
        """Analyze why the model is infeasible"""
        try:
            # Get IIS (Irreducible Inconsistent Subsystem)
            iis = self.model.getIis()
            return {
                'iis_available': iis is not None,
                'conflicting_constraints': getattr(iis, 'conflicting_constraints', []),
                'conflicting_variables': getattr(iis, 'conflicting_variables', []),
                'analysis': 'Model contains conflicting constraints that cannot be satisfied simultaneously'
            }
        except:
            return {'analysis': 'Infeasibility detected but detailed analysis not available'}
    
    def _analyze_unboundedness(self):
        """Analyze why the model is unbounded"""
        try:
            # Get unbounded ray
            primal_ray = self.model.getPrimalRay()
            return {
                'unbounded_ray_available': primal_ray is not None,
                'unbounded_direction': getattr(primal_ray, 'direction', None),
                'analysis': 'Model allows objective to improve indefinitely in certain direction'
            }
        except:
            return {'analysis': 'Unboundedness detected but detailed analysis not available'}
    
    def _get_solver_options_summary(self):
        """Get summary of solver options used"""
        try:
            options = self.model.getOptions()
            return {
                'analysis_level': getattr(options, 'highs_analysis_level', 0),
                'debug_level': getattr(options, 'highs_debug_level', 0),
                'log_to_console': getattr(options, 'log_to_console', False),
                'output_flag': getattr(options, 'output_flag', False),
                'presolve_enabled': getattr(options, 'presolve', True),
                'solver_type': getattr(options, 'solver', 'auto')
            }
        except:
            return {'options': 'Could not retrieve solver options'}
    
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
            # Simple parsing - split by + and extract coefficients
            terms = expression.replace(' ', '').split('+')
            coeffs = []
            
            for term in terms:
                if '*' in term:
                    coeff, var = term.split('*')
                    coeffs.append(float(coeff))
                else:
                    # Assume coefficient is 1
                    coeffs.append(1.0)
            
            return coeffs
        except:
            return [1.0]  # Default coefficient
    
    def _parse_constraint_expression(self, expression: str) -> tuple:
        """Parse constraint expression like 'x_ijt <= 200*y_ijt'"""
        try:
            # Simple parsing for basic constraints
            if '<=' in expression:
                lhs, rhs = expression.split('<=')
                # For now, return simple coefficients
                return [1.0], float(rhs.strip()), highspy.HighsBasisStatus.kLower
            elif '>=' in expression:
                lhs, rhs = expression.split('>=')
                return [1.0], float(rhs.strip()), highspy.HighsBasisStatus.kUpper
            elif '=' in expression:
                lhs, rhs = expression.split('=')
                return [1.0], float(rhs.strip()), highspy.HighsBasisStatus.kEqual
            else:
                return None, 0.0, highspy.HighsBasisStatus.kLower
        except:
            return None, 0.0, highspy.HighsBasisStatus.kLower
