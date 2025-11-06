"""TorchAO quantization wrappers (PyTorch)."""
from typing import Any, Dict, Tuple, Optional, List, Callable
import warnings
import os
import sys
import contextlib
import logging

# Suppress TorchAO and PyTorch warnings at import time
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

# Import torch after setting up warning suppression
import torch

# Context manager to suppress stderr during imports
@contextlib.contextmanager
def suppress_stderr():
	"""Temporarily suppress stderr output."""
	with open(os.devnull, 'w') as devnull:
		old_stderr = sys.stderr
		try:
			sys.stderr = devnull
			yield
		finally:
			sys.stderr = old_stderr


def quantize_pytorch_torchao(model: Any, **kwargs) -> Tuple[Any, Dict]:
	"""Quantize a PyTorch model via TorchAO.
	
	This function applies quantization to a PyTorch model using TorchAO's quantization
	APIs. It supports multiple quantization types including weight-only and dynamic
	activation + weight quantization.
	
	Args:
		model: PyTorch model to quantize
		**kwargs: Additional options:
			- quant_type (str): Type of quantization to apply. Options:
				- 'int4_weight_only': 4-bit integer weight-only quantization
				- 'int8_weight_only': 8-bit integer weight-only quantization
				- 'float8_weight_only': 8-bit float weight-only quantization
				- 'float8_dynamic': Float8 dynamic activation + weight quantization (default)
				- 'int8_dynamic': Int8 dynamic activation + weight quantization
			- config: Custom TorchAO config object (if provided, overrides quant_type)
	
	Returns:
		Tuple of (quantized_model, info_dict) where info_dict contains:
			- backend: "torchao"
			- quant_type: The quantization type applied
			- status: "success" or error details
	
	Raises:
		ImportError: If TorchAO is not installed
		RuntimeError: If quantization fails
	"""
	try:
		# Suppress warnings and stderr during import
		with warnings.catch_warnings():
			warnings.simplefilter("ignore")
			with suppress_stderr():
				from torchao.quantization import (
					quantize_,
					Int4WeightOnlyConfig,
					Int8WeightOnlyConfig,
					Float8WeightOnlyConfig,
					Float8DynamicActivationFloat8WeightConfig,
					Int8DynamicActivationInt8WeightConfig,
				)
	except ImportError as e:
		raise ImportError(
			"TorchAO not installed. Install with: pip install torchao"
		) from e
	
	try:
		# Check if custom config is provided
		if 'config' in kwargs:
			quant_config = kwargs['config']
			quant_type = "custom"
		else:
			# Map quant_type kwarg to config class
			quant_type = kwargs.get('quant_type', 'float8_dynamic')
			
			config_map = {
				'int4_weight_only': Int4WeightOnlyConfig,
				'int8_weight_only': Int8WeightOnlyConfig,
				'float8_weight_only': Float8WeightOnlyConfig,
				'float8_dynamic': Float8DynamicActivationFloat8WeightConfig,
				'int8_dynamic': Int8DynamicActivationInt8WeightConfig,
			}
			
			if quant_type not in config_map:
				raise ValueError(
					f"Unknown quant_type: {quant_type}. "
					f"Supported types: {list(config_map.keys())}"
				)
			
			config_class = config_map[quant_type]
			quant_config = config_class()
		
		# Apply quantization (modifies model in-place)
		quantize_(model, quant_config)
		
		info = {
			"backend": "torchao",
			"quant_type": quant_type,
			"status": "success"
		}
		
		return model, info
		
	except Exception as e:
		raise RuntimeError(f"TorchAO quantization failed: {e}") from e


class TorchAOQuantizer:
	"""Wrapper around TorchAO quantization methods."""
	
	def __init__(self):
		"""Initialize TorchAOQuantizer with available quantization methods."""
		try:
			# Suppress warnings and stderr during import
			with warnings.catch_warnings():
				warnings.simplefilter("ignore")
				with suppress_stderr():
					from torchao.quantization import (
						quantize_,
						Int8WeightOnlyConfig,
						Int8DynamicActivationInt8WeightConfig,
					)
					self._quantize_ = quantize_
					self._Int8WeightOnlyConfig = Int8WeightOnlyConfig
					self._Int8DynamicActivationInt8WeightConfig = Int8DynamicActivationInt8WeightConfig
					self._torchao_available = True
		except ImportError:
			self._torchao_available = False
			raise ImportError(
				"TorchAO not installed. Install with: pip install torchao"
			)
		
		# Compression ratios for each method (FP32 -> quantized)
		self.compression_ratios = {
			'int8_weight_only': 4.0,  # FP32 -> INT8
			'int8_dynamic': 4.0,
		}
		
		# Available quantization methods
		self.methods = {
			'int8_weight_only': 'int8_weight_only',
			'int8_dynamic': 'int8_dynamic',
		}
	
	def quantize(self, model: torch.nn.Module, method: str = 'int8_weight_only') -> torch.nn.Module:
		"""Apply TorchAO quantization to a model.
		
		Args:
			model: PyTorch model to quantize (modified in-place)
			method: Quantization method to apply. Options:
				- 'int8_weight_only': 8-bit integer weight-only quantization
				- 'int8_dynamic': 8-bit integer dynamic activation + weight quantization
		
		Returns:
			The quantized model (same object, modified in-place)
		
		Raises:
			ImportError: If TorchAO is not installed
			ValueError: If method is not supported
			RuntimeError: If quantization fails
		"""
		if not self._torchao_available:
			raise ImportError(
				"TorchAO not installed. Install with: pip install torchao"
			)
		
		if method not in self.methods:
			raise ValueError(
				f"Unknown method: {method}. "
				f"Supported methods: {list(self.methods.keys())}"
			)
		
		try:
			# Create appropriate config based on method
			if method == 'int8_weight_only':
				config = self._Int8WeightOnlyConfig()
			elif method == 'int8_dynamic':
				config = self._Int8DynamicActivationInt8WeightConfig()
			else:
				raise ValueError(f"Unsupported method: {method}")
			
			# TorchAO in-place quantization
			self._quantize_(model, config)
			return model
		
		except Exception as e:
			raise RuntimeError(f"TorchAO quantization failed: {e}") from e
	
	def estimate_compression(self, original_size: float, method: str) -> float:
		"""Estimate compressed model size based on quantization method.
		
		Args:
			original_size: Original model size in bytes (or any size unit)
			method: Quantization method used
		
		Returns:
			Estimated compressed size (in same unit as original_size)
		
		Raises:
			ValueError: If method is not supported
		"""
		if method not in self.compression_ratios:
			raise ValueError(
				f"Unknown method: {method}. "
				f"Supported methods: {list(self.compression_ratios.keys())}"
			)
		
		ratio = self.compression_ratios[method]
		return original_size / ratio
	
	def get_compression_ratio(self, method: str) -> float:
		"""Get compression ratio for a quantization method.
		
		Args:
			method: Quantization method
		
		Returns:
			Compression ratio (e.g., 4.0 means 4x compression)
		
		Raises:
			ValueError: If method is not supported
		"""
		if method not in self.compression_ratios:
			raise ValueError(
				f"Unknown method: {method}. "
				f"Supported methods: {list(self.compression_ratios.keys())}"
			)
		return self.compression_ratios[method]


