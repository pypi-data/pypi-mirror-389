"""Architecture-specific priors for MCTS initialization."""
from typing import Dict, Optional
from model_opt.autotuner.search_space import (
    ArchitectureFamily,
    CompressionTechnique,
    ModelSignature,
)


class ArchitecturePriors:
    """Architecture-specific prior probabilities for compression techniques."""
    
    def __init__(self):
        """Initialize priors based on architecture families."""
        # Convert existing rule-based recommendations to probability distributions
        self._priors = {
            ArchitectureFamily.CNN: {
                CompressionTechnique.QUANTIZE_INT8: 0.8,
                CompressionTechnique.PRUNE_STRUCTURED_30: 0.7,
                CompressionTechnique.PRUNE_STRUCTURED_50: 0.4,
                CompressionTechnique.FUSE_LAYERS: 0.9,
                CompressionTechnique.QUANTIZE_INT4: 0.2,
                CompressionTechnique.SVD_50: 0.3,
                CompressionTechnique.TOKEN_MERGE_30: 0.1,
            },
            ArchitectureFamily.VIT: {
                CompressionTechnique.TOKEN_MERGE_30: 0.8,
                CompressionTechnique.QUANTIZE_INT8: 0.6,
                CompressionTechnique.SVD_50: 0.7,
                CompressionTechnique.PRUNE_STRUCTURED_30: 0.3,
                CompressionTechnique.FUSE_LAYERS: 0.2,
                CompressionTechnique.QUANTIZE_INT4: 0.2,
            },
            ArchitectureFamily.HYBRID: {
                CompressionTechnique.QUANTIZE_INT8: 0.7,
                CompressionTechnique.PRUNE_STRUCTURED_30: 0.5,
                CompressionTechnique.TOKEN_MERGE_30: 0.6,
                CompressionTechnique.SVD_50: 0.4,
                CompressionTechnique.FUSE_LAYERS: 0.5,
                CompressionTechnique.QUANTIZE_INT4: 0.2,
            },
            ArchitectureFamily.DIFFUSION: {
                CompressionTechnique.TOKEN_MERGE_30: 0.8,
                CompressionTechnique.QUANTIZE_INT8: 0.6,
                CompressionTechnique.PRUNE_STRUCTURED_30: 0.2,
                CompressionTechnique.SVD_50: 0.3,
                CompressionTechnique.FUSE_LAYERS: 0.1,
                CompressionTechnique.QUANTIZE_INT4: 0.1,
            },
        }
    
    def get_priors(
        self,
        signature: ModelSignature,
        constraints: Optional[Dict] = None
    ) -> Dict[CompressionTechnique, float]:
        """Get prior probabilities for compression techniques.
        
        Args:
            signature: Model signature
            constraints: Optional constraints dict
            
        Returns:
            Dictionary mapping techniques to prior probabilities
        """
        base_priors = self._priors.get(signature.family, {})
        
        # Adjust based on model size
        if signature.total_params > 100_000_000:
            # Large models: favor more aggressive compression
            adjusted_priors = {}
            for tech, prob in base_priors.items():
                if tech == CompressionTechnique.PRUNE_STRUCTURED_50:
                    adjusted_priors[tech] = min(1.0, prob * 1.5)
                elif tech == CompressionTechnique.PRUNE_STRUCTURED_30:
                    adjusted_priors[tech] = prob * 0.8
                else:
                    adjusted_priors[tech] = prob
            base_priors = adjusted_priors
        
        # Apply constraints
        if constraints:
            max_acc_drop = constraints.get('max_accuracy_drop', 1.0)
            if max_acc_drop < 0.02:
                # Conservative: reduce aggressive techniques
                for tech in [CompressionTechnique.QUANTIZE_INT4, CompressionTechnique.PRUNE_STRUCTURED_50]:
                    if tech in base_priors:
                        base_priors[tech] *= 0.3
        
        # Normalize probabilities (softmax-like, but keep relative)
        max_prob = max(base_priors.values()) if base_priors else 1.0
        if max_prob > 0:
            normalized = {tech: prob / max_prob for tech, prob in base_priors.items()}
        else:
            normalized = base_priors
        
        return normalized
    
    def get_technique_prior(
        self,
        signature: ModelSignature,
        technique: CompressionTechnique
    ) -> float:
        """Get prior probability for a specific technique.
        
        Args:
            signature: Model signature
            technique: Compression technique
            
        Returns:
            Prior probability (0.0 to 1.0)
        """
        priors = self.get_priors(signature)
        return priors.get(technique, 0.1)  # Default to low prior if not in list
    
    def update_prior(
        self,
        family: ArchitectureFamily,
        technique: CompressionTechnique,
        probability: float
    ):
        """Update prior probability (for learning from results).
        
        Args:
            family: Architecture family
            technique: Compression technique
            probability: New prior probability (0.0 to 1.0)
        """
        if family not in self._priors:
            self._priors[family] = {}
        self._priors[family][technique] = max(0.0, min(1.0, probability))

