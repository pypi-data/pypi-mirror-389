"""Singular Value Decomposition (SVD) for model compression."""
from typing import Any, Dict, List, Optional, Tuple
import torch
import torch.nn as nn


class SVDLinear(nn.Module):
	"""Linear layer decomposed using SVD (Singular Value Decomposition).
	
	Replaces a single Linear layer with two Linear layers:
	- U: (out_features, rank)
	- V: (rank, in_features)
	
	Original weight W ≈ U @ V, where rank < min(out_features, in_features),
	reducing the number of parameters.
	"""
	
	def __init__(
		self,
		in_features: int,
		out_features: int,
		rank: Optional[int] = None,
		bias: Optional[torch.Tensor] = None
	):
		"""Initialize SVD-decomposed Linear layer.
		
		Args:
			in_features: Size of each input sample
			out_features: Size of each output sample
			rank: Rank of the decomposition. If None, uses min(in_features, out_features) // 2
			bias: Optional bias tensor. If provided, uses this bias.
				If None and original layer had bias, will be set during decomposition.
		"""
		super().__init__()
		
		if rank is None:
			rank = min(in_features, out_features) // 2
		
		if rank >= min(in_features, out_features):
			raise ValueError(
				f"Rank {rank} must be less than min({in_features}, {out_features})"
			)
		
		self.in_features = in_features
		self.out_features = out_features
		self.rank = rank
		
		# Decomposed layers: output = U(V(input))
		self.V = nn.Linear(in_features, rank, bias=False)
		self.U = nn.Linear(rank, out_features, bias=bias is not None)
		
		if bias is not None:
			self.U.bias.data.copy_(bias)
	
	def forward(self, x: torch.Tensor) -> torch.Tensor:
		"""Forward pass through decomposed layers.
		
		Args:
			x: Input tensor of shape (..., in_features)
		
		Returns:
			Output tensor of shape (..., out_features)
		"""
		return self.U(self.V(x))
	
	def compression_ratio(self) -> float:
		"""Calculate compression ratio achieved by decomposition.
		
		Returns:
			Ratio of original parameters to decomposed parameters
		"""
		original_params = self.in_features * self.out_features
		decomposed_params = (
			self.in_features * self.rank +  # V layer
			self.rank * self.out_features +  # U layer
			(self.out_features if self.U.bias is not None else 0)  # Bias
		)
		return original_params / decomposed_params if decomposed_params > 0 else 1.0


