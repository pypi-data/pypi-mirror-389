"""Search space definitions for autotuner compression strategies."""

from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


class ArchitectureFamily(Enum):
    """Model architecture families for compression strategy selection."""

    CNN = "cnn"
    VIT = "vit"
    HYBRID = "hybrid"
    DIFFUSION = "diffusion"


class CompressionTechnique(Enum):
    """Available compression techniques."""

    QUANTIZE_INT8 = "quantize_int8"
    QUANTIZE_INT4 = "quantize_int4"
    QUANTIZE_FP8 = "quantize_fp8"
    PRUNE_STRUCTURED_30 = "prune_structured_30"
    PRUNE_STRUCTURED_50 = "prune_structured_50"
    TOKEN_MERGE_30 = "token_merge_30"
    SVD_50 = "svd_50"
    FUSE_LAYERS = "fuse_layers"


@dataclass
class ModelSignature:
    """Unique signature for model architecture."""

    family: ArchitectureFamily
    total_params: int
    num_layers: int
    has_attention: bool
    has_conv: bool

    def to_hash(self) -> str:
        """Create hash for lookup in knowledge base.

        Returns:
            Hash string in format: "{family}_{params_in_M}M_{layers}L"
        """
        params_m = self.total_params // 1000000
        return f"{self.family.value}_{params_m}M_{self.num_layers}L"


@dataclass
class CompressionResult:
    """Result of applying compression techniques."""

    techniques: List[CompressionTechnique]
    speedup: float
    compression_ratio: float
    accuracy_drop: float
    memory_reduction: float
    inference_time_ms: float


@dataclass
class SearchNode:
    """Node in the search tree for MCTS."""

    signature: ModelSignature
    parent: Optional['SearchNode']
    techniques_applied: List[CompressionTechnique]
    result: Optional[CompressionResult]
    children: List['SearchNode']
    visit_count: int
    total_reward: float

    def ucb_score(self, exploration_weight: float = 1.41) -> float:
        """Calculate UCB1 score for tree search.

        Args:
            exploration_weight: Exploration constant (default: 1.41, which is sqrt(2)).

        Returns:
            UCB1 score. Returns infinity if node has not been visited.
        """
        if self.visit_count == 0:
            return float('inf')

        if self.parent is None:
            return 0.0

        exploitation = self.total_reward / self.visit_count
        exploration = exploration_weight * (self.parent.visit_count ** 0.5) / self.visit_count

        return exploitation + exploration

