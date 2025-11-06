from __future__ import annotations

from typing import Any
from pathlib import Path

from .base import BaseAdapter


class KerasAdapter(BaseAdapter):
	def can_handle(self, path: str) -> bool:
		ext = Path(path).suffix.lower()
		# .h5 or .keras files; SavedModel directory has no suffix
		return ext in {'.h5', '.keras'} or Path(path).is_dir()

	def load(self, path: str) -> Any:
		try:
			from tensorflow import keras as tfk
		except Exception:
			import keras as tfk  # type: ignore
		return tfk.models.load_model(path)

	def save(self, model: Any, path: str) -> None:
		model.save(path)

	def export_onnx(self, model: Any, path: str, opset: int = 17) -> None:
		# Try tf2onnx if available
		try:
			import tf2onnx  # noqa: F401
			export_path = path
			import tensorflow as tf
			# Convert via from_keras
			import tf2onnx.convert
			_ = tf2onnx.convert.from_keras(model, output_path=export_path, opset=opset)
		except Exception as e:
			raise RuntimeError(f"Keras->ONNX export requires tf2onnx: {e}")

	def export_torchscript(self, model: Any, path: str, optimize: bool = True) -> None:
		raise NotImplementedError("TorchScript export not supported for Keras directly")


