from __future__ import annotations

from typing import Any, Optional
from pathlib import Path


class BaseAdapter:
	"""Common adapter interface for model IO and exports."""

	def can_handle(self, path: str) -> bool:
		raise NotImplementedError

	def load(self, path: str) -> Any:
		raise NotImplementedError

	def save(self, model: Any, path: str) -> None:
		raise NotImplementedError

	def export_onnx(self, model: Any, path: str, opset: int = 17) -> None:
		raise NotImplementedError

	def export_torchscript(self, model: Any, path: str, optimize: bool = True) -> None:
		raise NotImplementedError


class AdapterRegistry:
	"""Registry to select adapter by file path."""

	def __init__(self) -> None:
		self._adapters: list[BaseAdapter] = []

	def register(self, adapter: BaseAdapter) -> None:
		self._adapters.append(adapter)

	def get_for(self, path: str) -> Optional[BaseAdapter]:
		for a in self._adapters:
			if a.can_handle(path):
				return a
		return None


