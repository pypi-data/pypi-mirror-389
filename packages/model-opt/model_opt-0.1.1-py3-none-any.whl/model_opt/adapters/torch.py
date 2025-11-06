from __future__ import annotations

from typing import Any
from pathlib import Path

from .base import BaseAdapter


class TorchAdapter(BaseAdapter):
	def can_handle(self, path: str) -> bool:
		ext = Path(path).suffix.lower()
		return ext in {'.pth', '.pt', '.pkl'}

	def load(self, path: str) -> Any:
		import torch
		model = torch.load(path, map_location='cpu')
		if hasattr(model, 'eval'):
			model.eval()
		return model

	def save(self, model: Any, path: str) -> None:
		import torch
		torch.save(model, path)

	def export_torchscript(self, model: Any, path: str, optimize: bool = True) -> None:
		import torch
		try:
			model = model.eval()
		except Exception:
			pass
		# Minimal example: trace with a dummy input if shape is common
		dummy = torch.randn(1, 3, 224, 224)
		traced = torch.jit.trace(model, dummy)
		if optimize:
			traced = torch.jit.optimize_for_inference(traced)
		traced.save(path)

	def export_onnx(self, model: Any, path: str, opset: int = 17) -> None:
		import torch
		dummy = torch.randn(1, 3, 224, 224)
		torch.onnx.export(model, dummy, path, opset_version=opset, input_names=['input'], output_names=['output'], dynamic_axes={'input': {0: 'batch'}, 'output': {0: 'batch'}})


