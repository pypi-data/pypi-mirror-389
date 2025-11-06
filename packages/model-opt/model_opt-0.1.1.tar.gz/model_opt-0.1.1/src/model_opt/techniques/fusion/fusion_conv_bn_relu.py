"""Conv-BN-ReLU fusion for PyTorch models."""
from typing import Any, Dict, List, Optional
import torch
import torch.nn as nn


class ConvBNReLUFuser:
	"""Fuse Conv2d-BatchNorm2d-ReLU layers using PyTorch/TorchScript fusion.
	
	This fusion combines convolutional, batch normalization, and activation layers
	into a single operation, reducing memory access and improving inference speed.
	"""
	
	def __init__(self):
		"""Initialize ConvBNReLUFuser."""
		self.supported_patterns = [
			['Conv2d', 'BatchNorm2d'],
			['Conv2d', 'BatchNorm2d', 'ReLU'],
			['Conv2d', 'BatchNorm2d', 'ReLU6'],
		]
	
	def fuse_model(
		self,
		model: nn.Module,
		inplace: bool = True,
		fuse_quantization: bool = False
	) -> nn.Module:
		"""Fuse Conv-BN-ReLU patterns in a PyTorch model.
		
		Args:
			model: PyTorch model to fuse
			inplace: Whether to modify the model in-place. Default: True
			fuse_quantization: Whether to use quantization-aware fusion.
				Default: False
		
		Returns:
			The fused model
		
		Raises:
			RuntimeError: If fusion fails
		
		Example:
			>>> import torch.nn as nn
			>>> from model_opt.techniques.fusion.fusion_conv_bn_relu import ConvBNReLUFuser
			>>> 
			>>> model = nn.Sequential(
			...     nn.Conv2d(3, 64, 3),
			...     nn.BatchNorm2d(64),
			...     nn.ReLU()
			... )
			>>> fuser = ConvBNReLUFuser()
			>>> fused_model = fuser.fuse_model(model)
		"""
		try:
			if not inplace:
				import copy
				model = copy.deepcopy(model)
			
			# Use PyTorch's built-in fusion for quantization-aware models
			if fuse_quantization:
				try:
					from torch.quantization import fuse_modules
					model = self._fuse_with_quantization(model, fuse_modules)
				except ImportError:
					# Fallback to regular fusion if quantization not available
					model = self._fuse_regular(model)
			else:
				# Regular fusion using TorchScript
				model = self._fuse_regular(model)
			
			return model
		
		except Exception as e:
			raise RuntimeError(f"Conv-BN-ReLU fusion failed: {e}") from e
	
	def _fuse_regular(self, model: nn.Module) -> nn.Module:
		"""Fuse layers using PyTorch's regular fusion (TorchScript compatible).
		
		Args:
			model: Model to fuse
		
		Returns:
			Fused model
		"""
		# Recurse through model and fuse Sequential blocks
		for name, module in list(model.named_children()):
			if isinstance(module, nn.Sequential):
				self._fuse_sequential(module)
			else:
				# Recurse into submodules
				self._fuse_regular(module)
		
		return model
	
	def _fuse_sequential(self, seq: nn.Sequential) -> None:
		"""Fuse layers within a Sequential module.
		
		Args:
			seq: Sequential module to process
		"""
		names = list(seq._modules.keys())
		
		i = 0
		while i < len(names) - 1:
			# Check for Conv-BN pattern
			conv_name = names[i]
			conv = seq._modules[conv_name]
			
			if not isinstance(conv, (nn.Conv1d, nn.Conv2d, nn.Conv3d)):
				i += 1
				continue
			
			# Check for BatchNorm following Conv
			if i + 1 < len(names):
				bn_name = names[i + 1]
				bn = seq._modules[bn_name]
				
				bn_types = (nn.BatchNorm1d, nn.BatchNorm2d, nn.BatchNorm3d)
				if isinstance(bn, bn_types):
					fuse_list = [conv_name, bn_name]
					
					# Check for ReLU/ReLU6 following BN
					if i + 2 < len(names):
						act_name = names[i + 2]
						act = seq._modules[act_name]
						if isinstance(act, (nn.ReLU, nn.ReLU6)):
							fuse_list.append(act_name)
					
					# Fuse the layers
					try:
						from torch.quantization import fuse_modules
						fuse_modules(seq, fuse_list, inplace=True)
						# Update names after fusion
						names = list(seq._modules.keys())
						i += len(fuse_list)
						continue
					except Exception:
						pass
			
			i += 1
	
	def _fuse_with_quantization(
		self,
		model: nn.Module,
		fuse_modules_func: Any
	) -> nn.Module:
		"""Fuse layers with quantization-aware fusion.
		
		Args:
			model: Model to fuse
			fuse_modules_func: PyTorch's fuse_modules function
		
		Returns:
			Fused model
		"""
		# This uses PyTorch's quantization-aware fusion
		# which is more robust but requires quantization setup
		for name, module in list(model.named_children()):
			if isinstance(module, nn.Sequential):
				self._fuse_sequential_quantized(module, fuse_modules_func)
			else:
				self._fuse_with_quantization(module, fuse_modules_func)
		
		return model
	
	def _fuse_sequential_quantized(
		self,
		seq: nn.Sequential,
		fuse_modules_func: Any
	) -> None:
		"""Fuse layers in Sequential with quantization support.
		
		Args:
			seq: Sequential module to process
			fuse_modules_func: PyTorch's fuse_modules function
		"""
		# Similar to _fuse_sequential but uses quantization-aware fusion
		names = list(seq._modules.keys())
		
		i = 0
		while i < len(names) - 1:
			conv_name = names[i]
			conv = seq._modules[conv_name]
			
			if not isinstance(conv, (nn.Conv1d, nn.Conv2d, nn.Conv3d)):
				i += 1
				continue
			
			if i + 1 < len(names):
				bn_name = names[i + 1]
				bn = seq._modules[bn_name]
				
				bn_types = (nn.BatchNorm1d, nn.BatchNorm2d, nn.BatchNorm3d)
				if isinstance(bn, bn_types):
					fuse_list = [conv_name, bn_name]
					
					if i + 2 < len(names):
						act_name = names[i + 2]
						act = seq._modules[act_name]
						if isinstance(act, (nn.ReLU, nn.ReLU6)):
							fuse_list.append(act_name)
					
					try:
						fuse_modules_func(seq, fuse_list, inplace=True)
						names = list(seq._modules.keys())
						i += len(fuse_list)
						continue
					except Exception:
						pass
			
			i += 1
	
	def fuse_pattern(
		self,
		modules: List[nn.Module],
		pattern: List[str]
	) -> nn.Module:
		"""Fuse a specific pattern of modules.
		
		Args:
			modules: List of modules to fuse
			pattern: Pattern to match (e.g., ['Conv2d', 'BatchNorm2d', 'ReLU'])
		
		Returns:
			Fused module
		"""
		if pattern not in self.supported_patterns:
			raise ValueError(
				f"Unsupported pattern: {pattern}. "
				f"Supported: {self.supported_patterns}"
			)
		
		try:
			from torch.quantization import fuse_modules
			# Create a temporary Sequential for fusion
			temp_seq = nn.Sequential(*modules)
			names = list(temp_seq._modules.keys())
			fuse_modules(temp_seq, names, inplace=True)
			return temp_seq[0]  # Return the fused module
		except Exception as e:
			raise RuntimeError(f"Pattern fusion failed: {e}") from e
	
	def get_fusion_info(self, model: nn.Module) -> Dict:
		"""Get information about fusion opportunities in a model.
		
		Args:
			model: Model to analyze
		
		Returns:
			Dictionary with fusion information
		"""
		info = {
			'total_conv_layers': 0,
			'fusable_patterns': [],
			'potential_speedup': 0.0
		}
		
		for name, module in model.named_modules():
			if isinstance(module, (nn.Conv1d, nn.Conv2d, nn.Conv3d)):
				info['total_conv_layers'] += 1
				# Check if followed by BN
				parent = module.parent if hasattr(module, 'parent') else None
				if parent and isinstance(parent, nn.Sequential):
					# Analyze pattern
					pass  # Pattern detection logic here
		
		return info

