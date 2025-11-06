"""MCTS engine for compression strategy optimization."""
import random
from typing import Dict, List, Optional, Any, Tuple
import time

try:
    import torch
    import torch.nn as nn
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False

from model_opt.autotuner.search_space import (
    ModelSignature,
    CompressionTechnique,
    CompressionResult,
)
from .nodes import EnhancedSearchNode
from .priors import ArchitecturePriors
from .rollout import ZeroShotRollout

# Import FederatedStorage from federated.py (file, not directory)
# Use importlib to avoid conflicts with federated/ directory
import importlib.util
import os
_federated_py_path = os.path.join(os.path.dirname(__file__), 'federated.py')
if os.path.exists(_federated_py_path):
    _spec = importlib.util.spec_from_file_location("_federated_storage_module", _federated_py_path)
    _federated_module = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_federated_module)
    FederatedStorage = _federated_module.FederatedStorage
else:
    # Fallback if file doesn't exist
    FederatedStorage = None

from model_opt.autotuner.tree_search import CompressionTreeSearch

# Optional federated tree manager integration
try:
    from .federated.manager import FederatedTreeManager
    _FEDERATED_TREE_AVAILABLE = True
except ImportError:
    _FEDERATED_TREE_AVAILABLE = False
    FederatedTreeManager = None


