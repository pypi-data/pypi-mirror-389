"""Evaluation metrics for model optimization."""
from typing import Dict, List, Optional, Any
import numpy as np
from model_opt.core.exceptions import ModelLoadError


class MetricCalculator:
    """Base class for metric calculation."""
    
    def calculate(self, predictions: Any, targets: Any) -> Dict[str, float]:
        """Calculate metrics.
        
        Args:
            predictions: Model predictions
            targets: Ground truth targets
            
        Returns:
            Dictionary of metric name -> value
        """
        raise NotImplementedError


class ClassificationMetrics(MetricCalculator):
    """Classification metrics (accuracy, top-k accuracy, etc.)."""
    
    def calculate(
        self,
        predictions: np.ndarray,
        targets: np.ndarray,
        top_k: List[int] = [1, 5]
    ) -> Dict[str, float]:
        """Calculate classification metrics.
        
        Args:
            predictions: Predicted class probabilities (N, C)
            targets: Ground truth class indices (N,)
            top_k: List of k values for top-k accuracy
            
        Returns:
            Dictionary of metrics
        """
        if predictions.ndim == 2:
            # Get predicted classes
            pred_classes = np.argmax(predictions, axis=1)
        else:
            pred_classes = predictions
        
        # Top-1 accuracy
        correct = (pred_classes == targets).sum()
        accuracy = correct / len(targets)
        
        metrics = {'accuracy': float(accuracy)}
        
        # Top-k accuracy
        if predictions.ndim == 2:
            for k in top_k:
                if k == 1:
                    continue
                top_k_correct = 0
                for i, target in enumerate(targets):
                    top_k_preds = np.argsort(predictions[i])[-k:][::-1]
                    if target in top_k_preds:
                        top_k_correct += 1
                metrics[f'top_{k}_accuracy'] = float(top_k_correct / len(targets))
        
        return metrics


class DetectionMetrics(MetricCalculator):
    """Detection metrics (mAP, etc.) using pycocotools."""
    
    def calculate(
        self,
        predictions: List[Dict],
        coco_gt: Any,
        coco_dt: Optional[Any] = None
    ) -> Dict[str, float]:
        """Calculate detection metrics.
        
        Args:
            predictions: List of prediction dictionaries
            coco_gt: COCO ground truth object
            coco_dt: Optional COCO detection object (will be created if None)
            
        Returns:
            Dictionary of metrics
        """
        try:
            from pycocotools.cocoeval import COCOeval
            
            # Create COCO detection object if needed
            if coco_dt is None:
                import json
                from pycocotools.coco import COCO
                
                # Convert predictions to COCO format
                coco_dt = coco_gt.loadRes(predictions)
            
            # Evaluate
            coco_eval = COCOeval(coco_gt, coco_dt, 'bbox')
            coco_eval.evaluate()
            coco_eval.accumulate()
            coco_eval.summarize()
            
            metrics = {
                'mAP': float(coco_eval.stats[0]),  # mAP @ IoU=0.50:0.95
                'mAP_50': float(coco_eval.stats[1]),  # mAP @ IoU=0.50
                'mAP_75': float(coco_eval.stats[2]),  # mAP @ IoU=0.75
                'mAP_small': float(coco_eval.stats[3]),  # mAP for small objects
                'mAP_medium': float(coco_eval.stats[4]),  # mAP for medium objects
                'mAP_large': float(coco_eval.stats[5]),  # mAP for large objects
            }
            
            return metrics
        except ImportError:
            raise ModelLoadError("pycocotools is required for detection metrics")
        except Exception as e:
            raise ModelLoadError(f"Failed to calculate detection metrics: {e}")

