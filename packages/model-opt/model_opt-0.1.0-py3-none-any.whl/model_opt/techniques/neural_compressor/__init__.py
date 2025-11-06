"""Intel Neural Compressor integration."""
from typing import Optional

try:
    import neural_compressor
    _NEURAL_COMPRESSOR_AVAILABLE = True
except ImportError:
    _NEURAL_COMPRESSOR_AVAILABLE = False
    neural_compressor = None

if _NEURAL_COMPRESSOR_AVAILABLE:
    from .inc_optimizer import NeuralCompressorOptimizer
else:
    NeuralCompressorOptimizer = None

__all__ = [
    'NeuralCompressorOptimizer',
    '_NEURAL_COMPRESSOR_AVAILABLE',
]

