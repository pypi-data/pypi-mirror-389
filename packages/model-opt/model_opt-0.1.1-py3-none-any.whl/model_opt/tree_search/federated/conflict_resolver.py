"""Conflict resolution using statistical testing."""
from typing import Dict, Any, Optional
import math

try:
    from scipy.stats import t as t_dist
    _SCIPY_AVAILABLE = True
except ImportError:
    _SCIPY_AVAILABLE = False
    t_dist = None

try:
    import numpy as np
    _NUMPY_AVAILABLE = True
except ImportError:
    _NUMPY_AVAILABLE = False
    np = None


class ConflictResolver:
    """Resolve conflicts using statistical testing."""
    
    def resolve_conflict(
        self,
        local_edge: Dict[str, Any],
        fed_edge: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Statistical testing for significant disagreements.
        
        Args:
            local_edge: Local edge data
            fed_edge: Federated edge data
            
        Returns:
            Resolution decision dictionary
        """
        local_weights = local_edge.get('weights', {})
        fed_weights = fed_edge.get('weights', {})
        
        local_weight = local_weights.get('success_probability', 0.5)
        fed_weight = fed_weights.get('success_probability', 0.5)
        delta = abs(local_weight - fed_weight)
        
        # Auto-merge if difference is small
        if delta <= 0.3:
            return {
                'action': 'auto_merge',
                'method': 'weighted_average',
                'reason': 'difference_within_tolerance'
            }
        
        # Perform Welch's t-test if scipy available
        if not _SCIPY_AVAILABLE:
            # Fallback: use sample size heuristic
            return self._resolve_by_heuristic(local_edge, fed_edge, delta)
        
        local_samples = local_weights.get('sample_count', 0)
        fed_samples = fed_weights.get('sample_count', 0)
        
        # Need sufficient samples for statistical test
        if local_samples < 5 or fed_samples < 5:
            return self._resolve_by_heuristic(local_edge, fed_edge, delta)
        
        # Get variance
        local_var = local_weights.get('variance', 0.01)
        if 'reward_history' in local_edge:
            local_rewards = local_edge['reward_history']
            if _NUMPY_AVAILABLE and len(local_rewards) > 1:
                local_var = float(np.var(local_rewards))
        
        fed_var = fed_weights.get('variance', 0.01)
        if 'reward_history' in fed_edge:
            fed_rewards = fed_edge['reward_history']
            if _NUMPY_AVAILABLE and len(fed_rewards) > 1:
                fed_var = float(np.var(fed_rewards))
        
        # t-statistic (Welch's t-test)
        se_local = math.sqrt(local_var / local_samples) if local_samples > 0 else 0.1
        se_fed = math.sqrt(fed_var / fed_samples) if fed_samples > 0 else 0.1
        se_diff = math.sqrt(se_local ** 2 + se_fed ** 2)
        
        if se_diff == 0:
            return self._resolve_by_heuristic(local_edge, fed_edge, delta)
        
        t_stat = (local_weight - fed_weight) / se_diff
        
        # Degrees of freedom (Welch-Satterthwaite)
        df_numerator = (se_local ** 2 + se_fed ** 2) ** 2
        df_denominator = (
            (se_local ** 2) ** 2 / (local_samples - 1) +
            (se_fed ** 2) ** 2 / (fed_samples - 1)
        )
        
        if df_denominator == 0:
            df = min(local_samples, fed_samples) - 1
        else:
            df = df_numerator / df_denominator
        
        # p-value from t-distribution
        try:
            p_value = 2 * (1 - t_dist.cdf(abs(t_stat), df))
        except Exception:
            return self._resolve_by_heuristic(local_edge, fed_edge, delta)
        
        # Decision based on p-value
        if p_value < 0.05:
            # Statistically significant difference
            if local_samples >= 20:
                return {
                    'action': 'accept_local',
                    'reason': 'significant_improvement_validated',
                    'p_value': float(p_value),
                    't_statistic': float(t_stat)
                }
            else:
                return {
                    'action': 'request_validation',
                    'reason': 'significant_but_low_samples',
                    'required_samples': 20,
                    'p_value': float(p_value),
                    't_statistic': float(t_stat)
                }
        else:
            # Not significant, keep federated
            return {
                'action': 'keep_federated',
                'reason': 'insufficient_evidence',
                'p_value': float(p_value),
                't_statistic': float(t_stat)
            }
    
    def _resolve_by_heuristic(
        self,
        local_edge: Dict[str, Any],
        fed_edge: Dict[str, Any],
        delta: float
    ) -> Dict[str, Any]:
        """Resolve conflict using heuristics when statistical test unavailable.
        
        Args:
            local_edge: Local edge data
            fed_edge: Federated edge data
            delta: Weight difference
            
        Returns:
            Resolution decision
        """
        local_samples = local_edge.get('weights', {}).get('sample_count', 0)
        fed_samples = fed_edge.get('weights', {}).get('sample_count', 0)
        
        # If local has significantly more samples and better performance
        if local_samples > fed_samples * 2 and local_samples >= 20:
            local_weight = local_edge.get('weights', {}).get('success_probability', 0.5)
            fed_weight = fed_edge.get('weights', {}).get('success_probability', 0.5)
            
            if local_weight > fed_weight:
                return {
                    'action': 'accept_local',
                    'reason': 'more_samples_and_better_performance',
                    'delta': float(delta)
                }
        
        # If federated has much more validation
        if fed_samples > local_samples * 5:
            return {
                'action': 'keep_federated',
                'reason': 'federated_has_more_validation',
                'delta': float(delta)
            }
        
        # Default: weighted average
        return {
            'action': 'auto_merge',
            'method': 'weighted_average',
            'reason': 'insufficient_samples_for_statistical_test',
            'delta': float(delta)
        }
    
    def apply_resolution(
        self,
        resolution: Dict[str, Any],
        local_edge: Dict[str, Any],
        fed_edge: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply resolution decision to edge.
        
        Args:
            resolution: Resolution decision from resolve_conflict()
            local_edge: Local edge data
            fed_edge: Federated edge data
            
        Returns:
            Resolved edge data
        """
        action = resolution.get('action', 'auto_merge')
        
        if action == 'accept_local':
            # Use local edge data
            resolved = dict(local_edge)
            resolved['metadata'] = {
                'resolution': 'accept_local',
                'reason': resolution.get('reason', ''),
                'resolved_at': resolution.get('timestamp', '')
            }
            return resolved
        
        elif action == 'keep_federated':
            # Keep federated edge data
            resolved = dict(fed_edge)
            resolved['metadata'] = {
                'resolution': 'keep_federated',
                'reason': resolution.get('reason', ''),
                'resolved_at': resolution.get('timestamp', '')
            }
            return resolved
        
        else:  # auto_merge
            # Weighted average based on sample counts
            local_samples = local_edge.get('weights', {}).get('sample_count', 0)
            fed_samples = fed_edge.get('weights', {}).get('sample_count', 0)
            total_samples = local_samples + fed_samples
            
            if total_samples == 0:
                beta = 0.5
            else:
                beta = local_samples / total_samples
                # Cap beta
                beta = max(0.1, min(0.7, beta))
            
            local_weight = local_edge.get('weights', {}).get('success_probability', 0.5)
            fed_weight = fed_edge.get('weights', {}).get('success_probability', 0.5)
            
            merged_weight = fed_weight * (1.0 - beta) + local_weight * beta
            merged_samples = total_samples
            
            resolved = {
                'weights': {
                    'success_probability': float(merged_weight),
                    'sample_count': int(merged_samples)
                },
                'metadata': {
                    'resolution': 'auto_merge',
                    'method': 'weighted_average',
                    'merge_beta': float(beta),
                    'reason': resolution.get('reason', '')
                }
            }
            
            return resolved

