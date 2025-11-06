"""Merge operations for federated tree synchronization."""
import networkx as nx
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import math

try:
    import numpy as np
    _NUMPY_AVAILABLE = True
except ImportError:
    _NUMPY_AVAILABLE = False
    np = None


class FederatedMergeOperations:
    """Operations for merging local and federated trees."""
    
    def __init__(self, change_threshold: float = 0.15, conflict_threshold: float = 0.3):
        """Initialize merge operations.
        
        Args:
            change_threshold: Threshold for significant changes (default: 0.15)
            conflict_threshold: Threshold for conflicts (default: 0.3)
        """
        self.change_threshold = change_threshold
        self.conflict_threshold = conflict_threshold
    
    def detect_changes(
        self,
        local_tree: nx.DiGraph,
        fed_tree: nx.DiGraph
    ) -> Dict[str, Any]:
        """Identify significant changes between local and federated trees.
        
        Args:
            local_tree: Local tree
            fed_tree: Federated tree
            
        Returns:
            Dictionary with detected changes
        """
        changes = {
            'updated_edges': [],
            'new_edges': [],
            'new_nodes': [],
            'conflicts': []
        }
        
        # Find edges with significant weight changes
        for parent, child in local_tree.edges():
            if not fed_tree.has_edge(parent, child):
                # New edge discovered
                edge_data = local_tree.edges[parent, child]
                changes['new_edges'].append({
                    'edge': (parent, child),
                    'data': dict(edge_data)
                })
                continue
            
            # Compare edge weights
            local_edge = local_tree.edges[parent, child]
            fed_edge = fed_tree.edges[parent, child]
            
            local_weight = local_edge.get('weights', {}).get('success_probability', 0.5)
            fed_weight = fed_edge.get('weights', {}).get('success_probability', 0.5)
            
            delta = abs(local_weight - fed_weight)
            
            if delta > self.change_threshold:
                changes['updated_edges'].append({
                    'edge': (parent, child),
                    'local_weight': local_weight,
                    'fed_weight': fed_weight,
                    'delta': delta,
                    'local_samples': local_edge.get('weights', {}).get('sample_count', 0),
                    'fed_samples': fed_edge.get('weights', {}).get('sample_count', 0)
                })
                
                if delta > self.conflict_threshold:
                    changes['conflicts'].append({
                        'edge': (parent, child),
                        'requires_review': True,
                        'delta': delta
                    })
        
        # Find new nodes from vector DB expansion
        for node_id in local_tree.nodes():
            if node_id not in fed_tree.nodes():
                node_data = local_tree.nodes[node_id]
                source = node_data.get('source', {})
                
                if source.get('origin') == 'paper':
                    validation = node_data.get('validation', {})
                    sample_count = validation.get('sample_count', 0)
                    
                    if sample_count >= 3:
                        changes['new_nodes'].append({
                            'node_id': node_id,
                            'data': dict(node_data),
                            'validated': True
                        })
                    else:
                        changes['new_nodes'].append({
                            'node_id': node_id,
                            'data': dict(node_data),
                            'validated': False
                        })
        
        return changes
    
    def compute_merge_confidence(
        self,
        local_stats: Dict[str, Any],
        fed_stats: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate confidence scores for weighted merge.
        
        Args:
            local_stats: Local statistics
            fed_stats: Federated statistics
            
        Returns:
            Confidence scores dictionary
        """
        # Local confidence from sample size and consistency
        local_samples = local_stats.get('sample_count', 0)
        
        # Get variance from reward history if available
        reward_history = local_stats.get('reward_history', [0.5])
        if _NUMPY_AVAILABLE and len(reward_history) > 1:
            local_variance = float(np.var(reward_history))
        else:
            local_variance = 0.1  # Default variance
        
        validation_quality = 1.0 - min(local_variance, 0.5)  # lower variance = higher quality
        confidence_local = math.sqrt(local_samples) * validation_quality
        
        # Federated confidence from community validation
        fed_samples = fed_stats.get('sample_count', 0)
        fed_validators = fed_stats.get('validators', 1)
        validator_diversity = min(fed_validators / 10.0, 1.0)  # cap at 10 validators
        
        confidence_fed = math.sqrt(fed_samples) * validator_diversity
        
        # Compute merge weight (beta)
        total_confidence = confidence_local + confidence_fed
        if total_confidence > 0:
            beta = confidence_local / total_confidence
        else:
            beta = 0.5
        
        # Cap beta to prevent single user dominating
        beta = max(0.1, min(0.7, beta))
        
        return {
            'confidence_local': float(confidence_local),
            'confidence_fed': float(confidence_fed),
            'merge_weight_beta': float(beta)
        }
    
    def merge_edge_weight(
        self,
        local_edge: Dict[str, Any],
        fed_edge: Dict[str, Any],
        beta: float
    ) -> Dict[str, Any]:
        """Merge local discoveries into federated tree using confidence weighting.
        
        Args:
            local_edge: Local edge data
            fed_edge: Federated edge data
            beta: Merge weight (0.0 to 1.0)
            
        Returns:
            Merged edge data
        """
        local_weights = local_edge.get('weights', {})
        fed_weights = fed_edge.get('weights', {})
        
        local_weight = local_weights.get('success_probability', 0.5)
        fed_weight = fed_weights.get('success_probability', 0.5)
        
        # Weighted average
        merged_weight = fed_weight * (1.0 - beta) + local_weight * beta
        
        # Update sample count
        local_samples = local_weights.get('sample_count', 0)
        fed_samples = fed_weights.get('sample_count', 0)
        merged_samples = fed_samples + local_samples
        
        # Update variance (pooled variance formula)
        local_rewards = local_edge.get('reward_history', [local_weight])
        fed_rewards = fed_edge.get('reward_history', [fed_weight])
        
        if _NUMPY_AVAILABLE and len(local_rewards) > 1:
            local_var = float(np.var(local_rewards))
        else:
            local_var = 0.01
        
        if _NUMPY_AVAILABLE and len(fed_rewards) > 1:
            fed_var = float(np.var(fed_rewards))
        else:
            fed_var = fed_weights.get('variance', 0.01)
        
        # Pooled variance
        if merged_samples > 0:
            pooled_var = (
                fed_samples * fed_var + local_samples * local_var +
                fed_samples * (fed_weight - merged_weight) ** 2 +
                local_samples * (local_weight - merged_weight) ** 2
            ) / merged_samples
        else:
            pooled_var = 0.01
        
        # Compute confidence interval
        std_error = math.sqrt(pooled_var / merged_samples) if merged_samples > 0 else 0.1
        ci_lower = merged_weight - 1.96 * std_error
        ci_upper = merged_weight + 1.96 * std_error
        
        return {
            'weights': {
                'success_probability': float(merged_weight),
                'sample_count': int(merged_samples),
                'variance': float(pooled_var),
                'confidence_interval': [float(ci_lower), float(ci_upper)]
            },
            'metadata': {
                'last_updated': datetime.now().isoformat(),
                'merge_beta': float(beta),
                'previous_weight': float(fed_weight)
            }
        }
    
    def merge_trees(
        self,
        local_tree: nx.DiGraph,
        fed_tree: nx.DiGraph
    ) -> nx.DiGraph:
        """Merge local tree into federated tree.
        
        Args:
            local_tree: Local tree to merge
            fed_tree: Federated tree to merge into
            
        Returns:
            Merged tree
        """
        # Create copy of federated tree
        merged_tree = fed_tree.copy()
        
        # Detect changes
        changes = self.detect_changes(local_tree, fed_tree)
        
        # Merge updated edges
        for edge_info in changes['updated_edges']:
            parent, child = edge_info['edge']
            
            if not merged_tree.has_edge(parent, child):
                continue
            
            local_edge = local_tree.edges[parent, child]
            fed_edge = merged_tree.edges[parent, child]
            
            # Compute merge confidence
            local_stats = {
                'sample_count': local_edge.get('weights', {}).get('sample_count', 0),
                'reward_history': local_edge.get('reward_history', [])
            }
            fed_stats = {
                'sample_count': fed_edge.get('weights', {}).get('sample_count', 0),
                'validators': fed_edge.get('validators', 1)
            }
            
            confidence = self.compute_merge_confidence(local_stats, fed_stats)
            beta = confidence['merge_weight_beta']
            
            # Merge edge
            merged_edge_data = self.merge_edge_weight(local_edge, fed_edge, beta)
            merged_tree.edges[parent, child].update(merged_edge_data)
        
        # Add new edges
        for edge_info in changes['new_edges']:
            parent, child = edge_info['edge']
            edge_data = edge_info['data']
            
            # Ensure nodes exist
            if parent not in merged_tree.nodes():
                merged_tree.add_node(parent, **local_tree.nodes[parent])
            if child not in merged_tree.nodes():
                merged_tree.add_node(child, **local_tree.nodes[child])
            
            merged_tree.add_edge(parent, child, **edge_data)
        
        # Add validated new nodes
        for node_info in changes['new_nodes']:
            if node_info.get('validated', False):
                node_id = node_info['node_id']
                node_data = node_info['data']
                merged_tree.add_node(node_id, **node_data)
        
        return merged_tree

