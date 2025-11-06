"""Pipeline composition utilities."""
from typing import Any, Callable, List, Tuple


def apply_sequence(model: Any, steps: List[Tuple[str, Callable]]):
	"""Apply a sequence of (name, fn) to a model, emitting simple logs."""
	current = model
	for name, fn in steps:
		print(f"[Pipeline] Applying: {name}")
		current = fn(current)
	print("[Pipeline] Completed")
	return current
