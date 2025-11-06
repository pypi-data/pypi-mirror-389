"""Enhanced SearchNode with MCTS fields for tree search."""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

from model_opt.autotuner.search_space import (
    ModelSignature,
    CompressionTechnique,
    CompressionResult,
    SearchNode as BaseSearchNode,
)


@dataclass
class EnhancedSearchNode(BaseSearchNode):
    """Enhanced search node with MCTS-specific fields."""
    
    # Required fields from BaseSearchNode (no defaults - must be provided)
    signature: ModelSignature  # Required, no default
    parent: Optional['EnhancedSearchNode'] = None
    techniques_applied: List[CompressionTechnique] = field(default_factory=list)
    result: Optional[CompressionResult] = None
    children: List['EnhancedSearchNode'] = field(default_factory=list)
    visit_count: int = 0
    total_reward: float = 0.0
    
    # MCTS fields
    confidence: float = 0.0
    q_value: float = 0.0
    prior_probability: float = 0.0
    sample_count: int = 0
    
    # Federated fields
    federated_prior: Optional[float] = None
    source_count: int = 0  # Number of sources contributing to this node
    
    def ucb_score_with_prior(
        self,
        exploration_weight: float = 1.41,
        prior_weight: float = 0.5
    ) -> float:
        """Calculate UCB1 score with federated priors.
        
        Args:
            exploration_weight: Exploration constant (default: 1.41).
            prior_weight: Weight for prior probability (0.0 to 1.0).
            
        Returns:
            UCB1 score with prior adjustment.
        """
        if self.visit_count == 0:
            return float('inf')
        
        if self.parent is None:
            return 0.0
        
        # Standard UCB1 components
        exploitation = self.q_value / self.visit_count if self.visit_count > 0 else 0.0
        exploration = exploration_weight * (self.parent.visit_count ** 0.5) / self.visit_count
        
        # Prior adjustment
        prior_adjustment = 0.0
        if self.federated_prior is not None:
            prior_adjustment = prior_weight * self.federated_prior
        elif self.prior_probability > 0:
            prior_adjustment = prior_weight * self.prior_probability
        
        return exploitation + exploration + prior_adjustment
    
    def update_from_result(self, result: CompressionResult):
        """Update node statistics from compression result.
        
        Args:
            result: CompressionResult from evaluation
        """
        self.result = result
        
        # Calculate reward (higher is better)
        # Reward = compression_ratio * speedup - accuracy_drop_penalty
        accuracy_penalty = result.accuracy_drop * 10.0  # Scale penalty
        reward = (result.compression_ratio * result.speedup) - accuracy_penalty
        
        # Update Q-value (running average)
        if self.visit_count == 0:
            self.q_value = reward
        else:
            # Running average update
            self.q_value = (self.q_value * self.visit_count + reward) / (self.visit_count + 1)
        
        self.visit_count += 1
        
        # Update confidence based on visit count and sample count
        self.confidence = min(1.0, (self.visit_count + self.sample_count) / 10.0)
    
    def get_best_child(self) -> Optional['EnhancedSearchNode']:
        """Get child with highest Q-value.
        
        Returns:
            Best child node or None if no children
        """
        if not self.children:
            return None
        
        return max(self.children, key=lambda c: c.q_value if c.visit_count > 0 else float('-inf'))
    
    def get_most_visited_child(self) -> Optional['EnhancedSearchNode']:
        """Get child with highest visit count.
        
        Returns:
            Most visited child node or None if no children
        """
        if not self.children:
            return None
        
        return max(self.children, key=lambda c: c.visit_count)

