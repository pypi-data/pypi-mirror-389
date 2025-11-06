"""Model zoo interface for pretrained model loading and architecture detection."""
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from .exceptions import ModelLoadError, EnvironmentError


class ModelZoo:
    """Interface for loading pretrained models from various sources."""
    
    def __init__(self):
        """Initialize model zoo."""
        self._registry: Dict[str, Dict] = {}
        self._initialize_registry()
    
    def _initialize_registry(self):
        """Initialize model registry with common architectures."""
        # PyTorch torchvision models
        self._registry['torchvision'] = {
            'resnet18': {'source': 'torchvision', 'framework': 'pytorch'},
            'resnet34': {'source': 'torchvision', 'framework': 'pytorch'},
            'resnet50': {'source': 'torchvision', 'framework': 'pytorch'},
            'resnet101': {'source': 'torchvision', 'framework': 'pytorch'},
            'resnet152': {'source': 'torchvision', 'framework': 'pytorch'},
            'vgg16': {'source': 'torchvision', 'framework': 'pytorch'},
            'vgg19': {'source': 'torchvision', 'framework': 'pytorch'},
            'alexnet': {'source': 'torchvision', 'framework': 'pytorch'},
            'mobilenet_v2': {'source': 'torchvision', 'framework': 'pytorch'},
            'mobilenet_v3_large': {'source': 'torchvision', 'framework': 'pytorch'},
            'mobilenet_v3_small': {'source': 'torchvision', 'framework': 'pytorch'},
            'densenet121': {'source': 'torchvision', 'framework': 'pytorch'},
            'densenet169': {'source': 'torchvision', 'framework': 'pytorch'},
            'densenet201': {'source': 'torchvision', 'framework': 'pytorch'},
            'efficientnet_b0': {'source': 'torchvision', 'framework': 'pytorch'},
            'efficientnet_b1': {'source': 'torchvision', 'framework': 'pytorch'},
            'efficientnet_b2': {'source': 'torchvision', 'framework': 'pytorch'},
            'efficientnet_b3': {'source': 'torchvision', 'framework': 'pytorch'},
            'efficientnet_b4': {'source': 'torchvision', 'framework': 'pytorch'},
        }
        
        # timm models (if available)
        if self._check_timm():
            try:
                import timm
                # Add common timm models
                timm_models = [
                    'vit_base_patch16_224',
                    'vit_large_patch16_224',
                    'deit_base_distilled_patch16_224',
                    'swin_base_patch4_window7_224',
                ]
                for model_name in timm_models:
                    self._registry['timm'] = self._registry.get('timm', {})
                    self._registry['timm'][model_name] = {
                        'source': 'timm',
                        'framework': 'pytorch'
                    }
            except:
                pass
    
    def _check_timm(self) -> bool:
        """Check if timm is available."""
        try:
            import timm
            return True
        except ImportError:
            return False
    
    def load_pretrained(
        self,
        model_name: str,
        source: Optional[str] = None,
        pretrained: bool = True
    ) -> Tuple[Any, str]:
        """Load pretrained model from zoo.
        
        Args:
            model_name: Name of the model
            source: Source name (torchvision, timm, etc.). If None, auto-detect.
            pretrained: Whether to load pretrained weights
            
        Returns:
            Tuple of (model, framework)
            
        Raises:
            ModelLoadError: If model cannot be loaded
            EnvironmentError: If required dependencies are missing
        """
        # Auto-detect source if not specified
        if source is None:
            source = self._detect_source(model_name)
        
        if source == 'torchvision':
            return self._load_torchvision(model_name, pretrained)
        elif source == 'timm':
            return self._load_timm(model_name, pretrained)
        elif source == 'torch_hub':
            return self._load_torch_hub(model_name, pretrained)
        else:
            raise ModelLoadError(f"Unknown model source: {source}")
    
    def _detect_source(self, model_name: str) -> str:
        """Detect source for model name.
        
        Args:
            model_name: Model name
            
        Returns:
            Source name
        """
        # Check torchvision first
        if model_name in self._registry.get('torchvision', {}):
            return 'torchvision'
        
        # Check timm
        if model_name in self._registry.get('timm', {}):
            return 'timm'
        
        # Default to torchvision
        return 'torchvision'
    
    def _load_torchvision(self, model_name: str, pretrained: bool) -> Tuple[Any, str]:
        """Load model from torchvision.
        
        Args:
            model_name: Model name
            pretrained: Whether to load pretrained weights
            
        Returns:
            Tuple of (model, framework)
        """
        try:
            import torchvision.models as models
        except ImportError:
            raise EnvironmentError(
                "torchvision is required. Install with: pip install torchvision"
            )
        
        if not hasattr(models, model_name):
            raise ModelLoadError(f"Model '{model_name}' not found in torchvision")
        
        model_fn = getattr(models, model_name)
        model = model_fn(pretrained=pretrained)
        model.eval()
        
        return model, 'pytorch'
    
    def _load_timm(self, model_name: str, pretrained: bool) -> Tuple[Any, str]:
        """Load model from timm.
        
        Args:
            model_name: Model name
            pretrained: Whether to load pretrained weights
            
        Returns:
            Tuple of (model, framework)
        """
        try:
            import timm
        except ImportError:
            raise EnvironmentError(
                "timm is required. Install with: pip install timm"
            )
        
        try:
            model = timm.create_model(model_name, pretrained=pretrained)
            model.eval()
            return model, 'pytorch'
        except Exception as e:
            raise ModelLoadError(f"Failed to load model '{model_name}' from timm: {e}")
    
    def _load_torch_hub(self, model_name: str, pretrained: bool) -> Tuple[Any, str]:
        """Load model from torch.hub.
        
        Args:
            model_name: Model name (format: repo/model_name)
            pretrained: Whether to load pretrained weights
            
        Returns:
            Tuple of (model, framework)
        """
        try:
            import torch
        except ImportError:
            raise EnvironmentError("PyTorch is required for torch.hub models")
        
        try:
            # Parse repo/model_name format
            if '/' in model_name:
                repo, name = model_name.split('/', 1)
            else:
                repo = 'pytorch/vision'
                name = model_name
            
            model = torch.hub.load(repo, name, pretrained=pretrained)
            model.eval()
            return model, 'pytorch'
        except Exception as e:
            raise ModelLoadError(f"Failed to load model '{model_name}' from torch.hub: {e}")
    
    def detect_architecture(self, model: Any, framework: str = 'pytorch') -> Dict[str, Any]:
        """Detect model architecture and metadata.
        
        Args:
            model: Model object
            framework: Framework name
            
        Returns:
            Dictionary with architecture information
        """
        if framework == 'pytorch':
            return self._detect_pytorch_architecture(model)
        elif framework in ['tensorflow', 'keras']:
            return self._detect_keras_architecture(model)
        else:
            return {'architecture_type': 'Unknown', 'framework': framework}
    
    def _detect_pytorch_architecture(self, model: Any) -> Dict[str, Any]:
        """Detect PyTorch model architecture.
        
        Args:
            model: PyTorch model
            
        Returns:
            Architecture information dictionary
        """
        arch_info = {
            'framework': 'pytorch',
            'model_class': model.__class__.__name__,
            'architecture_type': 'Unknown',
            'layer_types': {},
            'parameter_count': 0,
        }
        
        try:
            # Count parameters
            arch_info['parameter_count'] = sum(
                p.numel() for p in model.parameters() if p.requires_grad
            )
            
            # Detect layer types
            import torch.nn as nn
            layer_counts = {}
            for module in model.modules():
                module_type = type(module).__name__
                if module_type not in ['Sequential', 'ModuleList', 'ModuleDict']:
                    layer_counts[module_type] = layer_counts.get(module_type, 0) + 1
            
            arch_info['layer_types'] = layer_counts
            
            # Detect architecture type
            class_name = model.__class__.__name__.lower()
            if 'resnet' in class_name:
                arch_info['architecture_type'] = 'CNN (ResNet)'
                arch_info['model_family'] = 'ResNet'
            elif 'vgg' in class_name:
                arch_info['architecture_type'] = 'CNN (VGG)'
                arch_info['model_family'] = 'VGG'
            elif 'mobilenet' in class_name:
                arch_info['architecture_type'] = 'CNN (MobileNet)'
                arch_info['model_family'] = 'MobileNet'
            elif 'efficientnet' in class_name:
                arch_info['architecture_type'] = 'CNN (EfficientNet)'
                arch_info['model_family'] = 'EfficientNet'
            elif 'transformer' in class_name or 'vit' in class_name:
                arch_info['architecture_type'] = 'Transformer (ViT)'
                arch_info['model_family'] = 'Vision Transformer'
            elif 'densenet' in class_name:
                arch_info['architecture_type'] = 'CNN (DenseNet)'
                arch_info['model_family'] = 'DenseNet'
            else:
                # Check for common patterns
                if any('Conv' in str(type(m)) for m in model.modules()):
                    arch_info['architecture_type'] = 'CNN'
                elif any('Transformer' in str(type(m)) for m in model.modules()):
                    arch_info['architecture_type'] = 'Transformer'
                else:
                    arch_info['architecture_type'] = 'Unknown'
        
        except Exception as e:
            arch_info['error'] = str(e)
        
        return arch_info
    
    def _detect_keras_architecture(self, model: Any) -> Dict[str, Any]:
        """Detect Keras/TensorFlow model architecture.
        
        Args:
            model: Keras/TensorFlow model
            
        Returns:
            Architecture information dictionary
        """
        arch_info = {
            'framework': 'keras',
            'architecture_type': 'Unknown',
            'layer_types': {},
        }
        
        try:
            layer_counts = {}
            for layer in model.layers:
                layer_type = layer.__class__.__name__
                layer_counts[layer_type] = layer_counts.get(layer_type, 0) + 1
            
            arch_info['layer_types'] = layer_counts
            
            # Detect architecture type from layer names
            layer_names = [l.__class__.__name__ for l in model.layers]
            if any('ResNet' in n for n in layer_names):
                arch_info['architecture_type'] = 'CNN (ResNet)'
            elif any('VGG' in n for n in layer_names):
                arch_info['architecture_type'] = 'CNN (VGG)'
            elif any('MobileNet' in n for n in layer_names):
                arch_info['architecture_type'] = 'CNN (MobileNet)'
            else:
                arch_info['architecture_type'] = 'CNN'
        
        except Exception as e:
            arch_info['error'] = str(e)
        
        return arch_info
    
    def list_models(self, source: Optional[str] = None) -> List[str]:
        """List available models.
        
        Args:
            source: Optional source name to filter by
            
        Returns:
            List of model names
        """
        models = []
        if source:
            models.extend(self._registry.get(source, {}).keys())
        else:
            for source_registry in self._registry.values():
                models.extend(source_registry.keys())
        return sorted(set(models))


def get_model_zoo() -> ModelZoo:
    """Get or create global model zoo instance.
    
    Returns:
        ModelZoo instance
    """
    if '_model_zoo' not in globals():
        globals()['_model_zoo'] = ModelZoo()
    return globals()['_model_zoo']

