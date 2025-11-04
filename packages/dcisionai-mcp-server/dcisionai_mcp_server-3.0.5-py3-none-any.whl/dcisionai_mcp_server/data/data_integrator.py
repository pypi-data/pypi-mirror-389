"""
Data integration utilities for optimization models with DcisionAI datasets

Adapted from model-builder for DcisionAI platform integration
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime

from .interfaces import (
    ParsedProblem, DecisionVariable, Constraint, ObjectiveFunction,
    VariableType, ConstraintType, OptimizationProblemType,
    DatasetRegistry, Dataset, ProblemType
)
from .exceptions import DataIntegrationError, DataValidationError


class OptimizationDataIntegrator:
    """Integrates optimization models with existing DcisionAI datasets"""
    
    def __init__(self, dataset_registry: DatasetRegistry):
        """Initialize with dataset registry"""
        self.dataset_registry = dataset_registry
        self.logger = logging.getLogger(__name__)
        
        # Initialize parameter extraction strategies
        self._extraction_strategies = self._initialize_extraction_strategies()
    
    def _initialize_extraction_strategies(self) -> Dict[str, Any]:
        """Initialize strategies for extracting optimization parameters from datasets"""
        return {
            "demand_forecasting": {
                "target_columns": ["demand", "sales", "quantity", "volume"],
                "parameter_type": "constraint_rhs",
                "aggregation": "mean"
            },
            "cost_estimation": {
                "target_columns": ["cost", "price", "expense", "budget"],
                "parameter_type": "objective_coefficient",
                "aggregation": "mean"
            },
            "capacity_planning": {
                "target_columns": ["capacity", "limit", "maximum", "available"],
                "parameter_type": "constraint_rhs",
                "aggregation": "max"
            },
            "resource_allocation": {
                "target_columns": ["resource", "allocation", "assignment", "utilization"],
                "parameter_type": "constraint_coefficient",
                "aggregation": "sum"
            },
            "time_series": {
                "target_columns": ["time", "date", "period", "timestamp"],
                "parameter_type": "temporal_parameter",
                "aggregation": "latest"
            }
        }
    
    async def integrate_dataset_with_problem(self, problem: ParsedProblem, 
                                           dataset_id: str,
                                           integration_config: Optional[Dict[str, Any]] = None) -> ParsedProblem:
        """Integrate dataset with optimization problem"""
        
        try:
            self.logger.info(f"Integrating dataset {dataset_id} with problem {problem.problem_id}")
            
            # Get dataset from registry
            dataset = self.dataset_registry.get_dataset(dataset_id)
            if not dataset:
                raise DataIntegrationError(f"Dataset {dataset_id} not found in registry")
            
            # Validate dataset for optimization use
            validation_result = await self._validate_dataset_for_optimization(dataset, problem)
            if not validation_result["is_valid"]:
                raise DataIntegrationError(f"Dataset validation failed: {'; '.join(validation_result['errors'])}")
            
            # Extract parameters from dataset
            extracted_parameters = await self._extract_optimization_parameters(dataset, problem, integration_config)
            
            # Apply parameters to problem components
            enhanced_problem = await self._apply_parameters_to_problem(
                problem, extracted_parameters, dataset, integration_config
            )
            
            # Add data lineage information
            enhanced_problem.data_requirements.append(f"dataset:{dataset_id}")
            enhanced_problem.metadata = enhanced_problem.metadata or {}
            enhanced_problem.metadata.update({
                "integrated_dataset": dataset_id,
                "integration_timestamp": datetime.now().isoformat(),
                "extracted_parameters": list(extracted_parameters.keys()),
                "data_validation": validation_result
            })
            
            self.logger.info(f"Successfully integrated dataset {dataset_id} with problem {problem.problem_id}")
            return enhanced_problem
            
        except Exception as e:
            self.logger.error(f"Dataset integration failed: {str(e)}")
            if isinstance(e, DataIntegrationError):
                raise
            else:
                raise DataIntegrationError(f"Unexpected error during data integration: {str(e)}")
    
    async def _validate_dataset_for_optimization(self, dataset: Dataset, 
                                               problem: ParsedProblem) -> Dict[str, Any]:
        """Validate dataset suitability for optimization parameter extraction"""
        
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "recommendations": []
        }
        
        try:
            # Check dataset size
            if len(dataset.data) == 0:
                validation_result["errors"].append("Dataset is empty")
                validation_result["is_valid"] = False
            
            if len(dataset.data) < 10:
                validation_result["warnings"].append("Dataset has very few rows - parameter estimates may be unreliable")
            
            # Check for numeric columns
            numeric_columns = dataset.data.select_dtypes(include=[np.number]).columns.tolist()
            if not numeric_columns:
                validation_result["errors"].append("Dataset has no numeric columns for parameter extraction")
                validation_result["is_valid"] = False
            
            # Check for missing values
            missing_data = dataset.data.isnull().sum()
            high_missing_cols = missing_data[missing_data > len(dataset.data) * 0.5].index.tolist()
            if high_missing_cols:
                validation_result["warnings"].append(f"Columns with >50% missing data: {high_missing_cols}")
            
            # Check column relevance to optimization problem
            relevant_columns = await self._identify_relevant_columns(dataset, problem)
            if not relevant_columns:
                validation_result["warnings"].append("No obviously relevant columns found for optimization parameters")
            else:
                validation_result["recommendations"].append(f"Potentially relevant columns: {relevant_columns}")
            
            # Check data quality
            quality_issues = await self._check_data_quality(dataset)
            validation_result["warnings"].extend(quality_issues)
            
        except Exception as e:
            validation_result["errors"].append(f"Validation error: {str(e)}")
            validation_result["is_valid"] = False
        
        return validation_result
    
    async def _identify_relevant_columns(self, dataset: Dataset, 
                                       problem: Optional[ParsedProblem]) -> List[str]:
        """Identify columns relevant to optimization problem"""
        
        relevant_columns = []
        
        try:
            # Get problem keywords from description and variable names
            problem_keywords = set()
            
            # If no problem provided, return all numeric columns
            if problem is None:
                numeric_cols = dataset.data.select_dtypes(include=[np.number]).columns.tolist()
                return numeric_cols
            
            # Extract keywords from problem prompt
            if problem.original_prompt:
                problem_keywords.update(problem.original_prompt.lower().split())
            
            # Extract keywords from variable names and descriptions
            for var in problem.variables:
                problem_keywords.update(var.name.lower().split('_'))
                if var.description:
                    problem_keywords.update(var.description.lower().split())
            
            # Extract keywords from constraint descriptions
            for constraint in problem.constraints:
                if constraint.description:
                    problem_keywords.update(constraint.description.lower().split())
            
            # Match column names with problem keywords
            for column in dataset.data.columns:
                column_lower = column.lower()
                for keyword in problem_keywords:
                    if len(keyword) > 3 and keyword in column_lower:
                        relevant_columns.append(column)
                        break
            
            # Also check for common optimization parameter patterns
            optimization_patterns = [
                'cost', 'price', 'demand', 'capacity', 'limit', 'budget',
                'resource', 'allocation', 'quantity', 'volume', 'rate',
                'time', 'duration', 'distance', 'weight', 'profit'
            ]
            
            for column in dataset.data.columns:
                column_lower = column.lower()
                for pattern in optimization_patterns:
                    if pattern in column_lower and column not in relevant_columns:
                        relevant_columns.append(column)
                        break
            
        except Exception as e:
            self.logger.warning(f"Column relevance identification failed: {str(e)}")
        
        return list(set(relevant_columns))  # Remove duplicates
    
    async def _check_data_quality(self, dataset: Dataset) -> List[str]:
        """Check data quality issues"""
        
        quality_issues = []
        
        try:
            # Check for outliers in numeric columns
            numeric_columns = dataset.data.select_dtypes(include=[np.number]).columns
            
            for column in numeric_columns:
                Q1 = dataset.data[column].quantile(0.25)
                Q3 = dataset.data[column].quantile(0.75)
                IQR = Q3 - Q1
                
                outliers = dataset.data[
                    (dataset.data[column] < Q1 - 1.5 * IQR) | 
                    (dataset.data[column] > Q3 + 1.5 * IQR)
                ]
                
                if len(outliers) > len(dataset.data) * 0.1:
                    quality_issues.append(f"Column '{column}' has many outliers ({len(outliers)} rows)")
            
            # Check for constant columns
            constant_columns = []
            for column in dataset.data.columns:
                if dataset.data[column].nunique() <= 1:
                    constant_columns.append(column)
            
            if constant_columns:
                quality_issues.append(f"Constant columns found: {constant_columns}")
            
            # Check for duplicate rows
            duplicate_count = dataset.data.duplicated().sum()
            if duplicate_count > 0:
                quality_issues.append(f"Dataset contains {duplicate_count} duplicate rows")
            
        except Exception as e:
            quality_issues.append(f"Data quality check error: {str(e)}")
        
        return quality_issues
    
    async def _extract_optimization_parameters(self, dataset: Dataset, 
                                             problem: ParsedProblem,
                                             config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract optimization parameters from dataset"""
        
        extracted_parameters = {}
        
        try:
            # Use configuration if provided, otherwise auto-detect
            if config and "parameter_mapping" in config:
                # Use explicit parameter mapping
                parameter_mapping = config["parameter_mapping"]
                for param_name, column_info in parameter_mapping.items():
                    if isinstance(column_info, str):
                        column_name = column_info
                        aggregation = "mean"
                    else:
                        column_name = column_info.get("column")
                        aggregation = column_info.get("aggregation", "mean")
                    
                    if column_name in dataset.data.columns:
                        param_value = await self._extract_parameter_value(
                            dataset.data[column_name], aggregation
                        )
                        extracted_parameters[param_name] = param_value
            
            else:
                # Auto-detect parameters based on problem type and column patterns
                extracted_parameters = await self._auto_extract_parameters(dataset, problem)
            
            # Extract time-series parameters if applicable
            time_params = await self._extract_temporal_parameters(dataset, problem)
            extracted_parameters.update(time_params)
            
            # Extract categorical parameters
            categorical_params = await self._extract_categorical_parameters(dataset, problem)
            extracted_parameters.update(categorical_params)
            
        except Exception as e:
            self.logger.error(f"Parameter extraction failed: {str(e)}")
            raise DataIntegrationError(f"Failed to extract parameters: {str(e)}")
        
        return extracted_parameters
    
    async def _auto_extract_parameters(self, dataset: Dataset, 
                                     problem: ParsedProblem) -> Dict[str, Any]:
        """Auto-extract parameters based on problem characteristics"""
        
        parameters = {}
        
        try:
            # Identify parameter extraction strategies based on problem type
            strategies = []
            
            if problem.problem_type in [OptimizationProblemType.LINEAR_PROGRAMMING, 
                                      OptimizationProblemType.MIXED_INTEGER_PROGRAMMING]:
                strategies.extend(["demand_forecasting", "cost_estimation", "capacity_planning"])
            
            if problem.problem_type == OptimizationProblemType.SCHEDULING:
                strategies.extend(["time_series", "resource_allocation"])
            
            if problem.problem_type in [OptimizationProblemType.ROUTING, 
                                      OptimizationProblemType.FACILITY_LOCATION]:
                strategies.extend(["cost_estimation", "capacity_planning"])
            
            # Apply extraction strategies
            for strategy_name in strategies:
                if strategy_name in self._extraction_strategies:
                    strategy = self._extraction_strategies[strategy_name]
                    strategy_params = await self._apply_extraction_strategy(dataset, strategy, problem)
                    parameters.update(strategy_params)
            
        except Exception as e:
            self.logger.warning(f"Auto parameter extraction failed: {str(e)}")
        
        return parameters
    
    async def _apply_extraction_strategy(self, dataset: Dataset, 
                                       strategy: Dict[str, Any],
                                       problem: ParsedProblem) -> Dict[str, Any]:
        """Apply specific extraction strategy"""
        
        parameters = {}
        
        try:
            target_columns = strategy["target_columns"]
            parameter_type = strategy["parameter_type"]
            aggregation = strategy["aggregation"]
            
            # Find matching columns
            matching_columns = []
            for column in dataset.data.columns:
                column_lower = column.lower()
                for target in target_columns:
                    if target in column_lower:
                        matching_columns.append(column)
                        break
            
            # Extract parameters from matching columns
            for column in matching_columns:
                if dataset.data[column].dtype in ['int64', 'float64']:
                    param_value = await self._extract_parameter_value(dataset.data[column], aggregation)
                    param_name = f"{parameter_type}_{column.lower().replace(' ', '_')}"
                    parameters[param_name] = param_value
            
        except Exception as e:
            self.logger.warning(f"Strategy application failed: {str(e)}")
        
        return parameters
    
    async def _extract_parameter_value(self, series: pd.Series, aggregation: str) -> float:
        """Extract parameter value using specified aggregation"""
        
        try:
            # Remove missing values
            clean_series = series.dropna()
            
            if len(clean_series) == 0:
                return 0.0
            
            if aggregation == "mean":
                return float(clean_series.mean())
            elif aggregation == "median":
                return float(clean_series.median())
            elif aggregation == "max":
                return float(clean_series.max())
            elif aggregation == "min":
                return float(clean_series.min())
            elif aggregation == "sum":
                return float(clean_series.sum())
            elif aggregation == "std":
                return float(clean_series.std())
            elif aggregation == "latest":
                return float(clean_series.iloc[-1])
            else:
                return float(clean_series.mean())  # Default to mean
                
        except Exception as e:
            self.logger.warning(f"Parameter value extraction failed: {str(e)}")
            return 0.0
    
    async def _extract_temporal_parameters(self, dataset: Dataset, 
                                         problem: ParsedProblem) -> Dict[str, Any]:
        """Extract time-based parameters from dataset"""
        
        temporal_params = {}
        
        try:
            # Identify date/time columns
            date_columns = []
            for column in dataset.data.columns:
                if dataset.data[column].dtype == 'datetime64[ns]' or 'date' in column.lower() or 'time' in column.lower():
                    date_columns.append(column)
            
            # Extract temporal parameters
            for column in date_columns:
                try:
                    if dataset.data[column].dtype != 'datetime64[ns]':
                        # Try to convert to datetime
                        dataset.data[column] = pd.to_datetime(dataset.data[column], errors='coerce')
                    
                    # Extract time-based features
                    if not dataset.data[column].isna().all():
                        temporal_params[f"time_span_days_{column}"] = (
                            dataset.data[column].max() - dataset.data[column].min()
                        ).days
                        
                        temporal_params[f"data_points_{column}"] = len(dataset.data[column].dropna())
                        
                except Exception as e:
                    self.logger.warning(f"Temporal parameter extraction failed for {column}: {str(e)}")
            
        except Exception as e:
            self.logger.warning(f"Temporal parameter extraction failed: {str(e)}")
        
        return temporal_params
    
    async def _extract_categorical_parameters(self, dataset: Dataset, 
                                            problem: ParsedProblem) -> Dict[str, Any]:
        """Extract parameters from categorical columns"""
        
        categorical_params = {}
        
        try:
            # Identify categorical columns
            categorical_columns = dataset.data.select_dtypes(include=['object', 'category']).columns
            
            for column in categorical_columns:
                try:
                    # Count unique categories
                    unique_count = dataset.data[column].nunique()
                    categorical_params[f"categories_count_{column}"] = unique_count
                    
                    # Get most frequent category
                    if unique_count > 0:
                        most_frequent = dataset.data[column].mode().iloc[0] if len(dataset.data[column].mode()) > 0 else None
                        if most_frequent:
                            categorical_params[f"most_frequent_{column}"] = str(most_frequent)
                    
                    # Calculate category distribution entropy (measure of diversity)
                    value_counts = dataset.data[column].value_counts(normalize=True)
                    entropy = -sum(p * np.log2(p) for p in value_counts if p > 0)
                    categorical_params[f"entropy_{column}"] = entropy
                    
                except Exception as e:
                    self.logger.warning(f"Categorical parameter extraction failed for {column}: {str(e)}")
        
        except Exception as e:
            self.logger.warning(f"Categorical parameter extraction failed: {str(e)}")
        
        return categorical_params
    
    async def _apply_parameters_to_problem(self, problem: ParsedProblem, 
                                         parameters: Dict[str, Any],
                                         dataset: Dataset,
                                         config: Optional[Dict[str, Any]]) -> ParsedProblem:
        """Apply extracted parameters to problem components"""
        
        try:
            # Update constraints with parameters
            updated_constraints = []
            for constraint in problem.constraints:
                updated_constraint = await self._update_constraint_with_parameters(
                    constraint, parameters, config
                )
                updated_constraints.append(updated_constraint)
            
            # Update objective with parameters
            updated_objective = await self._update_objective_with_parameters(
                problem.objective, parameters, config
            )
            
            # Update variables if needed
            updated_variables = await self._update_variables_with_parameters(
                problem.variables, parameters, config
            )
            
            # Create enhanced problem
            enhanced_problem = ParsedProblem(
                problem_id=problem.problem_id,
                problem_type=problem.problem_type,
                variables=updated_variables,
                constraints=updated_constraints,
                objective=updated_objective,
                data_requirements=problem.data_requirements.copy(),
                confidence_score=problem.confidence_score,
                original_prompt=problem.original_prompt,
                created_at=problem.created_at
            )
            
            return enhanced_problem
            
        except Exception as e:
            self.logger.error(f"Parameter application failed: {str(e)}")
            raise DataIntegrationError(f"Failed to apply parameters: {str(e)}")
    
    async def _update_constraint_with_parameters(self, constraint: Constraint, 
                                               parameters: Dict[str, Any],
                                               config: Optional[Dict[str, Any]]) -> Constraint:
        """Update constraint with extracted parameters"""
        
        try:
            updated_expression = constraint.expression
            updated_rhs = constraint.right_hand_side
            
            # Replace parameter placeholders in expression
            for param_name, param_value in parameters.items():
                placeholder = f"{{{param_name}}}"
                if placeholder in updated_expression:
                    updated_expression = updated_expression.replace(placeholder, str(param_value))
            
            # Update RHS with relevant parameters
            constraint_name_lower = constraint.name.lower()
            for param_name, param_value in parameters.items():
                # Match constraint types with parameter types
                if ("capacity" in constraint_name_lower and "capacity" in param_name) or \
                   ("demand" in constraint_name_lower and "demand" in param_name) or \
                   ("budget" in constraint_name_lower and "cost" in param_name):
                    updated_rhs = float(param_value)
                    break
            
            return Constraint(
                name=constraint.name,
                expression=updated_expression,
                constraint_type=constraint.constraint_type,
                right_hand_side=updated_rhs,
                description=constraint.description + " (data-enhanced)"
            )
            
        except Exception as e:
            self.logger.warning(f"Constraint parameter update failed: {str(e)}")
            return constraint
    
    async def _update_objective_with_parameters(self, objective: ObjectiveFunction,
                                              parameters: Dict[str, Any],
                                              config: Optional[Dict[str, Any]]) -> ObjectiveFunction:
        """Update objective function with extracted parameters"""
        
        try:
            updated_expression = objective.expression
            
            # Replace parameter placeholders
            for param_name, param_value in parameters.items():
                placeholder = f"{{{param_name}}}"
                if placeholder in updated_expression:
                    updated_expression = updated_expression.replace(placeholder, str(param_value))
            
            # Update coefficients with cost/profit parameters
            for param_name, param_value in parameters.items():
                if "cost" in param_name or "profit" in param_name:
                    # This is a simplified approach - in practice would need expression parsing
                    if param_name.replace("objective_coefficient_", "") in updated_expression:
                        # Would implement proper coefficient replacement here
                        pass
            
            return ObjectiveFunction(
                expression=updated_expression,
                sense=objective.sense,
                description=objective.description + " (data-enhanced)"
            )
            
        except Exception as e:
            self.logger.warning(f"Objective parameter update failed: {str(e)}")
            return objective
    
    async def _update_variables_with_parameters(self, variables: List[DecisionVariable],
                                              parameters: Dict[str, Any],
                                              config: Optional[Dict[str, Any]]) -> List[DecisionVariable]:
        """Update variables with extracted parameters"""
        
        try:
            updated_variables = []
            
            for var in variables:
                updated_var = DecisionVariable(
                    name=var.name,
                    variable_type=var.variable_type,
                    lower_bound=var.lower_bound,
                    upper_bound=var.upper_bound,
                    description=var.description
                )
                
                # Update bounds with capacity parameters
                var_name_lower = var.name.lower()
                for param_name, param_value in parameters.items():
                    if "capacity" in param_name and var_name_lower in param_name:
                        if var.upper_bound is None:
                            updated_var.upper_bound = float(param_value)
                        break
                
                updated_variables.append(updated_var)
            
            return updated_variables
            
        except Exception as e:
            self.logger.warning(f"Variable parameter update failed: {str(e)}")
            return variables
    
    async def validate_data_for_optimization(self, dataset_id: str, 
                                           requirements: List[str]) -> Dict[str, Any]:
        """Validate dataset meets optimization model requirements"""
        
        try:
            dataset = self.dataset_registry.get_dataset(dataset_id)
            if not dataset:
                return {
                    "is_valid": False,
                    "errors": [f"Dataset {dataset_id} not found"],
                    "warnings": [],
                    "recommendations": []
                }
            
            validation_result = {
                "is_valid": True,
                "errors": [],
                "warnings": [],
                "recommendations": [],
                "available_parameters": []
            }
            
            # Check if dataset meets each requirement
            for requirement in requirements:
                requirement_met = await self._check_requirement(dataset, requirement)
                if not requirement_met["is_met"]:
                    validation_result["errors"].append(
                        f"Requirement '{requirement}' not met: {requirement_met['reason']}"
                    )
                    validation_result["is_valid"] = False
                else:
                    validation_result["available_parameters"].extend(requirement_met.get("parameters", []))
            
            # Add general recommendations
            if validation_result["is_valid"]:
                validation_result["recommendations"].append("Dataset is suitable for optimization parameter extraction")
            else:
                validation_result["recommendations"].append("Consider data preprocessing or alternative datasets")
            
            return validation_result
            
        except Exception as e:
            return {
                "is_valid": False,
                "errors": [f"Validation error: {str(e)}"],
                "warnings": [],
                "recommendations": []
            }
    
    async def _check_requirement(self, dataset: Dataset, requirement: str) -> Dict[str, Any]:
        """Check if dataset meets specific requirement"""
        
        try:
            requirement_lower = requirement.lower()
            
            # Check for numeric data requirement
            if "numeric" in requirement_lower:
                numeric_columns = dataset.data.select_dtypes(include=[np.number]).columns.tolist()
                return {
                    "is_met": len(numeric_columns) > 0,
                    "reason": f"Found {len(numeric_columns)} numeric columns" if numeric_columns else "No numeric columns found",
                    "parameters": numeric_columns
                }
            
            # Check for specific column patterns
            for pattern in ["cost", "demand", "capacity", "time", "resource"]:
                if pattern in requirement_lower:
                    matching_columns = [col for col in dataset.data.columns if pattern in col.lower()]
                    return {
                        "is_met": len(matching_columns) > 0,
                        "reason": f"Found columns matching '{pattern}': {matching_columns}" if matching_columns else f"No columns matching '{pattern}' found",
                        "parameters": matching_columns
                    }
            
            # Default: requirement is met
            return {
                "is_met": True,
                "reason": "General requirement satisfied",
                "parameters": []
            }
            
        except Exception as e:
            return {
                "is_met": False,
                "reason": f"Requirement check error: {str(e)}",
                "parameters": []
            }
    
    async def preprocess_data_for_optimization(self, dataset_id: str,
                                             preprocessing_config: Optional[Dict[str, Any]] = None) -> str:
        """Preprocess dataset for optimization use and return new dataset ID"""
        
        try:
            # Get original dataset
            original_dataset = self.dataset_registry.get_dataset(dataset_id)
            if not original_dataset:
                raise DataIntegrationError(f"Dataset {dataset_id} not found")
            
            # Create preprocessing configuration
            config = preprocessing_config or {
                "handle_missing": "mean_imputation",
                "remove_outliers": True,
                "normalize_numeric": False,  # Usually not needed for optimization parameters
                "encode_categorical": False  # Keep categorical for parameter extraction
            }
            
            # Apply preprocessing
            processed_data = original_dataset.data.copy()
            
            # Handle missing values
            if config.get("handle_missing") == "mean_imputation":
                numeric_columns = processed_data.select_dtypes(include=[np.number]).columns
                processed_data[numeric_columns] = processed_data[numeric_columns].fillna(
                    processed_data[numeric_columns].mean()
                )
            elif config.get("handle_missing") == "drop":
                processed_data = processed_data.dropna()
            
            # Remove outliers if requested
            if config.get("remove_outliers"):
                processed_data = await self._remove_outliers(processed_data)
            
            # Create new dataset
            processed_dataset = Dataset(
                id=f"{dataset_id}_optimized",
                name=f"{original_dataset.name} (Optimized)",
                data=processed_data,
                target_column=original_dataset.target_column,
                problem_type=original_dataset.problem_type,
                metadata={
                    **original_dataset.metadata,
                    "preprocessing_applied": config,
                    "original_dataset_id": dataset_id,
                    "optimization_ready": True
                }
            )
            
            # Store processed dataset
            self.dataset_registry.store_dataset(processed_dataset)
            
            return processed_dataset.id
            
        except Exception as e:
            self.logger.error(f"Data preprocessing failed: {str(e)}")
            raise DataIntegrationError(f"Failed to preprocess data: {str(e)}")
    
    async def _remove_outliers(self, data: pd.DataFrame) -> pd.DataFrame:
        """Remove outliers from numeric columns using IQR method"""
        
        try:
            cleaned_data = data.copy()
            numeric_columns = data.select_dtypes(include=[np.number]).columns
            
            for column in numeric_columns:
                Q1 = data[column].quantile(0.25)
                Q3 = data[column].quantile(0.75)
                IQR = Q3 - Q1
                
                # Define outlier bounds
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                # Remove outliers
                cleaned_data = cleaned_data[
                    (cleaned_data[column] >= lower_bound) & 
                    (cleaned_data[column] <= upper_bound)
                ]
            
            return cleaned_data
            
        except Exception as e:
            self.logger.warning(f"Outlier removal failed: {str(e)}")
            return data