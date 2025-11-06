"""NNCF quantization backend."""
from typing import Any, Dict, Optional, Tuple
from model_opt.core.exceptions import OptimizationError, EnvironmentError

try:
    import nncf
    import torch
    _NNCF_AVAILABLE = True
except ImportError:
    _NNCF_AVAILABLE = False


class NNCFQuantizer:
    """Quantization backend using NNCF."""
    
    def __init__(self):
        """Initialize NNCF quantizer."""
        if not _NNCF_AVAILABLE:
            raise EnvironmentError(
                "NNCF is not installed. Install with: pip install nncf"
            )
    
    def quantize(
        self,
        model: Any,
        calibration_dataset: Optional[Any] = None,
        quantization_mode: str = 'post_training',
        preset: str = 'performance',
        **kwargs
    ) -> Tuple[Any, Dict]:
        """Quantize model using NNCF.
        
        Args:
            model: PyTorch model to quantize
            calibration_dataset: Optional calibration dataset for PTQ
            quantization_mode: 'post_training' or 'quantization_aware_training'
            preset: 'performance' or 'mixed' (balanced)
            **kwargs: Additional quantization parameters
            
        Returns:
            Tuple of (quantized_model, quantization_info)
            
        Raises:
            OptimizationError: If quantization fails
        """
        if not isinstance(model, torch.nn.Module):
            raise OptimizationError("NNCF quantizer only supports PyTorch models")
        
        try:
            if quantization_mode == 'post_training':
                # Post-training quantization
                if calibration_dataset is None:
                    raise OptimizationError(
                        "Calibration dataset required for post-training quantization"
                    )
                
                # Create quantization configuration
                quantization_config = nncf.QuantizationConfig(
                    input_info=kwargs.get('input_info'),
                    preset=nncf.QuantizationPreset.PERFORMANCE if preset == 'performance' 
                           else nncf.QuantizationPreset.MIXED,
                )
                
                # Apply quantization
                quantized_model = nncf.quantize(model, quantization_config, calibration_dataset)
                
            elif quantization_mode == 'quantization_aware_training':
                # Quantization-aware training
                compression_config = nncf.QuantizationConfig(
                    input_info=kwargs.get('input_info'),
                    preset=nncf.QuantizationPreset.PERFORMANCE if preset == 'performance'
                           else nncf.QuantizationPreset.MIXED,
                )
                
                quantized_model = nncf.torch.create_compressed_model(model, compression_config)
            else:
                raise OptimizationError(f"Unknown quantization mode: {quantization_mode}")
            
            info = {
                'quantization_mode': quantization_mode,
                'preset': preset,
                'framework': 'nncf',
            }
            
            return quantized_model, info
            
        except Exception as e:
            raise OptimizationError(f"NNCF quantization failed: {e}")
    
    def get_quantization_info(self, model: Any) -> Dict:
        """Get quantization information from model.
        
        Args:
            model: Quantized model
            
        Returns:
            Dictionary with quantization information
        """
        # NNCF stores quantization info in model state
        info = {
            'quantized': True,
            'framework': 'nncf',
        }
        
        # Try to extract additional info if available
        if hasattr(model, 'nncf'):
            info['nncf_config'] = str(model.nncf)
        
        return info

