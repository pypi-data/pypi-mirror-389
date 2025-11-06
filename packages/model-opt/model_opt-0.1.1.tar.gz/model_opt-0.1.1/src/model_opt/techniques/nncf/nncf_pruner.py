"""NNCF pruning backend."""
from typing import Any, Dict, Optional, List
from model_opt.core.exceptions import OptimizationError, EnvironmentError

try:
    import nncf
    import torch
    _NNCF_AVAILABLE = True
except ImportError:
    _NNCF_AVAILABLE = False


class NNCFPruner:
    """Pruning backend using NNCF."""
    
    def __init__(self):
        """Initialize NNCF pruner."""
        if not _NNCF_AVAILABLE:
            raise EnvironmentError(
                "NNCF is not installed. Install with: pip install nncf"
            )
    
    def prune(
        self,
        model: Any,
        pruning_ratio: float = 0.5,
        pruning_method: str = 'magnitude',
        target_modules: Optional[List[str]] = None,
        **kwargs
    ) -> Any:
        """Prune model using NNCF.
        
        Args:
            model: PyTorch model to prune
            pruning_ratio: Fraction of weights to prune (0.0 to 1.0)
            pruning_method: Pruning method ('magnitude', 'rb', 'movement')
            target_modules: Optional list of module names to prune
            **kwargs: Additional pruning parameters
            
        Returns:
            Pruned model
            
        Raises:
            OptimizationError: If pruning fails
        """
        if not isinstance(model, torch.nn.Module):
            raise OptimizationError("NNCF pruner only supports PyTorch models")
        
        try:
            # Create pruning configuration
            if pruning_method == 'magnitude':
                pruning_config = nncf.MagnitudeSparsityConfig(
                    sparsity_level=pruning_ratio,
                    weight_importance=nncf.MagnitudeSparsityConfig.WeightImportanceType.WEIGHT,
                )
            elif pruning_method == 'rb':
                pruning_config = nncf.RBSparsityConfig(sparsity_level=pruning_ratio)
            elif pruning_method == 'movement':
                pruning_config = nncf.MovementSparsityConfig(
                    sparsity_level=pruning_ratio,
                    warmup_start_epoch=kwargs.get('warmup_start_epoch', 0),
                    warmup_end_epoch=kwargs.get('warmup_end_epoch', 3),
                )
            else:
                raise OptimizationError(f"Unknown pruning method: {pruning_method}")
            
            # Create compression configuration
            compression_config = nncf.CompressionConfig(
                pruning_config=pruning_config,
            )
            
            # Apply pruning
            pruned_model = nncf.torch.create_compressed_model(model, compression_config)
            
            return pruned_model
            
        except Exception as e:
            raise OptimizationError(f"NNCF pruning failed: {e}")
    
    def get_pruning_info(self, model: Any) -> Dict:
        """Get pruning information from model.
        
        Args:
            model: Pruned model
            
        Returns:
            Dictionary with pruning information
        """
        info = {
            'pruned': True,
            'framework': 'nncf',
        }
        
        # Try to extract additional info if available
        if hasattr(model, 'nncf'):
            info['nncf_config'] = str(model.nncf)
        
        return info

