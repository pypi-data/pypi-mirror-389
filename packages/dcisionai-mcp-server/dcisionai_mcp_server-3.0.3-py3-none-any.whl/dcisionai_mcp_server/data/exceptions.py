"""
Data integration exceptions
"""


class DataIntegrationError(Exception):
    """Base exception for data integration errors"""
    pass


class ExternalDataError(DataIntegrationError):
    """External data source errors"""
    pass


class DataValidationError(DataIntegrationError):
    """Data validation errors"""
    pass


class DataSimulationError(DataIntegrationError):
    """Data simulation errors"""
    pass

