"""Stable Diffusion pruning using ToMe (Token Merging)."""
from typing import Any, Dict, Optional
import torch


class StableDiffusionPruner:
	"""Stable Diffusion model pruning using ToMe (Token Merging).
	
	ToMe (Token Merging) is a method for accelerating Stable Diffusion models
	by merging redundant tokens in the attention mechanism. This allows for
	significant speedup with minimal quality loss.
	"""
	
	def __init__(self):
		"""Initialize StableDiffusionPruner with ToMe utilities."""
		try:
			import tomesd
			self._tomesd = tomesd
			self._tomesd_available = True
		except ImportError:
			self._tomesd_available = False
			raise ImportError(
				"tomesd not installed. Install with: pip install tomesd"
			)
	
	def apply_patch(
		self,
		model: torch.nn.Module,
		ratio: float = 0.5,
		sx: int = 2,
		sy: int = 2,
		max_downsample: int = 1,
		use_rand: bool = True,
		merge_attn: bool = True,
		merge_crossattn: bool = False,
		merge_mlp: bool = False
	) -> torch.nn.Module:
		"""Patch a Stable Diffusion model with ToMe for token merging.
		
		Using the default options are recommended for the highest quality.
		Tune ratio to suit your needs. You can patch the same model multiple times.
		
		Args:
			model: Stable Diffusion model to patch
			ratio: Token merging ratio (0.0 to 1.0). Higher values merge more tokens.
				Default 0.5 is recommended for good balance between speed and quality.
			sx: Token merging stride in x direction. Default: 2
			sy: Token merging stride in y direction. Default: 2
			max_downsample: Maximum downsample factor for merging. Default: 1
			use_rand: Whether to use random merging strategy. Default: True
			merge_attn: Whether to merge tokens in attention layers. Default: True
			merge_crossattn: Whether to merge tokens in cross-attention layers.
				Default: False
			merge_mlp: Whether to merge tokens in MLP layers. Default: False
		
		Returns:
			The patched model (modified in-place)
		
		Raises:
			ImportError: If tomesd is not installed
			RuntimeError: If patching fails
		
		Example:
			>>> # Basic usage with recommended defaults
			>>> pruner = StableDiffusionPruner()
			>>> model = pruner.apply_patch(model, ratio=0.5)
			>>> 
			>>> # Extreme merging for maximum speedup
			>>> model = pruner.apply_patch(
			...     model, ratio=0.9, sx=4, sy=4, max_downsample=2
			... )
		"""
		if not self._tomesd_available:
			raise ImportError(
				"tomesd not installed. Install with: pip install tomesd"
			)
		
		if not (0.0 <= ratio <= 1.0):
			raise ValueError(f"Ratio must be between 0.0 and 1.0, got {ratio}")
		
		try:
			self._tomesd.apply_patch(
				model,
				ratio=ratio,
				sx=sx,
				sy=sy,
				max_downsample=max_downsample,
				use_rand=use_rand,
				merge_attn=merge_attn,
				merge_crossattn=merge_crossattn,
				merge_mlp=merge_mlp
			)
			return model
		except Exception as e:
			raise RuntimeError(f"ToMe SD patching failed: {e}") from e
	
	def remove_patch(self, model: torch.nn.Module) -> torch.nn.Module:
		"""Remove ToMe patches from a Stable Diffusion model.
		
		Args:
			model: Stable Diffusion model to remove patches from
		
		Returns:
			The model with patches removed (modified in-place)
		
		Raises:
			ImportError: If tomesd is not installed
			RuntimeError: If patch removal fails
		"""
		if not self._tomesd_available:
			raise ImportError(
				"tomesd not installed. Install with: pip install tomesd"
			)
		
		try:
			self._tomesd.remove_patch(model)
			return model
		except Exception as e:
			raise RuntimeError(f"ToMe SD patch removal failed: {e}") from e
	
	def prune(
		self,
		model: torch.nn.Module,
		ratio: float = 0.5,
		sx: int = 2,
		sy: int = 2,
		max_downsample: int = 1,
		use_rand: bool = True,
		merge_attn: bool = True,
		merge_crossattn: bool = False,
		merge_mlp: bool = False
	) -> torch.nn.Module:
		"""Apply ToMe token merging to Stable Diffusion model (convenience method).
		
		This is an alias for apply_patch() to maintain consistency with other
		pruning interfaces.
		
		Args:
			model: Stable Diffusion model to prune
			ratio: Token merging ratio (0.0 to 1.0). Default: 0.5
			sx: Token merging stride in x direction. Default: 2
			sy: Token merging stride in y direction. Default: 2
			max_downsample: Maximum downsample factor. Default: 1
			use_rand: Whether to use random merging. Default: True
			merge_attn: Whether to merge attention tokens. Default: True
			merge_crossattn: Whether to merge cross-attention tokens. Default: False
			merge_mlp: Whether to merge MLP tokens. Default: False
		
		Returns:
			The pruned model (modified in-place)
		"""
		return self.apply_patch(
			model,
			ratio=ratio,
			sx=sx,
			sy=sy,
			max_downsample=max_downsample,
			use_rand=use_rand,
			merge_attn=merge_attn,
			merge_crossattn=merge_crossattn,
			merge_mlp=merge_mlp
		)
	
	def estimate_speedup(self, ratio: float) -> float:
		"""Estimate speedup factor based on token merging ratio.
		
		This is a rough estimate. Actual speedup depends on model architecture,
		hardware, and other factors.
		
		Args:
			ratio: Token merging ratio (0.0 to 1.0)
		
		Returns:
			Estimated speedup factor (e.g., 1.5 means 1.5x faster)
		"""
		# Rough approximation: speedup scales roughly with (1 - ratio)^-1
		# This is a simplified model and actual results may vary
		if ratio <= 0:
			return 1.0
		if ratio >= 1.0:
			return float('inf')  # Theoretical maximum
		
		# Empirical approximation based on typical ToMe performance
		# Higher ratios provide more speedup but with diminishing returns
		speedup = 1.0 / (1.0 - ratio * 0.6)  # Conservative estimate
		return min(speedup, 3.0)  # Cap at reasonable maximum