def autoquant(
	model: torch.nn.Module,
	example_input: Optional[Any] = None,
	qtensor_class_list: Optional[List] = None,
	filter_fn: Optional[Callable] = None,
	mode: List = ["interpolate", 0.85],
	manual: bool = False,
	set_inductor_config: bool = True,
	supress_autoquant_errors: bool = True,
	min_sqnr: Optional[float] = None,
	**aq_kwargs
) -> torch.nn.Module:
	"""Autoquantization function that identifies the fastest way to quantize each layer.
	
	Autoquantization happens in three steps:
	1. Prepare Model: the model is searched for Linear layers whose weights are exchanged
	   for AutoQuantizableLinearWeight.
	2. Shape Calibration: the user runs the model on one or more inputs, the details of
	   the activation shape/dtype seen by the AutoQuantizableLinearWeight are recorded.
	3. Finalize Autoquantization: for each AutoQuantizableLinearWeight, benchmarks are run
	   for each shape/dtype on each member of the qtensor_class_list. The fastest option
	   is picked, resulting in a highly performant model.
	
	This autoquant function performs step 1. Steps 2 and 3 can be completed by simply
	running the model. If example_input is provided, this function also runs the model
	(which completes steps 2 and 3).
	
	Args:
		model: The model to be autoquantized
		example_input: An example input for the model. If provided, performs a forward pass
			on this input (which fully autoquantizes the model unless manual=True). Defaults to None.
		qtensor_class_list: A list of tensor classes to be used for quantization.
			Defaults to DEFAULT_AUTOQUANT_CLASS_LIST.
		filter_fn: A filter function to apply to the model parameters. Defaults to None.
		mode: A list containing mode settings for quantization. The first element is the
			mode type (e.g., "interpolate"), and the second element is the mode value
			(e.g., 0.85). Defaults to ["interpolate", 0.85].
		manual: Whether to stop shape calibration and do autoquant after a single run
			(default, False) or to wait for the user to call model.finalize_autoquant (True)
			so inputs with several shapes/dtypes can be logged.
		set_inductor_config: Whether to automatically use recommended inductor config
			settings (defaults to True)
		supress_autoquant_errors: Whether to suppress errors during autoquantization
			(defaults to True)
		min_sqnr: Minimum acceptable signal to quantization noise ratio for output of
			quantized layer v.s. non-quantized layer. Used to filter out quantization
			methods that cause too large numerical impact. Reasonable starting value is 40.
		**aq_kwargs: Additional keyword arguments for the autoquantization process.
	
	Returns:
		The autoquantized and wrapped model. If example_input is provided, the function
		performs a forward pass on the input and returns the result of the forward pass.
	
	Raises:
		ImportError: If TorchAO is not installed
		RuntimeError: If autoquantization fails
	
	Example:
		>>> # Basic usage with example input
		>>> quantized_model = autoquant(model, example_input=input_tensor)
		>>> 
		>>> # Manual mode for multiple input shapes
		>>> quantized_model = autoquant(model, manual=True)
		>>> quantized_model(*input1)
		>>> quantized_model(*input2)
		>>> quantized_model.finalize_autoquant()
		>>> 
		>>> # With torch.compile
		>>> quantized_model = autoquant(torch.compile(model))
		>>> output = quantized_model(*example_input)
	"""
	try:
		# Suppress warnings and stderr during import
		with warnings.catch_warnings():
			warnings.simplefilter("ignore")
			with suppress_stderr():
				from torchao.quantization import autoquant as torchao_autoquant
	except ImportError as e:
		raise ImportError(
			"TorchAO not installed. Install with: pip install torchao"
		) from e
	
	try:
		return torchao_autoquant(
			model,
			example_input=example_input,
			qtensor_class_list=qtensor_class_list,
			filter_fn=filter_fn,
			mode=mode,
			manual=manual,
			set_inductor_config=set_inductor_config,
			supress_autoquant_errors=supress_autoquant_errors,
			min_sqnr=min_sqnr,
			**aq_kwargs
		)
	except Exception as e:
		raise RuntimeError(f"TorchAO autoquantization failed: {e}") from e

