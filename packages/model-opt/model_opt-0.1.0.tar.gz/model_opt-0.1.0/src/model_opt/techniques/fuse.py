"""Layer fusion utilities - unified interface to fusion backends."""
from typing import Any, Optional

# Import fusion implementations
try:
	from model_opt.techniques.fusion.fusion_conv_bn_relu import ConvBNReLUFuser
	from model_opt.techniques.fusion.fusion_linear_gelu import LinearGELUFuser
	_FUSION_AVAILABLE = True
except ImportError:
	_FUSION_AVAILABLE = False
	ConvBNReLUFuser = None
	LinearGELUFuser = None


class LayerFuser:
	"""Unified layer fusion helper with multiple backend support.
	
	Supports:
	- Conv-BN-ReLU fusion (PyTorch/TorchScript)
	- Linear-GELU fusion (Custom)
	"""
	
	def __init__(self):
		"""Initialize LayerFuser with available fusion backends."""
		self.conv_bn_relu_fuser = None
		self.linear_gelu_fuser = None
		
		if _FUSION_AVAILABLE:
			try:
				if ConvBNReLUFuser is not None:
					self.conv_bn_relu_fuser = ConvBNReLUFuser()
				if LinearGELUFuser is not None:
					self.linear_gelu_fuser = LinearGELUFuser()
			except Exception:
				pass
	
	def fuse_model(
		self,
		model: Any,
		framework: str = 'pytorch',
		fusion_types: Optional[list] = None,
		**kwargs
	) -> Any:
		"""Fuse layers in a model using available fusion backends.
		
		Args:
			model: Model to fuse
			framework: Framework name ('pytorch' only currently). Default: 'pytorch'
			fusion_types: List of fusion types to apply. Options:
				- 'conv_bn_relu': Conv-BN-ReLU fusion
				- 'linear_gelu': Linear-GELU fusion
				If None, applies all available fusions. Default: None
			**kwargs: Additional fusion options:
				- fuse_quantization: For Conv-BN-ReLU, use quantization-aware fusion
		
		Returns:
			The fused model
		
		Raises:
			ValueError: If framework is not supported
			RuntimeError: If fusion fails
		"""
		if framework != 'pytorch':
			raise ValueError(f"Layer fusion currently supports 'pytorch' only, got: {framework}")
		
		if fusion_types is None:
			fusion_types = ['conv_bn_relu', 'linear_gelu']
		
		current_model = model
		
		# Apply Conv-BN-ReLU fusion
		if 'conv_bn_relu' in fusion_types:
			if self.conv_bn_relu_fuser:
				fuse_quantization = kwargs.get('fuse_quantization', False)
				current_model = self.conv_bn_relu_fuser.fuse_model(
					current_model,
					fuse_quantization=fuse_quantization
				)
		
		# Apply Linear-GELU fusion
		if 'linear_gelu' in fusion_types:
			if self.linear_gelu_fuser:
				current_model = self.linear_gelu_fuser.fuse_model(current_model)
		
		return current_model
	
	def fuse_conv_bn_relu(
		self,
		model: Any,
		fuse_quantization: bool = False
	) -> Any:
		"""Fuse Conv-BN-ReLU patterns in a model.
		
		Args:
			model: Model to fuse
			fuse_quantization: Use quantization-aware fusion. Default: False
		
		Returns:
			The fused model
		"""
		if not self.conv_bn_relu_fuser:
			raise RuntimeError("Conv-BN-ReLU fusion not available")
		return self.conv_bn_relu_fuser.fuse_model(model, fuse_quantization=fuse_quantization)
	
	def fuse_linear_gelu(self, model: Any) -> Any:
		"""Fuse Linear-GELU patterns in a model.
		
		Args:
			model: Model to fuse
		
		Returns:
			The fused model
		"""
		if not self.linear_gelu_fuser:
			raise RuntimeError("Linear-GELU fusion not available")
		return self.linear_gelu_fuser.fuse_model(model)


