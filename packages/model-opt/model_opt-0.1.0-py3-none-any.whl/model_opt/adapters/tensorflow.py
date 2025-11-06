from __future__ import annotations

from typing import Any
from pathlib import Path

from .base import BaseAdapter


class TensorFlowAdapter(BaseAdapter):
	def can_handle(self, path: str) -> bool:
		ext = Path(path).suffix.lower()
		# SavedModel dir or frozen graph .pb
		return ext == '.pb' or Path(path).is_dir()

	def load(self, path: str) -> Any:
		import tensorflow as tf
		if Path(path).is_dir():
			return tf.keras.models.load_model(path)
		# For .pb frozen graphs, wrap loading into a concrete function if needed
		raise NotImplementedError("Direct .pb frozen graph loading not implemented; use SavedModel directory")

	def save(self, model: Any, path: str) -> None:
		# Save as SavedModel directory
		model.save(path)

	def export_onnx(self, model: Any, path: str, opset: int = 17) -> None:
		try:
			import tf2onnx.convert
			_ = tf2onnx.convert.from_keras(model, output_path=path, opset=opset)
		except Exception as e:
			raise RuntimeError(f"TensorFlow->ONNX export requires tf2onnx: {e}")

	def export_torchscript(self, model: Any, path: str, optimize: bool = True) -> None:
		raise NotImplementedError("TorchScript export not supported for TensorFlow")


