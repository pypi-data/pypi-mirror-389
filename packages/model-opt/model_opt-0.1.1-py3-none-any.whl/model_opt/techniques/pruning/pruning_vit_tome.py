"""Vision Transformer (ViT) pruning using ToMe (Token Merging)."""
from typing import Any, Dict, Optional
import torch


class ViTToMePruner:
	"""Vision Transformer pruning using ToMe (Token Merging).
	
	ToMe (Token Merging) is a method for accelerating Vision Transformer models
	by merging redundant tokens in the attention mechanism. This allows for
	significant speedup with minimal quality loss.
	"""
	
	def __init__(self):
		"""Initialize ViTToMePruner with ToMe utilities."""
		try:
			import tome
			self._tome = tome
			self._tome_available = True
		except ImportError:
			self._tome_available = False
			raise ImportError(
				"tome not installed. Install with: pip install tomesd"
			)
		
		# Try to import timm to check availability
		try:
			import timm
			self._timm = timm
			self._timm_available = True
		except ImportError:
			self._timm_available = False
	
	def apply_patch(
		self,
		model: torch.nn.Module,
		r: int = 16,
		use_timm: bool = True
	) -> torch.nn.Module:
		"""Patch a Vision Transformer model with ToMe for token merging.
		
		Args:
			model: Vision Transformer model to patch (timm model or compatible ViT/DeiT)
			r: Number of tokens reduced per layer. Higher values merge more tokens.
				Default: 16. See paper for details on optimal values.
			use_timm: Whether to use timm-specific patching. Default: True.
				Set to False if using a custom ViT model.
		
		Returns:
			The patched model (modified in-place)
		
		Raises:
			ImportError: If tome is not installed
			RuntimeError: If patching fails
		
		Example:
			>>> import timm
			>>> from model_opt.techniques.pruning.pruning_vit_tome import ViTToMePruner
			>>> 
			>>> # Load a pretrained model, can be any vit / deit model
			>>> model = timm.create_model("vit_base_patch16_224", pretrained=True)
			>>> 
			>>> # Patch the model with ToMe
			>>> pruner = ViTToMePruner()
			>>> model = pruner.apply_patch(model, r=16)
			>>> 
			>>> # Or use the prune method
			>>> model = pruner.prune(model, r=16)
		"""
		if not self._tome_available:
			raise ImportError(
				"tome not installed. Install with: pip install tomesd"
			)
		
		if r <= 0:
			raise ValueError(f"r (tokens reduced per layer) must be positive, got {r}")
		
		try:
			if use_timm and self._timm_available:
				# Use timm-specific patching
				self._tome.patch.timm(model)
			else:
				# Use generic ViT patching
				self._tome.patch.vit(model)
			
			# Set the number of tokens reduced per layer
			model.r = r
			
			return model
		except Exception as e:
			raise RuntimeError(f"ToMe ViT patching failed: {e}") from e
	
	def remove_patch(self, model: torch.nn.Module) -> torch.nn.Module:
		"""Remove ToMe patches from a Vision Transformer model.
		
		Args:
			model: Vision Transformer model to remove patches from
		
		Returns:
			The model with patches removed (modified in-place)
		
		Raises:
			ImportError: If tome is not installed
			RuntimeError: If patch removal fails
		"""
		if not self._tome_available:
			raise ImportError(
				"tome not installed. Install with: pip install tomesd"
			)
		
		try:
			# Remove ToMe patches
			if hasattr(model, 'r'):
				model.r = 0
			
			# Try to use tome's remove functionality if available
			if hasattr(self._tome.patch, 'remove'):
				self._tome.patch.remove(model)
			
			return model
		except Exception as e:
			raise RuntimeError(f"ToMe ViT patch removal failed: {e}") from e
	
	def prune(
		self,
		model: torch.nn.Module,
		r: int = 16,
		use_timm: bool = True
	) -> torch.nn.Module:
		"""Apply ToMe token merging to Vision Transformer model (convenience method).
		
		This is an alias for apply_patch() to maintain consistency with other
		pruning interfaces.
		
		Args:
			model: Vision Transformer model to prune
			r: Number of tokens reduced per layer. Default: 16
			use_timm: Whether to use timm-specific patching. Default: True
		
		Returns:
			The pruned model (modified in-place)
		"""
		return self.apply_patch(model, r=r, use_timm=use_timm)
	
	def create_timm_model(
		self,
		model_name: str = "vit_base_patch16_224",
		pretrained: bool = True,
		r: int = 16
	) -> torch.nn.Module:
		"""Create and patch a timm Vision Transformer model with ToMe.
		
		Convenience method to create a timm model and apply ToMe in one step.
		
		Args:
			model_name: Name of timm model to create (e.g., "vit_base_patch16_224")
			pretrained: Whether to load pretrained weights. Default: True
			r: Number of tokens reduced per layer. Default: 16
		
		Returns:
			The patched model with ToMe applied
		
		Raises:
			ImportError: If timm or tome is not installed
			RuntimeError: If model creation or patching fails
		"""
		if not self._timm_available:
			raise ImportError(
				"timm not installed. Install with: pip install timm"
			)
		
		if not self._tome_available:
			raise ImportError(
				"tome not installed. Install with: pip install tomesd"
			)
		
		try:
			# Create the model
			model = self._timm.create_model(model_name, pretrained=pretrained)
			
			# Apply ToMe patch
			return self.apply_patch(model, r=r, use_timm=True)
		except Exception as e:
			raise RuntimeError(f"Failed to create and patch timm model: {e}") from e
	
	def estimate_speedup(self, r: int, num_tokens: int = 197) -> float:
		"""Estimate speedup factor based on tokens reduced per layer.
		
		This is a rough estimate. Actual speedup depends on model architecture,
		hardware, input size, and other factors.
		
		Args:
			r: Number of tokens reduced per layer
			num_tokens: Total number of tokens per layer (default: 197 for ViT-B/16)
		
		Returns:
			Estimated speedup factor (e.g., 1.5 means 1.5x faster)
		"""
		if r <= 0:
			return 1.0
		
		if r >= num_tokens:
			return float('inf')  # Theoretical maximum
		
		# Rough approximation: speedup scales with reduction in token count
		# This is simplified and actual results vary by layer depth and model
		reduction_ratio = r / num_tokens
		
		# Empirical approximation - higher reduction provides more speedup
		# but with diminishing returns due to overhead
		speedup = 1.0 / (1.0 - reduction_ratio * 0.7)  # Conservative estimate
		return min(speedup, 2.5)  # Cap at reasonable maximum
	
	def get_supported_models(self) -> list:
		"""Get list of supported timm model names (Vision Transformers).
		
		Returns:
			List of common ViT/DeiT model names that work with ToMe
		"""
		return [
			"vit_base_patch16_224",
			"vit_base_patch16_384",
			"vit_base_patch32_224",
			"vit_large_patch16_224",
			"vit_large_patch16_384",
			"vit_small_patch16_224",
			"vit_tiny_patch16_224",
			"deit_base_patch16_224",
			"deit_small_patch16_224",
			"deit_tiny_patch16_224",
		]

