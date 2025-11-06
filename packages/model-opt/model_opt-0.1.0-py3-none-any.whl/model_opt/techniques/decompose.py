"""Model decomposition utilities - unified interface to decomposition backends."""
from typing import Any, Dict, Optional

# Import decomposition implementations
try:
	from model_opt.techniques.decomposition.decomposition_svd import SVDDecomposer
	_DECOMPOSITION_AVAILABLE = True
except ImportError:
	_DECOMPOSITION_AVAILABLE = False
	SVDDecomposer = None


class Decomposer:
	"""Unified model decomposition helper.
	
	Supports:
	- SVD (Singular Value Decomposition) for Linear layers
	"""
	
	def __init__(self):
		"""Initialize Decomposer with available decomposition backends."""
		self.svd_decomposer = None
		
		if _DECOMPOSITION_AVAILABLE and SVDDecomposer is not None:
			try:
				self.svd_decomposer = SVDDecomposer()
			except Exception:
				pass
	
	def decompose_model(
		self,
		model: Any,
		method: str = 'svd',
		rank_ratio: float = 0.5,
		min_rank: int = 1,
		max_rank: Optional[int] = None,
		modules_to_decompose: Optional[list] = None,
		**kwargs
	) -> Any:
		"""Decompose model using specified method.
		
		Args:
			model: Model to decompose
			method: Decomposition method. Options: 'svd'. Default: 'svd'
			rank_ratio: Ratio of rank to original dimension (0.0 to 1.0).
				Default: 0.5
			min_rank: Minimum rank for decomposition. Default: 1
			max_rank: Maximum rank for decomposition. Default: None
			modules_to_decompose: Optional list of module names to decompose.
				If None, decomposes all applicable layers.
			**kwargs: Additional decomposition options
		
		Returns:
			The decomposed model
		
		Raises:
			ValueError: If method is not supported
			RuntimeError: If decomposition fails
		"""
		if method == 'svd':
			if not self.svd_decomposer:
				raise RuntimeError("SVD decomposition not available")
			return self.svd_decomposer.decompose_model(
				model,
				rank_ratio=rank_ratio,
				min_rank=min_rank,
				max_rank=max_rank,
				modules_to_decompose=modules_to_decompose
			)
		else:
			raise ValueError(f"Unsupported decomposition method: {method}")
	
	def get_decomposition_info(
		self,
		model: Any,
		method: str = 'svd',
		rank_ratio: float = 0.5
	) -> Dict:
		"""Get information about decomposition opportunities.
		
		Args:
			model: Model to analyze
			method: Decomposition method. Default: 'svd'
			rank_ratio: Ratio to use for rank calculation. Default: 0.5
		
		Returns:
			Dictionary with decomposition information
		"""
		if method == 'svd':
			if not self.svd_decomposer:
				raise RuntimeError("SVD decomposition not available")
			return self.svd_decomposer.get_decomposition_info(model, rank_ratio=rank_ratio)
		else:
			raise ValueError(f"Unsupported decomposition method: {method}")