class SVDDecomposer:
	"""Decompose Linear layers using Singular Value Decomposition (SVD).
	
	SVD decomposes a weight matrix W into U @ S @ V^T, where:
	- U: left singular vectors
	- S: singular values (diagonal matrix)
	- V^T: right singular vectors (transposed)
	
	For decomposition, we combine S and V^T: W ≈ U @ (S @ V^T) = U @ V_new
	"""
	
	def __init__(self):
		"""Initialize SVDDecomposer."""
		pass
	
	def decompose_model(
		self,
		model: nn.Module,
		rank_ratio: float = 0.5,
		min_rank: int = 1,
		max_rank: Optional[int] = None,
		modules_to_decompose: Optional[List[str]] = None,
		inplace: bool = True
	) -> nn.Module:
		"""Decompose Linear layers in a model using SVD.
		
		Args:
			model: PyTorch model to decompose
			rank_ratio: Ratio of rank to original dimension (0.0 to 1.0).
				Default: 0.5 (half rank)
			min_rank: Minimum rank for decomposition. Default: 1
			max_rank: Maximum rank for decomposition. If None, no limit.
			modules_to_decompose: Optional list of module names to decompose.
				If None, decomposes all Linear layers.
			inplace: Whether to modify the model in-place. Default: True
		
		Returns:
			The decomposed model
		
		Raises:
			RuntimeError: If decomposition fails
		
		Example:
			>>> import torch.nn as nn
			>>> from model_opt.techniques.decomposition.decomposition_svd import SVDDecomposer
			>>> 
			>>> model = nn.Sequential(
			...     nn.Linear(512, 2048),
			...     nn.ReLU(),
			...     nn.Linear(2048, 512)
			... )
			>>> decomposer = SVDDecomposer()
			>>> decomposed_model = decomposer.decompose_model(model, rank_ratio=0.5)
		"""
		if not (0.0 < rank_ratio < 1.0):
			raise ValueError(f"rank_ratio must be between 0.0 and 1.0, got {rank_ratio}")
		
		try:
			if not inplace:
				import copy
				model = copy.deepcopy(model)
			
			# Decompose Linear layers
			self._decompose_recursive(
				model,
				rank_ratio,
				min_rank,
				max_rank,
				modules_to_decompose or []
			)
			
			return model
		
		except Exception as e:
			raise RuntimeError(f"SVD decomposition failed: {e}") from e
	
	def _decompose_recursive(
		self,
		module: nn.Module,
		rank_ratio: float,
		min_rank: int,
		max_rank: Optional[int],
		modules_to_decompose: List[str]
	) -> None:
		"""Recursively decompose Linear layers in the model.
		
		Args:
			module: Module to process
			rank_ratio: Ratio for rank calculation
			min_rank: Minimum rank
			max_rank: Maximum rank
			modules_to_decompose: List of module names to decompose
		"""
		for name, child in list(module.named_children()):
			full_name = f"{module.__class__.__name__}.{name}" if hasattr(module, '__class__') else name
			
			# Check if this module should be decomposed
			if isinstance(child, nn.Linear):
				should_decompose = (
					not modules_to_decompose or  # Decompose all if list is empty
					full_name in modules_to_decompose or
					name in modules_to_decompose
				)
				
				if should_decompose:
					svd_linear = self._decompose_linear(child, rank_ratio, min_rank, max_rank)
					setattr(module, name, svd_linear)
			else:
				# Recurse into child modules
				self._decompose_recursive(
					child, rank_ratio, min_rank, max_rank, modules_to_decompose
				)
	
	def _decompose_linear(
		self,
		linear: nn.Linear,
		rank_ratio: float,
		min_rank: int,
		max_rank: Optional[int]
	) -> SVDLinear:
		"""Decompose a single Linear layer using SVD.
		
		Args:
			linear: Linear layer to decompose
			rank_ratio: Ratio for rank calculation
			min_rank: Minimum rank
			max_rank: Maximum rank
		
		Returns:
			SVDLinear module replacing the original Linear layer
		"""
		# Extract weight matrix: shape (out_features, in_features)
		W = linear.weight.data
		out_features, in_features = W.shape
		
		# Calculate rank
		max_possible_rank = min(in_features, out_features)
		rank = max(min_rank, int(max_possible_rank * rank_ratio))
		
		if max_rank is not None:
			rank = min(rank, max_rank)
		
		rank = min(rank, max_possible_rank - 1)  # Ensure rank < min dimension
		
		if rank <= 0:
			raise ValueError(f"Invalid rank {rank} for layer with shape {W.shape}")
		
		# Perform SVD: W = U @ S @ V^T
		U, S, Vt = torch.linalg.svd(W, full_matrices=False)
		
		# Truncate to rank
		U = U[:, :rank]  # (out_features, rank)
		S = S[:rank]  # (rank,)
		Vt = Vt[:rank, :]  # (rank, in_features)
		
		# Combine S and V^T: V_new = S @ V^T
		# S is diagonal, so S @ V^T = diag(S) @ V^T
		# Vt is already V^T (transpose), so we use it directly
		S_diag = torch.diag(S)  # (rank, rank)
		V_new = S_diag @ Vt  # (rank, in_features)
		
		# Create SVDLinear module
		svd_linear = SVDLinear(
			in_features=in_features,
			out_features=out_features,
			rank=rank,
			bias=linear.bias.data.clone() if linear.bias is not None else None
		)
		
		# Set weights
		with torch.no_grad():
			svd_linear.V.weight.data.copy_(V_new)  # (rank, in_features)
			svd_linear.U.weight.data.copy_(U)  # (out_features, rank)
		
		return svd_linear
	
	def decompose_linear(
		self,
		linear: nn.Linear,
		rank: Optional[int] = None,
		rank_ratio: float = 0.5
	) -> SVDLinear:
		"""Decompose a single Linear layer using SVD.
		
		Args:
			linear: Linear layer to decompose
			rank: Explicit rank. If None, calculated from rank_ratio
			rank_ratio: Ratio for rank calculation if rank is None. Default: 0.5
		
		Returns:
			SVDLinear module
		"""
		if rank is None:
			max_rank = min(linear.in_features, linear.out_features)
			rank = max(1, int(max_rank * rank_ratio))
		
		return self._decompose_linear(linear, 0.0, rank, rank)
	
	def get_decomposition_info(
		self,
		model: nn.Module,
		rank_ratio: float = 0.5
	) -> Dict:
		"""Get information about SVD decomposition opportunities.
		
		Args:
			model: Model to analyze
			rank_ratio: Ratio to use for rank calculation
		
		Returns:
			Dictionary with decomposition information
		"""
		info = {
			'total_linear_layers': 0,
			'decomposable_layers': 0,
			'original_params': 0,
			'estimated_params_after': 0,
			'estimated_compression': 0.0,
			'layer_details': []
		}
		
		for name, module in model.named_modules():
			if isinstance(module, nn.Linear):
				info['total_linear_layers'] += 1
				
				in_features = module.in_features
				out_features = module.out_features
				bias_params = 1 if module.bias is not None else 0
				
				original_params = in_features * out_features + bias_params
				info['original_params'] += original_params
				
				# Calculate rank
				max_rank = min(in_features, out_features)
				rank = max(1, int(max_rank * rank_ratio))
				
				if rank < max_rank:
					info['decomposable_layers'] += 1
					
					# Calculate decomposed parameters
					decomposed_params = (
						in_features * rank +  # V layer
						rank * out_features +  # U layer
						bias_params  # Bias
					)
					info['estimated_params_after'] += decomposed_params
					
					compression = original_params / decomposed_params
					info['layer_details'].append({
						'name': name,
						'shape': (out_features, in_features),
						'rank': rank,
						'original_params': original_params,
						'decomposed_params': decomposed_params,
						'compression_ratio': compression
					})
				else:
					info['estimated_params_after'] += original_params
		
		if info['estimated_params_after'] > 0:
			info['estimated_compression'] = (
				info['original_params'] / info['estimated_params_after']
			)
		
		return info

