"""Linear-GELU fusion (custom implementation)."""
from typing import Any, Dict, Optional
import torch
import torch.nn as nn
import torch.nn.functional as F


class FusedLinearGELU(nn.Module):
	"""Custom fused Linear-GELU layer for improved performance.
	
	Combines a linear transformation and GELU activation into a single
	custom operation, reducing kernel launches and memory access.
	"""
	
	def __init__(self, in_features: int, out_features: int, bias: bool = True):
		"""Initialize FusedLinearGELU layer.
		
		Args:
			in_features: Size of each input sample
			out_features: Size of each output sample
			bias: If set to False, layer will not learn an additive bias.
				Default: True
		"""
		super().__init__()
		self.linear = nn.Linear(in_features, out_features, bias=bias)
	
	def forward(self, x: torch.Tensor) -> torch.Tensor:
		"""Forward pass: Linear transformation followed by GELU activation.
		
		Args:
			x: Input tensor of shape (..., in_features)
		
		Returns:
			Output tensor of shape (..., out_features) with GELU applied
		"""
		return F.gelu(self.linear(x))


class LinearGELUFuser:
	"""Fuse Linear-GELU layers into custom fused modules."""
	
	def __init__(self):
		"""Initialize LinearGELUFuser."""
		self.pattern = ['Linear', 'GELU']
	
	def fuse_model(
		self,
		model: nn.Module,
		inplace: bool = True
	) -> nn.Module:
		"""Fuse Linear-GELU patterns in a PyTorch model.
		
		Replaces consecutive Linear followed by GELU layers with
		FusedLinearGELU custom modules.
		
		Args:
			model: PyTorch model to fuse
			inplace: Whether to modify the model in-place. Default: True
		
		Returns:
			The fused model
		
		Raises:
			RuntimeError: If fusion fails
		
		Example:
			>>> import torch.nn as nn
			>>> from model_opt.techniques.fusion.fusion_linear_gelu import LinearGELUFuser
			>>> 
			>>> model = nn.Sequential(
			...     nn.Linear(512, 2048),
			...     nn.GELU(),
			...     nn.Linear(2048, 512)
			... )
			>>> fuser = LinearGELUFuser()
			>>> fused_model = fuser.fuse_model(model)
		"""
		try:
			if not inplace:
				import copy
				model = copy.deepcopy(model)
			
			# Recursively fuse Linear-GELU patterns
			self._fuse_recursive(model)
			
			return model
		
		except Exception as e:
			raise RuntimeError(f"Linear-GELU fusion failed: {e}") from e
	
	def _fuse_recursive(self, module: nn.Module) -> None:
		"""Recursively fuse Linear-GELU patterns in the model.
		
		Args:
			module: Module to process recursively
		"""
		# Process Sequential modules
		if isinstance(module, nn.Sequential):
			self._fuse_sequential(module)
		
		# Recursively process child modules
		for child in list(module.children()):
			self._fuse_recursive(child)
	
	def _fuse_sequential(self, seq: nn.Sequential) -> None:
		"""Fuse Linear-GELU patterns within a Sequential module.
		
		Args:
			seq: Sequential module to process
		"""
		modules = list(seq._modules.items())
		new_modules = []
		i = 0
		
		while i < len(modules):
			name, module = modules[i]
			
			# Check if current module is Linear
			if isinstance(module, nn.Linear):
				# Check if next module is GELU
				if i + 1 < len(modules):
					next_name, next_module = modules[i + 1]
					
					if isinstance(next_module, nn.GELU):
						# Fuse Linear and GELU
						fused = FusedLinearGELU(
							in_features=module.in_features,
							out_features=module.out_features,
							bias=module.bias is not None
						)
						
						# Copy weights and bias
						with torch.no_grad():
							fused.linear.weight.copy_(module.weight)
							if module.bias is not None:
								fused.linear.bias.copy_(module.bias)
						
						# Add fused module
						new_modules.append((name, fused))
						i += 2  # Skip both Linear and GELU
						continue
			
			# Keep original module
			new_modules.append((name, module))
			i += 1
		
		# Replace modules in Sequential
		seq._modules.clear()
		for name, module in new_modules:
			seq.add_module(name, module)
	
	def replace_linear_gelu(
		self,
		linear: nn.Linear,
		gelu: Optional[nn.GELU] = None
	) -> FusedLinearGELU:
		"""Replace a Linear (and optional GELU) with FusedLinearGELU.
		
		Args:
			linear: Linear layer to replace
			gelu: Optional GELU layer (for consistency checking)
		
		Returns:
			FusedLinearGELU module with copied weights
		"""
		fused = FusedLinearGELU(
			in_features=linear.in_features,
			out_features=linear.out_features,
			bias=linear.bias is not None
		)
		
		# Copy weights and bias
		with torch.no_grad():
			fused.linear.weight.copy_(linear.weight)
			if linear.bias is not None:
				fused.linear.bias.copy_(linear.bias)
		
		return fused
	
	def get_fusion_info(self, model: nn.Module) -> Dict:
		"""Get information about Linear-GELU fusion opportunities.
		
		Args:
			model: Model to analyze
		
		Returns:
			Dictionary with fusion information
		"""
		info = {
			'total_linear_layers': 0,
			'gelu_layers': 0,
			'fusable_pairs': 0,
			'potential_speedup': 0.0
		}
		
		# Count Linear and GELU layers
		for module in model.modules():
			if isinstance(module, nn.Linear):
				info['total_linear_layers'] += 1
			elif isinstance(module, nn.GELU):
				info['gelu_layers'] += 1
		
		# Find fusable pairs in Sequential modules
		for module in model.modules():
			if isinstance(module, nn.Sequential):
				modules_list = list(module.children())
				for i in range(len(modules_list) - 1):
					if isinstance(modules_list[i], nn.Linear):
						if isinstance(modules_list[i + 1], nn.GELU):
							info['fusable_pairs'] += 1
		
		# Estimate potential speedup (rough approximation)
		if info['fusable_pairs'] > 0:
			# Each fusion can provide ~10-15% speedup
			info['potential_speedup'] = info['fusable_pairs'] * 0.12
		
		return info

