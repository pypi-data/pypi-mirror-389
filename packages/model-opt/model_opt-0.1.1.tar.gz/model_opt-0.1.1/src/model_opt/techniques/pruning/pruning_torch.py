"""Torch-Pruning structured pruning wrapper (PyTorch)."""
from typing import Any, Dict, Optional
import torch


class StructuredPruner:
	"""Structured pruning using Torch-Pruning."""
	
	def __init__(self):
		"""Initialize StructuredPruner with available importance metrics."""
		try:
			import torch_pruning as tp
			self._tp = tp
			self._torch_pruning_available = True
		except ImportError:
			self._torch_pruning_available = False
			raise ImportError(
				"torch-pruning not installed. Install with: pip install torch-pruning"
			)
		
		# Initialize importance metrics
		# Try to initialize available metrics (some may not be available in all versions)
		self.importance_metrics = {}
		
		# Magnitude importance (always available)
		self.importance_metrics['magnitude'] = self._tp.importance.MagnitudeImportance()
		
		# Taylor importance (if available)
		try:
			self.importance_metrics['taylor'] = self._tp.importance.TaylorImportance()
		except (AttributeError, TypeError):
			pass
		
		# Group Taylor importance (GroupTaylorImportance in torch-pruning)
		try:
			if hasattr(self._tp.importance, 'GroupTaylorImportance'):
				self.importance_metrics['group_taylor'] = self._tp.importance.GroupTaylorImportance()
				# Also support 'group_norm' as an alias for backward compatibility
				self.importance_metrics['group_norm'] = self.importance_metrics['group_taylor']
		except (AttributeError, TypeError):
			pass
	
	def prune(
		self,
		model: torch.nn.Module,
		example_input: torch.Tensor,
		pruning_ratio: float = 0.3,
		importance: str = 'magnitude'
	) -> torch.nn.Module:
		"""Apply structured pruning to a model.
		
		Args:
			model: PyTorch model to prune (modified in-place)
			example_input: Example input tensor for dependency graph construction
			pruning_ratio: Fraction of channels/filters to prune (0.0 to 1.0)
			importance: Importance metric to use. Options:
				- 'magnitude': Magnitude-based importance (always available)
				- 'taylor': Taylor expansion-based importance (if available)
				- 'group_taylor' or 'group_norm': Group-based importance (if available)
		
		Returns:
			The pruned model (same object, modified in-place)
		
		Raises:
			ImportError: If torch-pruning is not installed
			ValueError: If importance metric is not supported
			RuntimeError: If pruning fails
		"""
		if not self._torch_pruning_available:
			raise ImportError(
				"torch-pruning not installed. Install with: pip install torch-pruning"
			)
		
		if importance not in self.importance_metrics:
			raise ValueError(
				f"Unknown importance metric: {importance}. "
				f"Supported metrics: {list(self.importance_metrics.keys())}"
			)
		
		try:
			# Build dependency graph
			DG = self._tp.DependencyGraph().build_dependency(
				model,
				example_inputs=example_input
			)
			
			# Get importance metric
			imp_metric = self.importance_metrics[importance]
			
			# Create pruner
			pruner = self._tp.pruner.MagnitudePruner(
				model,
				example_input,
				importance=imp_metric,
				pruning_ratio=pruning_ratio,
			)
			
			# Prune in one shot
			pruner.step()
			
			return model
		
		except Exception as e:
			raise RuntimeError(f"Torch-Pruning structured pruning failed: {e}") from e
	
	def estimate_flops_reduction(self, pruning_ratio: float) -> float:
		"""Estimate FLOP reduction based on pruning ratio.
		
		For structured pruning, FLOP reduction is typically close to the pruning ratio
		since entire channels/filters are removed.
		
		Args:
			pruning_ratio: Fraction of channels/filters pruned (0.0 to 1.0)
		
		Returns:
			Estimated FLOP reduction ratio (0.0 to 1.0)
		"""
		return pruning_ratio
	
	def get_supported_importance_metrics(self) -> list:
		"""Get list of supported importance metrics.
		
		Returns:
			List of supported importance metric names
		"""
		return list(self.importance_metrics.keys())

