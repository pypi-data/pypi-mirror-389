"""
Data Integration & Simulation Package

Provides intelligent data generation, external data connectors, and quality validation
for optimization problems.

Components:
- data_simulator: Domain-specific synthetic data generation (6 domains)
- external_connectors: Real-world data from Polygon.io & Alpha Vantage
- llm_adapter: LLM-based parameter extraction
- interfaces: Data structures and problem definitions
- exceptions: Data integration error types
"""

from .external_connectors import (
    ExternalDataManager,
    ExternalDataResult,
    PolygonConnector,
    AlphaVantageConnector,
    DataSourceType,
    merge_external_with_synthetic,
    calculate_portfolio_metrics
)

from .data_simulator import (
    DataSimulator,
    DomainDataGenerator,
    DataRequirements,
    DataQuality,
    SimulatedDataset,
    ExtractedData,
    DataSufficiencyReport
)

from .data_integrator import (
    OptimizationDataIntegrator
)

from .llm_adapter import (
    LLMManager,
    LLMRequest,
    LLMResponse
)

from .interfaces import (
    OptimizationProblemType,
    ParsedProblem,
    DecisionVariable,
    Constraint,
    ObjectiveFunction,
    VariableType,
    ConstraintType,
    Dataset,
    DatasetRegistry,
    ProblemType
)

from .exceptions import (
    DataIntegrationError,
    ExternalDataError,
    DataValidationError,
    DataSimulationError
)

__all__ = [
    # External connectors
    'ExternalDataManager',
    'ExternalDataResult',
    'PolygonConnector',
    'AlphaVantageConnector',
    'DataSourceType',
    'merge_external_with_synthetic',
    'calculate_portfolio_metrics',
    
    # Data simulator
    'DataSimulator',
    'DomainDataGenerator',
    'DataRequirements',
    'DataQuality',
    'SimulatedDataset',
    'ExtractedData',
    'DataSufficiencyReport',
    
    # Data integrator
    'OptimizationDataIntegrator',
    
    # LLM adapter
    'LLMManager',
    'LLMRequest',
    'LLMResponse',
    
    # Interfaces
    'OptimizationProblemType',
    'ParsedProblem',
    'DecisionVariable',
    'Constraint',
    'ObjectiveFunction',
    'VariableType',
    'ConstraintType',
    'Dataset',
    'DatasetRegistry',
    'ProblemType',
    
    # Exceptions
    'DataIntegrationError',
    'ExternalDataError',
    'DataValidationError',
    'DataSimulationError'
]


