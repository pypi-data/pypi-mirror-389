"""Unified model optimizer."""
from typing import Dict, Any, Optional, Callable, Tuple
from pathlib import Path
from model_opt.core.model_loader import load_model

# Internal adapters
from model_opt.adapters.base import AdapterRegistry
from model_opt.adapters.torch import TorchAdapter
from model_opt.adapters.keras import KerasAdapter
from model_opt.adapters.tensorflow import TensorFlowAdapter
from model_opt.adapters.onnx import OnnxAdapter
from model_opt.adapters.jax import JaxAdapter


class Optimizer:
	"""Unified optimizer for model optimization techniques."""
	
	def __init__(self, model_path: str, test_dataset: str, test_script: str):
		self.model_path = model_path
		self.test_dataset = test_dataset
		self.test_script = test_script
		self.model, self.framework = load_model(model_path)
		self._adapter_registry = self._init_registry()
		self._adapter = self._select_adapter(model_path)

	def _init_registry(self) -> AdapterRegistry:
		reg = AdapterRegistry()
		reg.register(TorchAdapter())
		reg.register(KerasAdapter())
		reg.register(TensorFlowAdapter())
		reg.register(OnnxAdapter())
		reg.register(JaxAdapter())
		return reg

	def _select_adapter(self, path: str):
		adapter = self._adapter_registry.get_for(path)
		return adapter
		
	def quantize(self, output_path: Optional[str] = None, **options) -> Tuple[Any, dict]:
		"""Apply quantization using TorchAO backend."""
		from model_opt.techniques.quantize import Quantizer
		
		method = options.get('quant_method', 'int8_weight_only')
		quantizer = Quantizer()
		q_model, q_info = quantizer.quantize(
			self.model,
			method=method,
			output_path=output_path,
			**options
		)
		return q_model, q_info
	
	def prune(self, **options) -> Any:
		"""Apply pruning using available backend."""
		backend = options.get('prune_backend', 'torch-pruning')
		amount = float(options.get('prune_amount', 0.5))
		
		if backend == 'torch-pruning':
			if self.framework != 'pytorch':
				raise ValueError("torch-pruning backend only supports PyTorch models")
			
			from model_opt.techniques.pruning.pruning_torch import StructuredPruner
			import torch
			
			# Create example input for dependency graph
			# This is a placeholder - should use actual model input shape
			example_input = torch.randn(1, 3, 224, 224)
			
			pruner = StructuredPruner()
			importance = options.get('prune_criterion', 'magnitude')
			return pruner.prune(self.model, example_input, pruning_ratio=amount, importance=importance)
		else:
			# Fallback to basic PyTorch pruning
			from model_opt.techniques.prune import Pruner
			criterion = options.get('prune_criterion', 'l1')
			return Pruner.prune_model(self.model, amount=amount, criterion=criterion)
	
	
	def optimize(self, techniques: list[str], output_path: Optional[str] = None, **options) -> Any:
		"""Apply multiple optimization techniques with backends."""
		current_model = self.model
		for technique in techniques:
			if technique == 'prune':
				current_model = self.prune(**options)
			elif technique == 'quantize':
				current_model, _ = self.quantize(output_path=output_path, **options)
			# TODO: fuse, distill
		return current_model

