"""Unified exception hierarchy for model-opt."""


class ModelOptError(Exception):
    """Base exception for all model-opt errors."""
    pass


class ConfigurationError(ModelOptError):
    """Error related to configuration loading or validation."""
    pass


class ModelLoadError(ModelOptError):
    """Error loading or parsing model files."""
    pass


class OptimizationError(ModelOptError):
    """Error during optimization process."""
    pass


class EnvironmentError(ModelOptError):
    """Error related to environment setup or dependencies."""
    pass


class HardwareError(ModelOptError):
    """Error related to hardware detection or resource management."""
    pass

