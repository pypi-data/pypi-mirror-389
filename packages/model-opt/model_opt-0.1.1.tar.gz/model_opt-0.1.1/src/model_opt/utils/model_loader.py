"""Model loader utility for loading downloaded pretrained models."""
import torch
from pathlib import Path
from typing import Optional, Dict, Any, Union
import os


class ModelLoader:
    """Utility class for loading pretrained models from downloaded files."""

    def __init__(self, models_dir: Union[str, Path] = "models"):
        """Initialize model loader.

        Args:
            models_dir: Root directory containing model categories
        """
        self.models_dir = Path(models_dir)

    def list_available_models(self, category: Optional[str] = None) -> Dict[str, list]:
        """List all available models.

        Args:
            category: Optional category filter (classification, detection, etc.)

        Returns:
            Dictionary mapping category to list of model names
        """
        available = {}
        categories = [category] if category else ['classification', 'detection', 'segmentation', 'multimodal']

        for cat in categories:
            cat_dir = self.models_dir / cat
            if cat_dir.exists():
                model_files = list(cat_dir.glob("*.pth")) + list(cat_dir.glob("*.pt"))
                available[cat] = [f.stem for f in model_files]

        return available

    def load_model(
        self,
        model_name: str,
        model_type: str = "classification",
        map_location: str = "cpu"
    ) -> Optional[torch.nn.Module]:
        """Load a pretrained model by name.

        Args:
            model_name: Name of the model (e.g., 'resnet50', 'yolov8s')
            model_type: Type/category of model (classification, detection, etc.)
            map_location: Device to load model on ('cpu', 'cuda', etc.)

        Returns:
            Loaded model or None if not found
        """
        model_path = self.models_dir / model_type / f"{model_name}.pth"
        
        # Try .pt extension if .pth doesn't exist
        if not model_path.exists():
            model_path = self.models_dir / model_type / f"{model_name}.pt"

        if not model_path.exists():
            raise FileNotFoundError(
                f"Model {model_name} not found in {self.models_dir / model_type}. "
                f"Available models: {self.list_available_models(model_type).get(model_type, [])}"
            )

        try:
            checkpoint = torch.load(model_path, map_location=map_location)
            return checkpoint
        except Exception as e:
            raise RuntimeError(f"Failed to load model {model_name}: {e}") from e

    def load_torchvision_model(
        self,
        model_name: str,
        map_location: str = "cpu"
    ) -> Optional[torch.nn.Module]:
        """Load a torchvision model and restore its state dict.

        Args:
            model_name: Name of torchvision model (e.g., 'resnet50')
            map_location: Device to load model on

        Returns:
            Loaded model with pretrained weights
        """
        try:
            import torchvision.models as models
        except ImportError:
            raise ImportError("torchvision not available. Install with: pip install torchvision")

        # Get model constructor
        model_fn = getattr(models, model_name, None)
        if model_fn is None:
            raise ValueError(f"Unknown torchvision model: {model_name}")

        # Load state dict
        checkpoint = self.load_model(model_name, model_type="classification", map_location=map_location)
        
        # Create model and load weights
        model = model_fn(pretrained=False)  # Don't download, we have the weights
        if isinstance(checkpoint, dict):
            if 'state_dict' in checkpoint:
                model.load_state_dict(checkpoint['state_dict'])
            elif 'model_state_dict' in checkpoint:
                model.load_state_dict(checkpoint['model_state_dict'])
            else:
                # Assume it's a state dict
                model.load_state_dict(checkpoint)
        else:
            model.load_state_dict(checkpoint)

        model.eval()
        return model

    def get_model_info(self, model_name: str, model_type: str = "classification") -> Dict[str, Any]:
        """Get metadata about a model.

        Args:
            model_name: Name of the model
            model_type: Type/category of model

        Returns:
            Dictionary with model metadata
        """
        model_path = self.models_dir / model_type / f"{model_name}.pth"
        if not model_path.exists():
            model_path = self.models_dir / model_type / f"{model_name}.pt"

        if not model_path.exists():
            return {}

        info = {
            'name': model_name,
            'type': model_type,
            'path': str(model_path),
            'size_mb': model_path.stat().st_size / (1024 * 1024),
            'exists': True
        }

        # Try to load and get additional info
        try:
            checkpoint = torch.load(model_path, map_location='cpu')
            if isinstance(checkpoint, dict):
                if 'model_name' in checkpoint:
                    info['original_name'] = checkpoint['model_name']
                if 'processor' in checkpoint:
                    info['has_processor'] = True
        except Exception:
            pass

        return info


def load_model_from_registry(
    model_name: str,
    category: str,
    models_dir: Union[str, Path] = "models"
) -> Optional[torch.nn.Module]:
    """Convenience function to load a model from the registry.

    Args:
        model_name: Name of the model
        category: Model category
        models_dir: Root directory containing models

    Returns:
        Loaded model
    """
    loader = ModelLoader(models_dir)
    return loader.load_model(model_name, category)


if __name__ == "__main__":
    import sys

    loader = ModelLoader()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            category = sys.argv[2] if len(sys.argv) > 2 else None
            models = loader.list_available_models(category)
            print("Available models:")
            for cat, model_list in models.items():
                print(f"\n{cat}:")
                for model in model_list:
                    print(f"  - {model}")
        else:
            model_name = sys.argv[1]
            model_type = sys.argv[2] if len(sys.argv) > 2 else "classification"
            model = loader.load_model(model_name, model_type)
            print(f"Loaded model: {model_name} ({type(model)})")
    else:
        print("Usage:")
        print("  python model_loader.py list [category]")
        print("  python model_loader.py <model_name> [model_type]")

