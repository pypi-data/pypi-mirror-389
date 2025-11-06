"""Model pruning utilities - unified interface to pruning backends."""
from typing import Any, Dict, Iterable, Optional

# Import pruning implementations
try:
	from model_opt.techniques.pruning.pruning_torch import StructuredPruner
	_TORCH_PRUNING_AVAILABLE = True
except ImportError:
	_TORCH_PRUNING_AVAILABLE = False
	StructuredPruner = None

try:
	from model_opt.techniques.pruning.pruning_unstructured_torch import UnstructuredPruner
	_UNSTRUCTURED_PRUNING_AVAILABLE = True
except ImportError:
	_UNSTRUCTURED_PRUNING_AVAILABLE = False
	UnstructuredPruner = None

try:
	from model_opt.techniques.pruning.pruning_sd import StableDiffusionPruner
	_SD_PRUNING_AVAILABLE = True
except ImportError:
	_SD_PRUNING_AVAILABLE = False
	StableDiffusionPruner = None

try:
	from model_opt.techniques.pruning.pruning_vit_tome import ViTToMePruner
	_VIT_PRUNING_AVAILABLE = True
except ImportError:
	_VIT_PRUNING_AVAILABLE = False
	ViTToMePruner = None


class Pruner:
	"""Unified model pruner with multiple backend support.
	
	Supports:
	- Structured pruning (torch-pruning)
	- Unstructured pruning (PyTorch native)
	- Stable Diffusion pruning (ToMe)
	- Vision Transformer pruning (ToMe)
	"""
	
	def __init__(self):
		"""Initialize Pruner with available backends."""
		self.structured_pruner = None
		self.unstructured_pruner = None
		self.sd_pruner = None
		self.vit_pruner = None
		
		if _TORCH_PRUNING_AVAILABLE and StructuredPruner is not None:
			try:
				self.structured_pruner = StructuredPruner()
			except ImportError:
				pass
		
		if _UNSTRUCTURED_PRUNING_AVAILABLE and UnstructuredPruner is not None:
			try:
				self.unstructured_pruner = UnstructuredPruner()
			except ImportError:
				pass
		
		if _SD_PRUNING_AVAILABLE and StableDiffusionPruner is not None:
			try:
				self.sd_pruner = StableDiffusionPruner()
			except ImportError:
				pass
		
		if _VIT_PRUNING_AVAILABLE and ViTToMePruner is not None:
			try:
				self.vit_pruner = ViTToMePruner()
			except ImportError:
				pass
	
	def prune_model(
		self,
		model: Any,
		amount: float = 0.5,
		criterion: str = 'l1',
		prune_type: str = 'unstructured',
		**kwargs
	) -> Any:
		"""Prune model using specified backend.
		
		Args:
			model: Model to prune
			amount: Fraction to prune (0.0 to 1.0). Default: 0.5
			criterion: Pruning criterion. Options depend on prune_type:
				- For unstructured: 'l1', 'l2', 'random'
				- For structured: 'magnitude', 'taylor', 'group_norm'
				Default: 'l1'
			prune_type: Type of pruning. Options:
				- 'unstructured': Unstructured pruning (local or global)
				- 'structured': Structured pruning (requires example_input)
				- 'sd': Stable Diffusion token merging
				- 'vit': Vision Transformer token merging
				Default: 'unstructured'
			**kwargs: Additional pruning options:
				- example_input: For structured pruning, example input tensor
				- importance: For structured pruning, importance metric
				- ratio: For SD/ViT pruning, token merging ratio
		
		Returns:
			The pruned model
		
		Raises:
			ValueError: If prune_type is not supported
			RuntimeError: If pruning fails
		"""
		if prune_type == 'unstructured':
			if not self.unstructured_pruner:
				# Fallback to basic unstructured pruning
				return self._prune_basic_unstructured(model, amount, criterion)
			
			pruning_scope = kwargs.get('pruning_scope', 'local')  # 'local' or 'global'
			if pruning_scope == 'local':
				return self.unstructured_pruner.prune_local(
					model, amount=amount, criterion=criterion, **kwargs
				)
			else:
				return self.unstructured_pruner.prune_global(
					model, amount=amount, criterion=criterion, **kwargs
				)
		
		elif prune_type == 'structured':
			if not self.structured_pruner:
				raise RuntimeError("Structured pruning not available. Install torch-pruning")
			
			example_input = kwargs.get('example_input')
			if example_input is None:
				raise ValueError("structured pruning requires example_input in kwargs")
			
			importance = kwargs.get('importance', criterion if criterion in ['magnitude', 'taylor', 'group_norm'] else 'magnitude')
			return self.structured_pruner.prune(
				model, example_input, pruning_ratio=amount, importance=importance
			)
		
		elif prune_type == 'sd':
			if not self.sd_pruner:
				raise RuntimeError("Stable Diffusion pruning not available. Install tomesd")
			
			ratio = kwargs.get('ratio', amount)
			return self.sd_pruner.apply_patch(model, ratio=ratio, **kwargs)
		
		elif prune_type == 'vit':
			if not self.vit_pruner:
				raise RuntimeError("ViT pruning not available. Install tomesd")
			
			r = kwargs.get('r', int(amount * 16))  # Convert ratio to token count
			return self.vit_pruner.apply_patch(model, r=r, **kwargs)
		
		else:
			raise ValueError(f"Unsupported prune_type: {prune_type}")
	
	@staticmethod
	def _prune_basic_unstructured(
		model: Any,
		amount: float = 0.5,
		criterion: str = 'l1'
	) -> Any:
		"""Basic unstructured pruning fallback (legacy method).
		
		Args:
			model: Model to prune
			amount: Fraction to prune
			criterion: Pruning criterion
		
		Returns:
			The pruned model
		"""
		try:
			import torch
			import torch.nn as nn
			from torch.nn.utils import prune as nnprune
		except Exception as e:
			raise RuntimeError(f"PyTorch pruning unavailable: {e}")

		if amount <= 0:
			return model

		modules: Iterable[tuple[str, nn.Module]] = model.named_modules()
		for name, module in modules:
			if isinstance(module, (nn.Conv2d, nn.Linear)):
				try:
					if criterion.lower() == 'l1':
						nnprune.l1_unstructured(module, name='weight', amount=amount)
					else:
						nnprune.l1_unstructured(module, name='weight', amount=amount)
				except Exception:
					continue

		# Make pruning permanent
		for name, module in model.named_modules():
			if hasattr(module, 'weight_mask'):
				try:
					nnprune.remove(module, 'weight')
				except Exception:
					pass

		return model