class MCTSEngine:
    """Monte Carlo Tree Search engine for compression strategy."""
    
    def __init__(
        self,
        tree_search: Optional[CompressionTreeSearch] = None,
        storage_backend: Optional[Any] = None,
        n_simulations: int = 50,
        exploration_weight: float = 1.41,
        timeout_seconds: float = 300.0,
        federated_tree_manager: Optional[Any] = None,
        vector_db: Optional[Any] = None
    ):
        """Initialize MCTS engine.
        
        Args:
            tree_search: Optional CompressionTreeSearch instance
            storage_backend: Optional storage backend for federated learning
            n_simulations: Number of MCTS simulations (default: 50)
            exploration_weight: UCB exploration constant (default: 1.41)
            timeout_seconds: Maximum time for search (default: 300s)
            federated_tree_manager: Optional FederatedTreeManager instance
            vector_db: Optional vector database for paper expansion
        """
        if not _TORCH_AVAILABLE:
            raise ImportError("PyTorch is required for MCTSEngine")
        
        self.tree_search = tree_search or CompressionTreeSearch()
        self.federated = FederatedStorage(storage_backend)
        self.priors = ArchitecturePriors()
        self.rollout = ZeroShotRollout()
        
        # Optional federated tree manager for NetworkX-based trees
        self.federated_tree_manager = federated_tree_manager
        if _FEDERATED_TREE_AVAILABLE and federated_tree_manager is None and storage_backend is not None:
            try:
                from .federated.manager import FederatedTreeManager
                self.federated_tree_manager = FederatedTreeManager(
                    storage_backend=storage_backend,
                    vector_db=vector_db
                )
            except Exception:
                pass
        
        self.n_simulations = n_simulations
        self.exploration_weight = exploration_weight
        self.timeout_seconds = timeout_seconds
        
        self.root: Optional[EnhancedSearchNode] = None
    
    def search(
        self,
        model: nn.Module,
        signature: ModelSignature,
        constraints: Optional[Dict[str, float]] = None,
        example_input: Optional[Any] = None
    ) -> Tuple[List[CompressionTechnique], CompressionResult]:
        """Run MCTS search to find optimal compression strategy.
        
        Args:
            model: PyTorch model to optimize
            signature: Model signature
            constraints: Optional constraints dict
            example_input: Optional example input tensor
            
        Returns:
            Tuple of (best_techniques, best_result)
        """
        start_time = time.time()
        
        # Initialize root node
        self.root = EnhancedSearchNode(
            signature=signature,
            parent=None,
            techniques_applied=[],
            result=None,
            children=[],
            visit_count=0,
            total_reward=0.0
        )
        
        # Set priors from architecture
        priors = self.priors.get_priors(signature, constraints)
        for tech, prob in priors.items():
            # Set federated prior if available
            fed_prior = self.federated.get_federated_prior(signature, tech)
            if fed_prior is not None:
                # Combine architecture prior with federated prior
                combined_prior = (prob + fed_prior) / 2.0
            else:
                combined_prior = prob
            
            # Create child node with prior
            child = EnhancedSearchNode(
                signature=signature,
                parent=self.root,
                techniques_applied=[tech],
                result=None,
                children=[],
                visit_count=0,
                total_reward=0.0,
                prior_probability=prob,
                federated_prior=fed_prior
            )
            child.sample_count = self.federated.get_sample_count(signature, tech)
            self.root.children.append(child)
        
        # Run MCTS simulations
        for sim in range(self.n_simulations):
            if time.time() - start_time > self.timeout_seconds:
                break
            
            # Selection: Choose path to leaf
            leaf = self._select(self.root)
            
            # Expansion: Add children if not terminal
            if leaf.visit_count == 0:
                # New node - run rollout
                result = self._simulate(model, leaf, example_input)
                leaf.update_from_result(result)
                
                # Update federated storage
                if leaf.techniques_applied:
                    for tech in leaf.techniques_applied:
                        self.federated.update_result(signature, tech, result)
            else:
                # Expand if possible
                if not leaf.children:
                    self._expand(leaf, signature, constraints)
                
                # Select best child and simulate
                if leaf.children:
                    child = max(leaf.children, key=lambda c: c.ucb_score_with_prior())
                    result = self._simulate(model, child, example_input)
                    child.update_from_result(result)
                    
                    # Update federated storage
                    for tech in child.techniques_applied:
                        self.federated.update_result(signature, tech, result)
                
                # Backpropagation
                self._backpropagate(leaf, result)
        
        # Get best strategy
        best_node = self.root.get_best_child()
        if best_node is None:
            # Fallback to most visited
            best_node = self.root.get_most_visited_child()
        
        if best_node is None or best_node.result is None:
            # Fallback to rule-based
            techniques = self.tree_search.recommend_techniques(signature, constraints)
            result = self._simulate(model, self.root, example_input)
            return techniques, result
        
        return best_node.techniques_applied, best_node.result
    
    def _select(self, node: EnhancedSearchNode) -> EnhancedSearchNode:
        """Select path to leaf using UCB1.
        
        Args:
            node: Current node
            
        Returns:
            Leaf node
        """
        while node.children:
            # Choose child with highest UCB score
            best_child = max(
                node.children,
                key=lambda c: c.ucb_score_with_prior(self.exploration_weight)
            )
            node = best_child
        
        return node
    
    def _expand(
        self,
        node: EnhancedSearchNode,
        signature: ModelSignature,
        constraints: Optional[Dict]
    ):
        """Expand node by adding children for available techniques.
        
        Args:
            node: Node to expand
            signature: Model signature
            constraints: Optional constraints
        """
        # Get available techniques based on current path
        available_techniques = self._get_available_techniques(
            node.techniques_applied,
            signature,
            constraints
        )
        
        # Create child nodes
        for technique in available_techniques:
            new_techniques = node.techniques_applied + [technique]
            
            # Get priors
            priors = self.priors.get_priors(signature, constraints)
            prior_prob = priors.get(technique, 0.1)
            fed_prior = self.federated.get_federated_prior(signature, technique)
            
            child = EnhancedSearchNode(
                signature=signature,
                parent=node,
                techniques_applied=new_techniques,
                result=None,
                children=[],
                visit_count=0,
                total_reward=0.0,
                prior_probability=prior_prob,
                federated_prior=fed_prior
            )
            child.sample_count = self.federated.get_sample_count(signature, technique)
            node.children.append(child)
    
    def _simulate(
        self,
        model: nn.Module,
        node: EnhancedSearchNode,
        example_input: Optional[Any]
    ) -> CompressionResult:
        """Simulate (rollout) from node to estimate reward.
        
        Args:
            model: Model to evaluate
            node: Node to simulate from
            example_input: Optional example input
            
        Returns:
            CompressionResult from rollout
        """
        # Use zero-shot rollout for fast evaluation
        original_size = self._get_model_size(model)
        
        result = self.rollout.evaluate_config(
            model,
            node.techniques_applied,
            example_input=example_input,
            original_size=original_size,
            timeout_seconds=30.0
        )
        
        return result
    
    def _backpropagate(
        self,
        node: EnhancedSearchNode,
        result: CompressionResult
    ):
        """Backpropagate result up the tree.
        
        Args:
            node: Node to start backpropagation from
            result: Result to propagate
        """
        current = node
        
        while current is not None:
            current.update_from_result(result)
            current = current.parent
    
    def _get_available_techniques(
        self,
        applied_techniques: List[CompressionTechnique],
        signature: ModelSignature,
        constraints: Optional[Dict]
    ) -> List[CompressionTechnique]:
        """Get available techniques that can be applied.
        
        Args:
            applied_techniques: Already applied techniques
            signature: Model signature
            constraints: Optional constraints
            
        Returns:
            List of available techniques
        """
        # Get base recommendations
        base_techniques = self.tree_search.recommend_techniques(signature, constraints)
        
        # Filter out already applied techniques
        available = [t for t in base_techniques if t not in applied_techniques]
        
        # Limit to reasonable number of techniques (avoid combinatorial explosion)
        max_techniques = 3
        if len(available) > max_techniques:
            # Prioritize by prior probability
            priors = self.priors.get_priors(signature, constraints)
            available.sort(key=lambda t: priors.get(t, 0.0), reverse=True)
            available = available[:max_techniques]
        
        return available
    
    def _get_model_size(self, model: nn.Module) -> float:
        """Get model size in MB."""
        param_size = sum(p.numel() * p.element_size() for p in model.parameters())
        buffer_size = sum(b.numel() * b.element_size() for b in model.buffers())
        total_size = param_size + buffer_size
        return total_size / (1024 * 1024)

