from __future__ import annotations

from typing import Any
from pathlib import Path

from .base import BaseAdapter


class OnnxAdapter(BaseAdapter):
	def can_handle(self, path: str) -> bool:
		return Path(path).suffix.lower() == '.onnx'

	def load(self, path: str) -> Any:
		try:
			import onnxruntime as ort
			return ort.InferenceSession(path)
		except Exception:
			import onnx
			return onnx.load(path)

	def save(self, model: Any, path: str) -> None:
		try:
			import onnx
			onnx.save(model, path)
		except Exception as e:
			raise RuntimeError(f"Saving ONNX requires onnx: {e}")

	def export_onnx(self, model: Any, path: str, opset: int = 17) -> None:
		# Already ONNX: either pass-through (copy) or re-save
		self.save(model, path)

	def export_torchscript(self, model: Any, path: str, optimize: bool = True) -> None:
		raise NotImplementedError("TorchScript export not applicable for ONNX models")



