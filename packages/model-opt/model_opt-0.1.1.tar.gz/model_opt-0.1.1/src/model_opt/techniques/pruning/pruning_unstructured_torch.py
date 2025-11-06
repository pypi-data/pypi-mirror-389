"""PyTorch unstructured pruning utilities."""
from typing import Any, Dict, List, Optional, Tuple, Iterable
import torch
import torch.nn as nn
from torch.nn.utils import prune as nnprune


class UnstructuredPruner:
	"""Unstructured pruning using PyTorch's built-in pruning utilities.
	
	Supports both local (per-layer) and global (across-layers) unstructured pruning
	using L1, L2, or random pruning criteria.
	"""
	
	def __init__(self):
		"""Initialize UnstructuredPruner."""
		# Supported pruning criteria
		self.supported_criteria = ['l1', 'l2', 'random']
		
		# Supported pruning types
		self.supported_types = ['local', 'global']
	
	def prune_local(
		self,
		model: nn.Module,
		amount: float = 0.5,
		criterion: str = 'l1',
		parameter_name: str = 'weight',
		modules: Optional[List[Tuple[str, nn.Module]]] = None,
		make_permanent: bool = True
	) -> nn.Module:
		"""Apply local (per-layer) unstructured pruning.
		
		Prunes each layer independently by removing the specified fraction of parameters
		from each layer based on the chosen criterion.
		
		Args:
			model: PyTorch model to prune
			amount: Fraction of parameters to prune in each layer (0.0 to 1.0)
			criterion: Pruning criterion. Options:
				- 'l1': L1 norm (magnitude-based)
				- 'l2': L2 norm (magnitude-based)
				- 'random': Random pruning
			parameter_name: Name of parameter to prune (default: 'weight')
			modules: Optional list of (name, module) tuples to prune. If None,
				prunes all Conv2d and Linear layers.
			make_permanent: If True, removes pruning reparametrization to make
				pruning permanent. Defaults to True.
		
		Returns:
			The pruned model (modified in-place)
		
		Raises:
			ValueError: If criterion is not supported or amount is invalid
			RuntimeError: If pruning fails
		"""
		if amount <= 0 or amount >= 1:
			raise ValueError(f"Amount must be between 0 and 1, got {amount}")
		
		if criterion.lower() not in self.supported_criteria:
			raise ValueError(
				f"Unsupported criterion: {criterion}. "
				f"Supported criteria: {self.supported_criteria}"
			)
		
		try:
			# Get modules to prune
			if modules is None:
				modules = [
					(name, module) for name, module in model.named_modules()
					if isinstance(module, (nn.Conv2d, nn.Linear))
				]
			
			# Apply local pruning to each module
			for name, module in modules:
				if not hasattr(module, parameter_name):
					continue
				
				param = getattr(module, parameter_name)
				if param is None:
					continue
				
				try:
					if criterion.lower() == 'l1':
						nnprune.l1_unstructured(
							module, name=parameter_name, amount=amount
						)
					elif criterion.lower() == 'l2':
						nnprune.ln_unstructured(
							module, name=parameter_name, amount=amount, n=2
						)
					elif criterion.lower() == 'random':
						nnprune.random_unstructured(
							module, name=parameter_name, amount=amount
						)
				except Exception as e:
					# Skip modules that fail to prune
					continue
			
			# Make pruning permanent if requested
			if make_permanent:
				self._make_pruning_permanent(model, parameter_name)
			
			return model
		
		except Exception as e:
			raise RuntimeError(f"Local unstructured pruning failed: {e}") from e
	
	def prune_global(
		self,
		model: nn.Module,
		amount: float = 0.5,
		criterion: str = 'l1',
		parameter_name: str = 'weight',
		modules: Optional[List[Tuple[str, nn.Module]]] = None,
		make_permanent: bool = True
	) -> nn.Module:
		"""Apply global (across-layers) unstructured pruning.
		
		Prunes parameters globally across all specified layers, removing the specified
		fraction of parameters from the entire model based on the chosen criterion.
		
		Args:
			model: PyTorch model to prune
			amount: Fraction of parameters to prune globally (0.0 to 1.0)
			criterion: Pruning criterion. Options:
				- 'l1': L1 norm (magnitude-based)
				- 'l2': L2 norm (magnitude-based)
				- 'random': Random pruning
			parameter_name: Name of parameter to prune (default: 'weight')
			modules: Optional list of (name, module) tuples to prune. If None,
				prunes all Conv2d and Linear layers.
			make_permanent: If True, removes pruning reparametrization to make
				pruning permanent. Defaults to True.
		
		Returns:
			The pruned model (modified in-place)
		
		Raises:
			ValueError: If criterion is not supported or amount is invalid
			RuntimeError: If pruning fails
		"""
		if amount <= 0 or amount >= 1:
			raise ValueError(f"Amount must be between 0 and 1, got {amount}")
		
		if criterion.lower() not in self.supported_criteria:
			raise ValueError(
				f"Unsupported criterion: {criterion}. "
				f"Supported criteria: {self.supported_criteria}"
			)
		
		try:
			# Get modules to prune
			if modules is None:
				modules = [
					(name, module) for name, module in model.named_modules()
					if isinstance(module, (nn.Conv2d, nn.Linear))
				]
			
			# Prepare parameters for global pruning
			parameters_to_prune = []
			for name, module in modules:
				if hasattr(module, parameter_name):
					param = getattr(module, parameter_name)
					if param is not None:
						parameters_to_prune.append((module, parameter_name))
			
			if not parameters_to_prune:
				return model
			
			# Apply global pruning
			if criterion.lower() == 'l1':
				nnprune.global_unstructured(
					parameters_to_prune,
					pruning_method=nnprune.L1Unstructured,
					amount=amount
				)
			elif criterion.lower() == 'l2':
				nnprune.global_unstructured(
					parameters_to_prune,
					pruning_method=nnprune.LnUnstructured,
					amount=amount,
					n=2
				)
			elif criterion.lower() == 'random':
				nnprune.global_unstructured(
					parameters_to_prune,
					pruning_method=nnprune.RandomUnstructured,
					amount=amount
				)
			
			# Make pruning permanent if requested
			if make_permanent:
				self._make_pruning_permanent(model, parameter_name)
			
			return model
		
		except Exception as e:
			raise RuntimeError(f"Global unstructured pruning failed: {e}") from e
	
	def prune(
		self,
		model: nn.Module,
		amount: float = 0.5,
		criterion: str = 'l1',
		prune_type: str = 'local',
		parameter_name: str = 'weight',
		modules: Optional[List[Tuple[str, nn.Module]]] = None,
		make_permanent: bool = True
	) -> nn.Module:
		"""Apply unstructured pruning (convenience method).
		
		Args:
			model: PyTorch model to prune
			amount: Fraction of parameters to prune (0.0 to 1.0)
			criterion: Pruning criterion ('l1', 'l2', 'random')
			prune_type: Type of pruning ('local' or 'global')
			parameter_name: Name of parameter to prune (default: 'weight')
			modules: Optional list of (name, module) tuples to prune
			make_permanent: If True, makes pruning permanent
	
		Returns:
			The pruned model (modified in-place)
		"""
		if prune_type.lower() not in self.supported_types:
			raise ValueError(
				f"Unsupported prune_type: {prune_type}. "
				f"Supported types: {self.supported_types}"
			)
		
		if prune_type.lower() == 'local':
			return self.prune_local(
				model, amount, criterion, parameter_name, modules, make_permanent
			)
		else:
			return self.prune_global(
				model, amount, criterion, parameter_name, modules, make_permanent
			)
	
	def _make_pruning_permanent(
		self,
		model: nn.Module,
		parameter_name: str = 'weight'
	) -> None:
		"""Remove pruning reparametrization to make pruning permanent.
		
		Args:
			model: Model to process
			parameter_name: Name of parameter to process
		"""
		for name, module in model.named_modules():
			if hasattr(module, f'{parameter_name}_mask'):
				try:
					nnprune.remove(module, parameter_name)
				except Exception:
					pass
	
	def get_pruning_info(self, model: nn.Module, parameter_name: str = 'weight') -> Dict:
		"""Get information about current pruning state.
		
		Args:
			model: Model to inspect
			parameter_name: Name of parameter to inspect
		
		Returns:
			Dictionary with pruning information
		"""
		info = {
			'total_modules': 0,
			'pruned_modules': 0,
			'total_parameters': 0,
			'pruned_parameters': 0,
			'pruning_ratio': 0.0
		}
		
		for name, module in model.named_modules():
			if hasattr(module, parameter_name):
				param = getattr(module, parameter_name)
				if param is not None:
					info['total_modules'] += 1
					total_params = param.numel()
					info['total_parameters'] += total_params
					
					# Check if module is pruned
					if hasattr(module, f'{parameter_name}_mask'):
						info['pruned_modules'] += 1
						mask = getattr(module, f'{parameter_name}_mask')
						pruned_params = (mask == 0).sum().item()
						info['pruned_parameters'] += pruned_params
		
		if info['total_parameters'] > 0:
			info['pruning_ratio'] = info['pruned_parameters'] / info['total_parameters']
		
		return info

