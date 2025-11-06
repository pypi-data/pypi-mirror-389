"""Model optimization toolkit package."""

from .core.optimizer import Optimizer
from .core.model_loader import analyze_model

# Try importing optional modules
try:
	from .autotuner import IntelligentOptimizer
except ImportError:
	IntelligentOptimizer = None

try:
	from .agent import ResearchAgent
except ImportError:
	ResearchAgent = None

try:
	from .techniques import Quantizer, Pruner, LayerFuser, Decomposer
except ImportError:
	Quantizer = None
	Pruner = None
	LayerFuser = None
	Decomposer = None

__version__ = "0.1.0"

__all__ = [
	"Optimizer",
	"analyze_model",
	"IntelligentOptimizer",
	"ResearchAgent",
	"Quantizer",
	"Pruner",
	"LayerFuser",
	"Decomposer",
	"__version__",
]


