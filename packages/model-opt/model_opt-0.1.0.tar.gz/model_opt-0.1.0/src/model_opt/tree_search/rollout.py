"""Zero-shot rollout evaluator for fast tree search simulation."""
import time
from typing import Dict, Optional, Any, List, Tuple
import numpy as np

try:
    import torch
    import torch.nn as nn
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False

from model_opt.autotuner.search_space import (
    CompressionTechnique,
    CompressionResult,
    ModelSignature,
)
from model_opt.techniques.quantize import Quantizer
from model_opt.techniques.prune import Pruner
from model_opt.techniques.decompose import Decomposer
from model_opt.techniques.fuse import LayerFuser


class ZeroShotRollout:
    """Zero-shot evaluation for MCTS rollouts (fast, no validation data needed)."""
    
    def __init__(self):
        """Initialize zero-shot rollout evaluator."""
        if not _TORCH_AVAILABLE:
            raise ImportError("PyTorch is required for ZeroShotRollout")
        
        self.quantizer = Quantizer()
        self.pruner = Pruner()
        self.decomposer = Decomposer()
        self.fuser = LayerFuser()
    
    def evaluate_config(
        self,
        model: nn.Module,
        techniques: List[CompressionTechnique],
        example_input: Optional[Any] = None,
        original_size: Optional[float] = None,
        timeout_seconds: float = 30.0
    ) -> CompressionResult:
        """Evaluate compression configuration using zero-shot methods.
        
        Args:
            model: Model to evaluate
            techniques: List of compression techniques to apply
            example_input: Optional example input tensor
            original_size: Original model size in MB (will calculate if None)
            timeout_seconds: Maximum time for evaluation (default: 30s)
            
        Returns:
            CompressionResult with proxy metrics
        """
        start_time = time.time()
        
        # Calculate original size if not provided
        if original_size is None:
            original_size = self._get_model_size(model)
        
        # Apply techniques sequentially
        current_model = model
        applied_techniques = []
        
        for technique in techniques:
            if time.time() - start_time > timeout_seconds:
                break
            
            try:
                current_model = self._apply_technique(
                    current_model,
                    technique,
                    example_input=example_input
                )
                applied_techniques.append(technique)
            except Exception as e:
                # Skip failed techniques
                continue
        
        # Calculate proxy metrics
        optimized_size = self._get_model_size(current_model)
        compression_ratio = original_size / optimized_size if optimized_size > 0 else 1.0
        
        # Estimate speedup based on techniques
        speedup = self._estimate_speedup(applied_techniques)
        
        # Estimate accuracy drop (conservative proxy)
        accuracy_drop = self._estimate_accuracy_drop(applied_techniques)
        
        # Measure inference time if example_input available
        inference_time_ms = 0.0
        if example_input is not None:
            inference_time_ms = self._measure_inference_time(current_model, example_input)
        
        return CompressionResult(
            techniques=applied_techniques,
            speedup=speedup,
            compression_ratio=compression_ratio,
            accuracy_drop=accuracy_drop,
            memory_reduction=compression_ratio,
            inference_time_ms=inference_time_ms
        )
    
    def _apply_technique(
        self,
        model: nn.Module,
        technique: CompressionTechnique,
        example_input: Optional[Any] = None
    ) -> nn.Module:
        """Apply single compression technique (reuse existing logic)."""
        if technique == CompressionTechnique.QUANTIZE_INT8:
            quantized_model, _ = self.quantizer.quantize(model, method='int8_weight_only')
            return quantized_model
        
        elif technique == CompressionTechnique.PRUNE_STRUCTURED_30:
            if example_input is None:
                example_input = self._create_dummy_input(model)
            return self.pruner.prune_model(
                model,
                amount=0.3,
                criterion='magnitude',
                prune_type='structured',
                example_input=example_input
            )
        
        elif technique == CompressionTechnique.PRUNE_STRUCTURED_50:
            if example_input is None:
                example_input = self._create_dummy_input(model)
            return self.pruner.prune_model(
                model,
                amount=0.5,
                criterion='magnitude',
                prune_type='structured',
                example_input=example_input
            )
        
        elif technique == CompressionTechnique.TOKEN_MERGE_30:
            model_str = str(model).lower()
            if 'unet' in model_str or 'diffusion' in model_str:
                return self.pruner.prune_model(
                    model,
                    amount=0.3,
                    prune_type='sd',
                    ratio=0.3
                )
            else:
                return self.pruner.prune_model(
                    model,
                    amount=0.3,
                    prune_type='vit',
                    r=int(0.3 * 16)
                )
        
        elif technique == CompressionTechnique.SVD_50:
            return self.decomposer.decompose_model(model, rank_ratio=0.5)
        
        elif technique == CompressionTechnique.FUSE_LAYERS:
            return self.fuser.fuse_model(
                model,
                fusion_types=['conv_bn_relu', 'linear_gelu']
            )
        
        else:
            return model
    
    def _estimate_speedup(self, techniques: List[CompressionTechnique]) -> float:
        """Estimate speedup based on techniques (proxy metric).
        
        Args:
            techniques: List of applied techniques
            
        Returns:
            Estimated speedup factor
        """
        speedup = 1.0
        
        for technique in techniques:
            if technique == CompressionTechnique.QUANTIZE_INT8:
                speedup *= 1.5  # INT8 typically 1.5-2x
            elif technique == CompressionTechnique.PRUNE_STRUCTURED_30:
                speedup *= 1.3
            elif technique == CompressionTechnique.PRUNE_STRUCTURED_50:
                speedup *= 1.6
            elif technique == CompressionTechnique.TOKEN_MERGE_30:
                speedup *= 1.2
            elif technique == CompressionTechnique.FUSE_LAYERS:
                speedup *= 1.1
            elif technique == CompressionTechnique.SVD_50:
                speedup *= 1.2
        
        return speedup
    
    def _estimate_accuracy_drop(self, techniques: List[CompressionTechnique]) -> float:
        """Estimate accuracy drop based on techniques (conservative proxy).
        
        Args:
            techniques: List of applied techniques
            
        Returns:
            Estimated accuracy drop (0.0 to 1.0)
        """
        total_drop = 0.0
        
        for technique in techniques:
            if technique == CompressionTechnique.QUANTIZE_INT8:
                total_drop += 0.01  # ~1% for INT8
            elif technique == CompressionTechnique.PRUNE_STRUCTURED_30:
                total_drop += 0.02  # ~2% for 30% pruning
            elif technique == CompressionTechnique.PRUNE_STRUCTURED_50:
                total_drop += 0.05  # ~5% for 50% pruning
            elif technique == CompressionTechnique.TOKEN_MERGE_30:
                total_drop += 0.01
            elif technique == CompressionTechnique.SVD_50:
                total_drop += 0.02
        
        return min(1.0, total_drop)  # Cap at 100%
    
    def _get_model_size(self, model: nn.Module) -> float:
        """Get model size in MB."""
        param_size = sum(p.numel() * p.element_size() for p in model.parameters())
        buffer_size = sum(b.numel() * b.element_size() for b in model.buffers())
        total_size = param_size + buffer_size
        return total_size / (1024 * 1024)
    
    def _measure_inference_time(
        self,
        model: nn.Module,
        example_input: Any,
        iterations: int = 10
    ) -> float:
        """Measure inference time in milliseconds.
        
        Args:
            model: Model to benchmark
            example_input: Example input tensor
            iterations: Number of iterations
            
        Returns:
            Average inference time in milliseconds
        """
        model.eval()
        times = []
        
        with torch.no_grad():
            for _ in range(iterations):
                start = time.time()
                _ = model(example_input)
                times.append((time.time() - start) * 1000)
        
        return np.mean(times)
    
    def _create_dummy_input(self, model: nn.Module) -> Any:
        """Create dummy input tensor for model."""
        dummy_shape = None
        
        for module in model.modules():
            if isinstance(module, nn.Conv2d):
                in_channels = module.in_channels
                dummy_shape = (1, in_channels, 224, 224)
                break
            elif isinstance(module, nn.Conv1d):
                in_channels = module.in_channels
                dummy_shape = (1, in_channels, 224)
                break
            elif isinstance(module, nn.Linear):
                in_features = module.in_features
                dummy_shape = (1, in_features)
                break
        
        if dummy_shape is None:
            dummy_shape = (1, 3, 224, 224)
        
        return torch.randn(*dummy_shape)

