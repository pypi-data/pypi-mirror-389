"""Dataset loaders for evaluation."""
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from model_opt.core.exceptions import ModelLoadError


class DatasetLoader:
    """Load evaluation datasets."""
    
    def __init__(self, dataset_type: str, dataset_path: str):
        """Initialize dataset loader.
        
        Args:
            dataset_type: Type of dataset ('imagenet', 'coco', 'imagenet-d')
            dataset_path: Path to dataset directory
        """
        self.dataset_type = dataset_type
        self.dataset_path = Path(dataset_path)
        
        if not self.dataset_path.exists():
            raise ModelLoadError(
                f"Dataset path does not exist: {dataset_path}\n"
                f"Run: python scripts/download_datasets/download_{dataset_type}.py"
            )
    
    def load_imagenet(self, split: str = 'val') -> Tuple[Any, Any]:
        """Load ImageNet dataset.
        
        Args:
            split: Dataset split ('train', 'val')
            
        Returns:
            Tuple of (dataset, num_classes)
        """
        try:
            import torchvision
            from torchvision.datasets import ImageNet
            
            dataset = ImageNet(
                root=str(self.dataset_path.parent),
                split=split,
                transform=None  # Will be set by caller
            )
            return dataset, 1000
        except ImportError:
            raise ModelLoadError("torchvision is required for ImageNet dataset")
        except Exception as e:
            raise ModelLoadError(f"Failed to load ImageNet: {e}")
    
    def load_coco(self, split: str = 'val') -> Tuple[Any, Dict]:
        """Load COCO dataset.
        
        Args:
            split: Dataset split ('val', 'train')
            
        Returns:
            Tuple of (dataset, annotations_dict)
        """
        try:
            from pycocotools.coco import COCO
            
            annotations_file = self.dataset_path / 'annotations' / f'instances_{split}2017.json'
            if not annotations_file.exists():
                raise ModelLoadError(
                    f"COCO annotations not found: {annotations_file}\n"
                    f"Run: python scripts/download_datasets/download_coco.py"
                )
            
            coco = COCO(str(annotations_file))
            
            # Get image IDs
            img_ids = coco.getImgIds()
            
            return coco, {
                'images': img_ids,
                'num_classes': len(coco.getCatIds()),
            }
        except ImportError:
            raise ModelLoadError("pycocotools is required for COCO dataset")
        except Exception as e:
            raise ModelLoadError(f"Failed to load COCO: {e}")
    
    def load(self, split: str = 'val') -> Tuple[Any, Dict]:
        """Load dataset based on type.
        
        Args:
            split: Dataset split
            
        Returns:
            Tuple of (dataset, metadata)
        """
        if self.dataset_type == 'imagenet':
            dataset, num_classes = self.load_imagenet(split)
            return dataset, {'num_classes': num_classes, 'type': 'classification'}
        elif self.dataset_type == 'coco':
            dataset, metadata = self.load_coco(split)
            return dataset, {**metadata, 'type': 'detection'}
        elif self.dataset_type == 'imagenet-d':
            # ImageNet-D robustness dataset
            return self.load_imagenet_d(split)
        else:
            raise ModelLoadError(f"Unknown dataset type: {self.dataset_type}")
    
    def load_imagenet_d(self, split: str = 'val') -> Tuple[Any, Dict]:
        """Load ImageNet-D robustness dataset.
        
        Args:
            split: Dataset split
            
        Returns:
            Tuple of (dataset, metadata)
        """
        # Placeholder - would load robustness variants
        try:
            import torchvision
            # For now, fall back to regular ImageNet
            dataset, num_classes = self.load_imagenet(split)
            return dataset, {
                'num_classes': num_classes,
                'type': 'classification',
                'robustness': True
            }
        except Exception as e:
            raise ModelLoadError(f"Failed to load ImageNet-D: {e}")

