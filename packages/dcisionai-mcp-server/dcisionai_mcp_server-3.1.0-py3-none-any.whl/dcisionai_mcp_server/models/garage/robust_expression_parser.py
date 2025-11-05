#!/usr/bin/env python3
"""
Robust Expression Parser using SymPy
Handles complex mathematical expressions that simple string parsing cannot
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application

logger = logging.getLogger(__name__)


class RobustExpressionParser:
    """Enhanced parser supporting complex mathematical expressions using SymPy"""
    
    def __init__(self):
        self.transformations = (standard_transformations + (implicit_multiplication_application,))
    
    def parse_constraint(
        self, 
        expression: str, 
        variables: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Parse constraints like:
        - "2*x + 3*y <= 10"
        - "sum(x[i] for i in range(5)) >= 100"
        - "x**2 + y**2 <= 50"
        
        Returns dict with:
        - lhs_coefficients: {var_name: coefficient}
        - sense: '<=', '>=', or '='
        - rhs: right-hand side value
        """
        try:
            # Clean the expression
            expression = expression.strip()
            
            # Detect constraint sense
            if '<=' in expression:
                sense = '<='
                lhs_str, rhs_str = expression.split('<=', 1)
            elif '>=' in expression:
                sense = '>='
                lhs_str, rhs_str = expression.split('>=', 1)
            elif '==' in expression:
                sense = '='
                lhs_str, rhs_str = expression.split('==', 1)
            elif '=' in expression and '!=' not in expression:
                sense = '='
                lhs_str, rhs_str = expression.split('=', 1)
            else:
                logger.error(f"No valid constraint sense found in: {expression}")
                return None
            
            lhs_str = lhs_str.strip()
            rhs_str = rhs_str.strip()
            
            # Create sympy symbols for all variables
            sympy_vars = {}
            for var_name in variables.keys():
                # Clean variable name for sympy
                clean_name = self._clean_variable_name(var_name)
                sympy_vars[clean_name] = sp.Symbol(clean_name)
            
            # Parse LHS using sympy
            try:
                lhs_expr = parse_expr(lhs_str, local_dict=sympy_vars, transformations=self.transformations)
            except Exception as e:
                logger.warning(f"SymPy parsing failed for LHS '{lhs_str}', trying simple parsing: {e}")
                # Fallback to simple parsing
                return self._simple_constraint_parse(expression, variables)
            
            # Parse RHS
            try:
                rhs_expr = parse_expr(rhs_str, local_dict=sympy_vars, transformations=self.transformations)
                rhs_value = float(rhs_expr.evalf())
            except:
                # RHS might just be a number
                try:
                    rhs_value = float(rhs_str)
                except:
                    logger.error(f"Could not parse RHS: {rhs_str}")
                    return None
            
            # Extract coefficients from LHS
            lhs_coefficients = {}
            
            # Expand the expression
            lhs_expanded = sp.expand(lhs_expr)
            
            # Get coefficients for each variable
            for var_name, sym in sympy_vars.items():
                coeff = lhs_expanded.coeff(sym)
                if coeff is not None and coeff != 0:
                    lhs_coefficients[var_name] = float(coeff)
            
            # Check for constant term
            constant_term = lhs_expanded.as_coeff_Add()[0]
            if constant_term != 0:
                # Move constant to RHS
                rhs_value -= float(constant_term)
            
            logger.info(f"✅ Parsed constraint: {lhs_coefficients} {sense} {rhs_value}")
            
            return {
                'lhs_coefficients': lhs_coefficients,
                'sense': sense,
                'rhs': rhs_value,
                'original_expression': expression
            }
            
        except Exception as e:
            logger.error(f"Failed to parse constraint '{expression}': {e}")
            # Try simple fallback
            return self._simple_constraint_parse(expression, variables)
    
    def parse_objective(
        self, 
        expression: str, 
        variables: Dict[str, Any],
        obj_type: str = 'minimize'
    ) -> Optional[Dict[str, Any]]:
        """
        Parse objectives like:
        - "minimize 5*x + 3*y"
        - "maximize sum(profit[i]*quantity[i])"
        - "minimize ||x - target||^2"
        
        Returns dict with:
        - coefficients: {var_name: coefficient}
        - type: 'minimize' or 'maximize'
        - is_quadratic: bool
        """
        try:
            # Clean the expression
            expression = expression.strip()
            
            # Remove objective type prefix if present
            expression = re.sub(r'^(minimize|maximize)\s+', '', expression, flags=re.IGNORECASE)
            
            # Create sympy symbols
            sympy_vars = {}
            for var_name in variables.keys():
                clean_name = self._clean_variable_name(var_name)
                sympy_vars[clean_name] = sp.Symbol(clean_name)
            
            # Parse expression
            try:
                obj_expr = parse_expr(expression, local_dict=sympy_vars, transformations=self.transformations)
            except Exception as e:
                logger.warning(f"SymPy parsing failed for objective '{expression}': {e}")
                return self._simple_objective_parse(expression, variables, obj_type)
            
            # Expand expression
            obj_expanded = sp.expand(obj_expr)
            
            # Extract linear coefficients
            linear_coefficients = {}
            for var_name, sym in sympy_vars.items():
                coeff = obj_expanded.coeff(sym)
                if coeff is not None and coeff != 0:
                    linear_coefficients[var_name] = float(coeff)
            
            # Check if quadratic
            is_quadratic = False
            quadratic_terms = {}
            
            # Look for x^2 terms
            for var_name, sym in sympy_vars.items():
                quad_coeff = obj_expanded.coeff(sym**2)
                if quad_coeff is not None and quad_coeff != 0:
                    is_quadratic = True
                    quadratic_terms[f"{var_name}^2"] = float(quad_coeff)
            
            # Look for cross terms (x*y)
            var_names = list(sympy_vars.keys())
            for i, var1 in enumerate(var_names):
                for var2 in var_names[i+1:]:
                    sym1 = sympy_vars[var1]
                    sym2 = sympy_vars[var2]
                    cross_coeff = obj_expanded.coeff(sym1 * sym2)
                    if cross_coeff is not None and cross_coeff != 0:
                        is_quadratic = True
                        quadratic_terms[f"{var1}*{var2}"] = float(cross_coeff)
            
            logger.info(f"✅ Parsed objective ({obj_type}): {linear_coefficients}")
            if is_quadratic:
                logger.info(f"   Quadratic terms: {quadratic_terms}")
            
            return {
                'coefficients': linear_coefficients,
                'type': obj_type,
                'is_quadratic': is_quadratic,
                'quadratic_terms': quadratic_terms if is_quadratic else {},
                'original_expression': expression
            }
            
        except Exception as e:
            logger.error(f"Failed to parse objective '{expression}': {e}")
            return self._simple_objective_parse(expression, variables, obj_type)
    
    def _clean_variable_name(self, var_name: str) -> str:
        """Clean variable name to be sympy-compatible"""
        # Replace special characters with underscores
        clean = re.sub(r'[^a-zA-Z0-9_]', '_', var_name)
        # Ensure it starts with a letter
        if clean[0].isdigit():
            clean = 'var_' + clean
        return clean
    
    def _simple_constraint_parse(
        self, 
        expression: str, 
        variables: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Fallback simple parser for when SymPy fails"""
        try:
            # Detect sense
            if '<=' in expression:
                sense = '<='
                lhs, rhs = expression.split('<=')
            elif '>=' in expression:
                sense = '>='
                lhs, rhs = expression.split('>=')
            elif '=' in expression:
                sense = '='
                lhs, rhs = expression.split('=')
            else:
                return None
            
            lhs = lhs.strip()
            rhs_value = float(rhs.strip())
            
            # Extract coefficients using regex
            lhs_coefficients = {}
            
            # Pattern: coefficient*variable or just variable
            for var_name in variables.keys():
                # Look for patterns like "5*var_name" or "var_name"
                pattern = rf'([\d\.]+)\s*\*\s*{re.escape(var_name)}'
                match = re.search(pattern, lhs)
                if match:
                    lhs_coefficients[var_name] = float(match.group(1))
                elif var_name in lhs:
                    lhs_coefficients[var_name] = 1.0
            
            return {
                'lhs_coefficients': lhs_coefficients,
                'sense': sense,
                'rhs': rhs_value,
                'original_expression': expression
            }
        except Exception as e:
            logger.error(f"Simple parsing also failed: {e}")
            return None
    
    def _simple_objective_parse(
        self, 
        expression: str, 
        variables: Dict[str, Any],
        obj_type: str
    ) -> Optional[Dict[str, Any]]:
        """Fallback simple parser for objectives"""
        try:
            coefficients = {}
            
            # Remove spaces
            expr = expression.replace(' ', '')
            
            # Split by + and - while preserving signs
            terms = re.split(r'([+-])', expr)
            
            # Reconstruct terms with signs
            current_sign = '+'
            for term in terms:
                if term in ['+', '-']:
                    current_sign = term
                elif term:
                    # Parse term
                    for var_name in variables.keys():
                        if var_name in term:
                            # Extract coefficient
                            coeff_str = term.replace(f'*{var_name}', '').replace(var_name, '')
                            if coeff_str:
                                coeff = float(coeff_str)
                            else:
                                coeff = 1.0
                            
                            if current_sign == '-':
                                coeff = -coeff
                            
                            coefficients[var_name] = coeff
                            break
            
            return {
                'coefficients': coefficients,
                'type': obj_type,
                'is_quadratic': False,
                'quadratic_terms': {},
                'original_expression': expression
            }
        except Exception as e:
            logger.error(f"Simple objective parsing also failed: {e}")
            return None
    
    def validate_expression_syntax(self, expression: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that an expression has valid syntax
        Returns (is_valid, error_message)
        """
        try:
            # Try to parse with sympy
            parse_expr(expression, transformations=self.transformations)
            return (True, None)
        except Exception as e:
            return (False, str(e))

