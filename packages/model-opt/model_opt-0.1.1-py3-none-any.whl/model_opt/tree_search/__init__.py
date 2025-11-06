"""MCTS tree search for compression strategy optimization."""
# Import FederatedStorage from federated.py file (not federated/ directory)
import importlib.util
import os
_federated_py_path = os.path.join(os.path.dirname(__file__), 'federated.py')
if os.path.exists(_federated_py_path):
    _spec = importlib.util.spec_from_file_location("_federated_storage_module", _federated_py_path)
    _federated_module = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_federated_module)
    FederatedStorage = _federated_module.FederatedStorage
else:
    FederatedStorage = None

from .nodes import EnhancedSearchNode
from .mcts_engine import MCTSEngine
from .rollout import ZeroShotRollout
from .priors import ArchitecturePriors

# Optional federated tree operations
try:
    from .federated import (
        FederatedTreeOperations,
        FederatedTreeStorage,
        FederatedMergeOperations,
        ConflictResolver,
        FederatedTreeManager,
    )
    _FEDERATED_TREE_AVAILABLE = True
    _FEDERATED_EXPORTS = [
        'FederatedTreeOperations',
        'FederatedTreeStorage',
        'FederatedMergeOperations',
        'ConflictResolver',
        'FederatedTreeManager',
    ]
except ImportError:
    _FEDERATED_TREE_AVAILABLE = False
    _FEDERATED_EXPORTS = []

__all__ = [
    'EnhancedSearchNode',
    'MCTSEngine',
    'ZeroShotRollout',
    'FederatedStorage',
    'ArchitecturePriors',
] + _FEDERATED_EXPORTS

