"""JAX adapter and helpers (best-effort placeholders)."""
from typing import Any
from pathlib import Path

from .base import BaseAdapter


def params_to_numpy_tree(params: Any) -> Any:
	try:
		import jax
		return jax.tree_map(lambda x: x if hasattr(x, 'shape') else x, params)
	except Exception as e:
		raise RuntimeError(f"JAX adapter failed: {e}")


class JaxAdapter(BaseAdapter):
	def can_handle(self, path: str) -> bool:
		ext = Path(path).suffix.lower()
		return ext in {'.ckpt', '.jax'}

	def load(self, path: str) -> Any:
		# Minimal: load pickled params
		import pickle
		with open(path, 'rb') as f:
			return pickle.load(f)

	def save(self, model: Any, path: str) -> None:
		import pickle
		with open(path, 'wb') as f:
			pickle.dump(model, f)

	def export_onnx(self, model: Any, path: str, opset: int = 17) -> None:
		raise NotImplementedError("Exporting JAX params to ONNX requires a traced function; not available here")

	def export_torchscript(self, model: Any, path: str, optimize: bool = True) -> None:
		raise NotImplementedError("TorchScript export not supported for JAX")
