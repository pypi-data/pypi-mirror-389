"""Quantization utilities - unified interface to quantization backends."""
from typing import Any, Dict, Tuple, Optional
import warnings
import os
import logging

# Suppress TorchAO and PyTorch warnings
os.environ.setdefault('TORCHAO_SUPPRESS_WARNINGS', '1')
os.environ.setdefault('PYTHONWARNINGS', 'ignore')

# Suppress PyTorch logging warnings
logging.getLogger('torch.distributed.elastic.multiprocessing.redirects').setLevel(logging.ERROR)

# Suppress warnings
warnings.filterwarnings('ignore', category=UserWarning, module='torch')
warnings.filterwarnings('ignore', message='.*Skipping import of cpp extensions.*')
warnings.filterwarnings('ignore', message='.*Redirects are currently not supported.*')
warnings.filterwarnings('ignore', message='.*incompatible torch version.*')
warnings.filterwarnings('ignore', message='.*NOTE.*Redirects.*')

# Import quantization implementations
# Note: There's a naming conflict between quantize.py (this module) and quantize/ (directory)
# We need to import from the directory using importlib or a workaround
try:
	import importlib.util
	import sys
	from pathlib import Path
	
	# Suppress warnings during import
	with warnings.catch_warnings():
		warnings.simplefilter("ignore")
		
		# Import from quantize/quantize_torch.py directly
		quantize_torch_path = Path(__file__).parent / 'quantize' / 'quantize_torch.py'
		if quantize_torch_path.exists():
			spec = importlib.util.spec_from_file_location(
				"quantize_torch", 
				quantize_torch_path
			)
			quantize_torch_module = importlib.util.module_from_spec(spec)
			spec.loader.exec_module(quantize_torch_module)
			
			TorchAOQuantizer = quantize_torch_module.TorchAOQuantizer
			quantize_pytorch_torchao = quantize_torch_module.quantize_pytorch_torchao
			autoquant = quantize_torch_module.autoquant
			_TORCHAO_AVAILABLE = True
		else:
			raise ImportError("quantize_torch.py not found")
except (ImportError, AttributeError, Exception):
	_TORCHAO_AVAILABLE = False
	TorchAOQuantizer = None
	quantize_pytorch_torchao = None
	autoquant = None


class Quantizer:
	"""Unified quantization wrapper with multiple backend support.
	
	Supports:
	- TorchAO quantization (weight-only and dynamic)
	- Autoquantization (automatic method selection)
	"""
	
	def __init__(self):
		"""Initialize Quantizer with available backends."""
		self.torchao_quantizer = None
		if _TORCHAO_AVAILABLE and TorchAOQuantizer is not None:
			try:
				self.torchao_quantizer = TorchAOQuantizer()
			except (ImportError, Exception) as e:
				# Silently fail if TorchAO can't be initialized
				# (might be incompatible version or missing dependencies)
				import warnings
				warnings.filterwarnings('ignore')
				pass
	
	def quantize(
		self,
		model: Any,
		method: str = 'int8_weight_only',
		output_path: Optional[str] = None,
		**kwargs
	) -> Tuple[Any, dict]:
		"""Quantize model using TorchAO backend.
		
		Args:
			model: PyTorch model to quantize
			method: Quantization method. Options:
				- 'int8_weight_only': 8-bit integer weight-only quantization
				- 'int8_dynamic': 8-bit integer dynamic activation + weight quantization
				- 'autoquant': Automatic quantization method selection
			output_path: Optional path to save quantized model
			**kwargs: Additional quantization options:
				- For autoquant: example_input, qtensor_class_list, etc.
		
		Returns:
			Tuple of (quantized_model, quantization_info dict)
		"""
		if method == 'autoquant':
			return self._quantize_autoquant(model, output_path=output_path, **kwargs)
		
		if not self.torchao_quantizer:
			raise ImportError("TorchAO not available. Install with: pip install torchao")
		
		quantized_model = self.torchao_quantizer.quantize(model, method=method)
		
		info = {
			"backend": "torchao",
			"method": method,
			"status": "success"
		}
		
		if output_path:
			try:
				import torch
				torch.save(quantized_model, output_path)
			except Exception as e:
				print(f"Warning: Could not save quantized model: {e}")
		
		return quantized_model, info
	
	def _quantize_autoquant(
		self,
		model: Any,
		output_path: Optional[str] = None,
		**kwargs
	) -> Tuple[Any, dict]:
		"""Apply autoquantization to model.
		
		Args:
			model: Model to quantize
			output_path: Optional path to save quantized model
			**kwargs: Autoquantization options
		
		Returns:
			Tuple of (quantized_model, quantization_info dict)
		"""
		if not _TORCHAO_AVAILABLE or autoquant is None:
			raise ImportError("TorchAO autoquant not available. Install with: pip install torchao")
		
		quantized_model = autoquant(model, **kwargs)
		
		info = {
			"backend": "torchao",
			"method": "autoquant",
			"status": "success"
		}
		
		if output_path:
			try:
				import torch
				torch.save(quantized_model, output_path)
			except Exception as e:
				print(f"Warning: Could not save quantized model: {e}")
		
		return quantized_model, info