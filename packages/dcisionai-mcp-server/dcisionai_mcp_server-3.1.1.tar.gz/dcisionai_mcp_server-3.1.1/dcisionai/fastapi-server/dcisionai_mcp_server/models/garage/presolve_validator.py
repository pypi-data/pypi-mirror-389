#!/usr/bin/env python3
"""
Pre-Solve Validator
Validates and diagnoses models before solving to catch errors early
"""

import logging
import re
from typing import Any, Dict, List, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of model validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    checks_passed: Dict[str, bool]
    
    def __str__(self):
        status = "✅ VALID" if self.is_valid else "❌ INVALID"
        return f"""
Validation Result: {status}
Errors: {len(self.errors)}
Warnings: {len(self.warnings)}
Checks Passed: {sum(self.checks_passed.values())}/{len(self.checks_passed)}
"""


class PreSolveValidator:
    """Comprehensive pre-solve validation for optimization models"""
    
    def __init__(self):
        self.max_coefficient_magnitude = 1e10  # Numerical stability threshold
        self.min_coefficient_magnitude = 1e-10
    
    def validate_model(self, model_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate model before solving
        
        Checks:
        1. Variable coverage - all variables in constraints are defined
        2. Bound consistency - bounds are valid and consistent
        3. Feasibility pre-check - obvious infeasibility
        4. Numerical stability - no huge or tiny coefficients
        5. Objective validity - objective is well-defined
        """
        errors = []
        warnings = []
        suggestions = []
        checks = {}
        
        # Extract model components
        variables = model_data.get('variables', [])
        constraints = model_data.get('constraints', [])
        objective = model_data.get('objective', {})
        
        # Convert variables to dict for easier lookup
        var_dict = {}
        if isinstance(variables, list):
            for var in variables:
                if isinstance(var, dict):
                    var_dict[var.get('name')] = var
        elif isinstance(variables, dict):
            var_dict = variables
        
        # Check 1: Variable Coverage
        coverage_valid, coverage_errors, coverage_warnings = self._check_variable_coverage(
            var_dict, constraints, objective
        )
        checks['variable_coverage'] = coverage_valid
        errors.extend(coverage_errors)
        warnings.extend(coverage_warnings)
        
        # Check 2: Bound Consistency
        bounds_valid, bounds_errors, bounds_warnings = self._check_bounds(var_dict)
        checks['bound_consistency'] = bounds_valid
        errors.extend(bounds_errors)
        warnings.extend(bounds_warnings)
        
        # Check 3: Obvious Infeasibility
        feasibility_ok, feasibility_errors, feasibility_warnings = self._check_obvious_infeasibility(
            var_dict, constraints
        )
        checks['feasibility_pre_check'] = feasibility_ok
        errors.extend(feasibility_errors)
        warnings.extend(feasibility_warnings)
        
        # Check 4: Numerical Stability
        numerics_ok, numerics_errors, numerics_warnings = self._check_numerical_stability(
            var_dict, constraints, objective
        )
        checks['numerical_stability'] = numerics_ok
        errors.extend(numerics_errors)
        warnings.extend(numerics_warnings)
        
        # Check 5: Objective Validity
        obj_valid, obj_errors, obj_warnings = self._check_objective(var_dict, objective)
        checks['objective_validity'] = obj_valid
        errors.extend(obj_errors)
        warnings.extend(obj_warnings)
        
        # Generate suggestions based on issues found
        if errors or warnings:
            suggestions = self._generate_suggestions(errors, warnings, checks)
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            checks_passed=checks
        )
    
    def _check_variable_coverage(
        self, 
        variables: Dict[str, Any], 
        constraints: List[Any],
        objective: Dict[str, Any]
    ) -> tuple:
        """Check that all variables referenced in constraints/objective are defined"""
        errors = []
        warnings = []
        
        var_names = set(variables.keys())
        referenced_vars = set()
        
        # Check constraints
        for i, constraint in enumerate(constraints):
            if isinstance(constraint, dict):
                expression = constraint.get('expression', '')
                # Extract variable names from expression
                for var_name in var_names:
                    if var_name in expression:
                        referenced_vars.add(var_name)
                
                # Check for undefined variables
                # Simple heuristic: look for tokens that might be variables
                tokens = expression.replace('<=', ' ').replace('>=', ' ').replace('==', ' ').replace('=', ' ')
                tokens = tokens.replace('+', ' ').replace('-', ' ').replace('*', ' ').replace('/', ' ')
                tokens = [t.strip() for t in tokens.split() if t.strip()]
                
                for token in tokens:
                    # If it's not a number and not a defined variable, it might be undefined
                    try:
                        float(token)
                    except:
                        if token not in var_names and not token.isdigit():
                            if len(token) > 1:  # Ignore single character operators
                                errors.append(f"Constraint {i}: Undefined variable '{token}' in expression: {expression}")
        
        # Check objective
        if objective:
            obj_expr = objective.get('expression', '')
            for var_name in var_names:
                if var_name in obj_expr:
                    referenced_vars.add(var_name)
        
        # Warn about unused variables
        unused_vars = var_names - referenced_vars
        if unused_vars:
            warnings.append(f"Unused variables (not in any constraint or objective): {unused_vars}")
        
        is_valid = len(errors) == 0
        return (is_valid, errors, warnings)
    
    def _check_bounds(self, variables: Dict[str, Any]) -> tuple:
        """Check that variable bounds are valid and consistent"""
        errors = []
        warnings = []
        
        for var_name, var_data in variables.items():
            bounds_str = var_data.get('bounds', '0 to inf')
            
            try:
                # Parse bounds
                if ' or ' in bounds_str:  # Binary: '0 or 1'
                    lower, upper = 0, 1
                elif ' to ' in bounds_str:  # Range: '0 to 200'
                    parts = bounds_str.split(' to ')
                    lower = float(parts[0]) if parts[0] != '-inf' else float('-inf')
                    upper = float(parts[1]) if parts[1] != 'inf' else float('inf')
                else:
                    # Try to parse as single number
                    val = float(bounds_str)
                    lower, upper = val, val
                
                # Check consistency
                if lower > upper:
                    errors.append(f"Variable '{var_name}': Lower bound ({lower}) > upper bound ({upper})")
                
                # Warn about very tight bounds
                if lower == upper and lower != 0:
                    warnings.append(f"Variable '{var_name}': Fixed to constant value {lower}")
                
                # Warn about unbounded variables
                if lower == float('-inf') or upper == float('inf'):
                    warnings.append(f"Variable '{var_name}': Unbounded ({bounds_str})")
                
            except Exception as e:
                errors.append(f"Variable '{var_name}': Invalid bounds format '{bounds_str}': {e}")
        
        is_valid = len(errors) == 0
        return (is_valid, errors, warnings)
    
    def _check_obvious_infeasibility(
        self, 
        variables: Dict[str, Any], 
        constraints: List[Any]
    ) -> tuple:
        """Check for obviously infeasible constraints"""
        errors = []
        warnings = []
        
        for i, constraint in enumerate(constraints):
            if isinstance(constraint, dict):
                expression = constraint.get('expression', '')
                
                # Check for contradictory constraints
                # Example: "x <= 10" and "x >= 20"
                
                # Check for tautologies (always true)
                # Example: "x >= -inf"
                if 'inf' in expression.lower():
                    warnings.append(f"Constraint {i}: Contains infinity, might be tautological: {expression}")
                
                # Check for constraints that are always false
                # Example: "0 <= -1"
                if re.match(r'^\d+\s*[<>=]+\s*-\d+', expression):
                    errors.append(f"Constraint {i}: Obviously infeasible: {expression}")
        
        is_valid = len(errors) == 0
        return (is_valid, errors, warnings)
    
    def _check_numerical_stability(
        self, 
        variables: Dict[str, Any], 
        constraints: List[Any],
        objective: Dict[str, Any]
    ) -> tuple:
        """Check for numerical issues (very large or small coefficients)"""
        errors = []
        warnings = []
        
        import re
        
        def extract_coefficients(expression: str) -> List[float]:
            """Extract numerical coefficients from expression"""
            # Find all numbers in the expression
            numbers = re.findall(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', expression)
            return [float(n) for n in numbers if n]
        
        # Check constraints
        for i, constraint in enumerate(constraints):
            if isinstance(constraint, dict):
                expression = constraint.get('expression', '')
                coeffs = extract_coefficients(expression)
                
                for coeff in coeffs:
                    if abs(coeff) > self.max_coefficient_magnitude:
                        warnings.append(
                            f"Constraint {i}: Very large coefficient ({coeff:.2e}) may cause numerical issues"
                        )
                    elif 0 < abs(coeff) < self.min_coefficient_magnitude:
                        warnings.append(
                            f"Constraint {i}: Very small coefficient ({coeff:.2e}) may cause numerical issues"
                        )
        
        # Check objective
        if objective:
            obj_expr = objective.get('expression', '')
            coeffs = extract_coefficients(obj_expr)
            
            for coeff in coeffs:
                if abs(coeff) > self.max_coefficient_magnitude:
                    warnings.append(
                        f"Objective: Very large coefficient ({coeff:.2e}) may cause numerical issues"
                    )
                elif 0 < abs(coeff) < self.min_coefficient_magnitude:
                    warnings.append(
                        f"Objective: Very small coefficient ({coeff:.2e}) may cause numerical issues"
                    )
            
            # Check if all objective coefficients are 0
            if all(c == 0 for c in coeffs):
                errors.append("Objective: All coefficients are zero - no optimization possible")
        
        is_valid = len(errors) == 0
        return (is_valid, errors, warnings)
    
    def _check_objective(
        self, 
        variables: Dict[str, Any], 
        objective: Dict[str, Any]
    ) -> tuple:
        """Check that objective is well-defined"""
        errors = []
        warnings = []
        
        if not objective:
            errors.append("No objective function defined")
            return (False, errors, warnings)
        
        obj_type = objective.get('type', 'minimize')
        obj_expr = objective.get('expression', '')
        
        if not obj_expr:
            errors.append("Objective expression is empty")
            return (False, errors, warnings)
        
        if obj_type not in ['minimize', 'maximize']:
            errors.append(f"Invalid objective type: '{obj_type}' (must be 'minimize' or 'maximize')")
        
        # Check if objective references at least one variable
        var_names = set(variables.keys())
        references_var = any(var_name in obj_expr for var_name in var_names)
        
        if not references_var:
            warnings.append("Objective does not reference any decision variables")
        
        is_valid = len(errors) == 0
        return (is_valid, errors, warnings)
    
    def _generate_suggestions(
        self, 
        errors: List[str], 
        warnings: List[str],
        checks: Dict[str, bool]
    ) -> List[str]:
        """Generate actionable suggestions based on validation issues"""
        suggestions = []
        
        # Variable coverage issues
        if not checks.get('variable_coverage', True):
            suggestions.append("Fix undefined variables: Ensure all variables used in constraints are properly defined")
        
        # Bound issues
        if not checks.get('bound_consistency', True):
            suggestions.append("Fix variable bounds: Check that lower bounds <= upper bounds for all variables")
        
        # Infeasibility issues
        if not checks.get('feasibility_pre_check', True):
            suggestions.append("Review constraints: Some constraints appear contradictory or infeasible")
            suggestions.append("Consider using LLM-guided reformulation to resolve infeasibility")
        
        # Numerical issues
        if not checks.get('numerical_stability', True):
            suggestions.append("Scale your model: Consider normalizing coefficients to avoid numerical instability")
            suggestions.append("Use consistent units: Very large/small coefficients often indicate unit mismatches")
        
        # Objective issues
        if not checks.get('objective_validity', True):
            suggestions.append("Define a valid objective: Ensure objective expression is non-empty and references variables")
        
        return suggestions

