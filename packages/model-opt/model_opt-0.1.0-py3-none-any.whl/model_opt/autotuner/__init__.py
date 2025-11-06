"""Autotuner: Intelligent model compression strategy selection using tree search."""

from .search_space import (
    ArchitectureFamily,
    CompressionTechnique,
    ModelSignature,
    CompressionResult,
    SearchNode,
)
from .tree_search import CompressionTreeSearch
from .intelligent_optimizer import IntelligentOptimizer

# Optional MCTS exports
try:
    from model_opt.tree_search import (
        EnhancedSearchNode,
        MCTSEngine,
        ZeroShotRollout,
        FederatedStorage,
        ArchitecturePriors,
    )
    _MCTS_EXPORTS = [
        "EnhancedSearchNode",
        "MCTSEngine",
        "ZeroShotRollout",
        "FederatedStorage",
        "ArchitecturePriors",
    ]
except ImportError:
    _MCTS_EXPORTS = []

__all__ = [
    "ArchitectureFamily",
    "CompressionTechnique",
    "ModelSignature",
    "CompressionResult",
    "SearchNode",
    "CompressionTreeSearch",
    "IntelligentOptimizer",
] + _MCTS_EXPORTS

