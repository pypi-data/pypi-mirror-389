"""Core APIs: analysis and optimization."""

from .model_loader import analyze_model
from .optimizer import Optimizer

# Core infrastructure modules
from .exceptions import (
	ModelOptError,
	ConfigurationError,
	ModelLoadError,
	OptimizationError,
	EnvironmentError,
	HardwareError,
)
from .cli_engine import CommandRouter
from .logger import StructuredLogger, get_logger
from .config import ConfigManager, load_config
from .environment import EnvironmentManager, get_environment_manager
from .model_zoo import ModelZoo, get_model_zoo
from .hardware import HardwareManager, get_hardware_manager

# Import IntelligentOptimizer from autotuner
try:
	from model_opt.autotuner.intelligent_optimizer import IntelligentOptimizer
	_INTELLIGENT_OPTIMIZER_AVAILABLE = True
except ImportError:
	_INTELLIGENT_OPTIMIZER_AVAILABLE = False
	IntelligentOptimizer = None

__all__ = [
	"analyze_model",
	"Optimizer",
	"IntelligentOptimizer",
	# Exceptions
	"ModelOptError",
	"ConfigurationError",
	"ModelLoadError",
	"OptimizationError",
	"EnvironmentError",
	"HardwareError",
	# CLI Engine
	"CommandRouter",
	# Logging
	"StructuredLogger",
	"get_logger",
	# Configuration
	"ConfigManager",
	"load_config",
	# Environment
	"EnvironmentManager",
	"get_environment_manager",
	# Model Zoo
	"ModelZoo",
	"get_model_zoo",
	# Hardware
	"HardwareManager",
	"get_hardware_manager",
]


