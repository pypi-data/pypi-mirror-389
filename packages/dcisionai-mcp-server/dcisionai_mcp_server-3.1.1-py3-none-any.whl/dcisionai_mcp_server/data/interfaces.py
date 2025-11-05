"""
Minimal interfaces for data integration

Adapted from model-builder interfaces
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import datetime


class OptimizationProblemType(Enum):
    """Types of optimization problems"""
    LINEAR_PROGRAMMING = "linear_programming"
    MIXED_INTEGER_PROGRAMMING = "mixed_integer_programming"
    QUADRATIC_PROGRAMMING = "quadratic_programming"
    NONLINEAR_PROGRAMMING = "nonlinear_programming"
    SCHEDULING = "scheduling"
    ROUTING = "routing"
    FACILITY_LOCATION = "facility_location"
    PORTFOLIO_OPTIMIZATION = "portfolio_optimization"
    KNAPSACK = "knapsack"
    ASSIGNMENT = "assignment"
    GENERAL = "general"


class VariableType(Enum):
    """Types of decision variables"""
    CONTINUOUS = "continuous"
    INTEGER = "integer"
    BINARY = "binary"


class ConstraintType(Enum):
    """Types of constraints"""
    EQUALITY = "equality"
    LESS_THAN_OR_EQUAL = "less_than_or_equal"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"


@dataclass
class DecisionVariable:
    """Decision variable definition"""
    name: str
    variable_type: VariableType
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None
    description: Optional[str] = None


@dataclass
class Constraint:
    """Constraint definition"""
    name: str
    expression: str
    constraint_type: ConstraintType
    right_hand_side: float
    description: Optional[str] = None


@dataclass
class ObjectiveFunction:
    """Objective function definition"""
    expression: str
    sense: str  # "minimize" or "maximize"
    description: Optional[str] = None


@dataclass
class ParsedProblem:
    """Parsed optimization problem"""
    problem_id: str
    problem_type: OptimizationProblemType
    variables: List[DecisionVariable]
    constraints: List[Constraint]
    objective: ObjectiveFunction
    data_requirements: List[str] = field(default_factory=list)
    confidence_score: float = 1.0
    original_prompt: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None


# Stub for Dataset (simplified from model-builder)
@dataclass
class Dataset:
    """Simplified dataset representation"""
    id: str
    name: str
    data: Any  # Usually pd.DataFrame
    target_column: Optional[str] = None
    problem_type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# Stub for DatasetRegistry
class DatasetRegistry:
    """Simplified dataset registry"""
    
    def __init__(self):
        self.datasets = {}
    
    def get_dataset(self, dataset_id: str) -> Optional[Dataset]:
        """Get dataset by ID"""
        return self.datasets.get(dataset_id)
    
    def store_dataset(self, dataset: Dataset):
        """Store dataset"""
        self.datasets[dataset.id] = dataset


# Stub for ProblemType
class ProblemType(Enum):
    """Problem type enum"""
    OPTIMIZATION = "optimization"
    CLASSIFICATION = "classification"
    REGRESSION = "regression"

