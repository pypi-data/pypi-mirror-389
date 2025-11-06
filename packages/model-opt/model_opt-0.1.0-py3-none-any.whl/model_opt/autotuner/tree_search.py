"""Monte Carlo Tree Search for compression strategy optimization."""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

from .search_space import (
    ArchitectureFamily,
    CompressionTechnique,
    ModelSignature,
    CompressionResult,
)


class CompressionTreeSearch:
    """Monte Carlo Tree Search for compression strategy."""

    def __init__(
        self,
        knowledge_base_path: str = "compression_kb.json",
        storage_backend: Optional[Any] = None
    ):
        """Initialize CompressionTreeSearch.

        Args:
            knowledge_base_path: Path to JSON file for knowledge base storage (fallback).
            storage_backend: Optional storage backend (MongoDB, Redis, etc.).
        """
        self.kb_path = Path(knowledge_base_path)
        self.storage_backend = storage_backend
        self.knowledge_base = self._load_kb()
        self.root = None

    def _load_kb(self) -> Dict:
        """Load knowledge base from storage backend or disk.

        Returns:
            Dictionary containing cached compression results.
        """
        # Try storage backend first (only if it's not a string/file path)
        if self.storage_backend is not None and not isinstance(self.storage_backend, str):
            try:
                # Load all entries from storage backend
                keys = self.storage_backend.list_keys()
                kb = {}
                for key in keys:
                    value = self.storage_backend.load(key)
                    if value:
                        kb[key] = value
                if kb:
                    return kb
            except Exception as e:
                print(f"Warning: Could not load from storage backend: {e}")
        
        # Fallback to JSON file
        if self.kb_path.exists():
            try:
                with open(self.kb_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load knowledge base: {e}")
                return {}
        return {}

    def _save_kb(self):
        """Save knowledge base to storage backend or disk."""
        # Try storage backend first (only if it's not a string/file path)
        if self.storage_backend is not None and not isinstance(self.storage_backend, str):
            try:
                # Save all entries to storage backend
                for key, value in self.knowledge_base.items():
                    self.storage_backend.save(key, value)
                return
            except Exception as e:
                print(f"Warning: Could not save to storage backend: {e}")
        
        # Fallback to JSON file
        try:
            self.kb_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.kb_path, 'w') as f:
                json.dump(self.knowledge_base, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save knowledge base: {e}")

    def lookup(self, signature: ModelSignature) -> Optional[CompressionResult]:
        """Fast lookup in knowledge base.

        Args:
            signature: Model signature to look up.

        Returns:
            CompressionResult if found, None otherwise.
        """
        key = signature.to_hash()

        if key in self.knowledge_base:
            cached = self.knowledge_base[key]
            return CompressionResult(
                techniques=[CompressionTechnique(t) for t in cached['techniques']],
                speedup=cached['speedup'],
                compression_ratio=cached['compression_ratio'],
                accuracy_drop=cached['accuracy_drop'],
                memory_reduction=cached['memory_reduction'],
                inference_time_ms=cached['inference_time_ms']
            )

        return None

    def recommend_techniques(
        self,
        signature: ModelSignature,
        constraints: Optional[Dict[str, float]] = None
    ) -> List[CompressionTechnique]:
        """Recommend compression techniques based on tree search.

        Args:
            signature: Model signature for recommendation.
            constraints: Optional constraints dict with keys like 'max_accuracy_drop'.

        Returns:
            List of recommended CompressionTechnique enums.
        """
        techniques = []

        # Architecture-specific rules (learned from papers)
        if signature.family == ArchitectureFamily.CNN:
            techniques.append(CompressionTechnique.QUANTIZE_INT8)
            techniques.append(CompressionTechnique.PRUNE_STRUCTURED_30)
            techniques.append(CompressionTechnique.FUSE_LAYERS)

        elif signature.family == ArchitectureFamily.VIT:
            techniques.append(CompressionTechnique.TOKEN_MERGE_30)
            techniques.append(CompressionTechnique.QUANTIZE_INT8)
            techniques.append(CompressionTechnique.SVD_50)

        elif signature.family == ArchitectureFamily.HYBRID:
            if signature.has_conv:
                techniques.append(CompressionTechnique.PRUNE_STRUCTURED_30)
            if signature.has_attention:
                techniques.append(CompressionTechnique.TOKEN_MERGE_30)
            techniques.append(CompressionTechnique.QUANTIZE_INT8)

        elif signature.family == ArchitectureFamily.DIFFUSION:
            techniques.append(CompressionTechnique.TOKEN_MERGE_30)
            techniques.append(CompressionTechnique.QUANTIZE_INT8)

        # Size-based rules
        if signature.total_params > 100_000_000:
            # Large models: aggressive compression
            if CompressionTechnique.PRUNE_STRUCTURED_30 in techniques:
                techniques.remove(CompressionTechnique.PRUNE_STRUCTURED_30)
                techniques.append(CompressionTechnique.PRUNE_STRUCTURED_50)

        # Apply constraints
        if constraints:
            techniques = self._filter_by_constraints(techniques, constraints)

        return techniques

    def update_knowledge_base(
        self,
        signature: ModelSignature,
        result: CompressionResult
    ):
        """Update KB with new result (public contribution).

        Args:
            signature: Model signature for the result.
            result: CompressionResult to store.
        """
        key = signature.to_hash()

        # Store result
        self.knowledge_base[key] = {
            'techniques': [t.value for t in result.techniques],
            'speedup': result.speedup,
            'compression_ratio': result.compression_ratio,
            'accuracy_drop': result.accuracy_drop,
            'memory_reduction': result.memory_reduction,
            'inference_time_ms': result.inference_time_ms,
            'timestamp': time.time()
        }

        # Save to disk
        self._save_kb()

        print(f"✓ Updated knowledge base: {key}")
        print(f"  Techniques: {[t.value for t in result.techniques]}")
        print(f"  Speedup: {result.speedup:.2f}x")
        print(f"  Accuracy drop: {result.accuracy_drop:.2%}")

    def _filter_by_constraints(
        self,
        techniques: List[CompressionTechnique],
        constraints: Dict[str, float]
    ) -> List[CompressionTechnique]:
        """Filter techniques that violate constraints.

        Args:
            techniques: List of techniques to filter.
            constraints: Constraint dictionary with keys like 'max_accuracy_drop'.

        Returns:
            Filtered list of techniques.
        """
        # Estimate which techniques might violate constraints
        # (Simple heuristic - can be refined)
        max_acc_drop = constraints.get('max_accuracy_drop', 0.05)

        if max_acc_drop < 0.02:
            # Conservative: avoid aggressive techniques
            aggressive = [
                CompressionTechnique.QUANTIZE_INT4,
                CompressionTechnique.PRUNE_STRUCTURED_50
            ]
            techniques = [t for t in techniques if t not in aggressive]

        return techniques

