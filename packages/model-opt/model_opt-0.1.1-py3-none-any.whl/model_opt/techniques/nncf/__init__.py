"""NNCF (Neural Network Compression Framework) integration."""
from typing import Optional

try:
    import nncf
    _NNCF_AVAILABLE = True
except ImportError:
    _NNCF_AVAILABLE = False
    nncf = None

if _NNCF_AVAILABLE:
    from .nncf_quantizer import NNCFQuantizer
    from .nncf_pruner import NNCFPruner
else:
    NNCFQuantizer = None
    NNCFPruner = None

__all__ = [
    'NNCFQuantizer',
    'NNCFPruner',
    '_NNCF_AVAILABLE',
]

