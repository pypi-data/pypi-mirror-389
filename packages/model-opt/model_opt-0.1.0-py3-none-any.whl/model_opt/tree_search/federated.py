"""Federated storage integration with confidence-weighted merging."""
from typing import Dict, List, Optional, Any
from model_opt.core.storage.base import StorageBackend
from model_opt.autotuner.search_space import (
    ModelSignature,
    CompressionResult,
    CompressionTechnique,
)


class FederatedStorage:
    """Federated storage with confidence-weighted merging."""
    
    def __init__(self, storage_backend: Optional[StorageBackend] = None):
        """Initialize federated storage.
        
        Args:
            storage_backend: Optional storage backend (MongoDB, Redis, etc.)
        """
        self.storage_backend = storage_backend
        self._local_cache: Dict[str, Dict] = {}
    
    def get_federated_prior(
        self,
        signature: ModelSignature,
        technique: CompressionTechnique
    ) -> Optional[float]:
        """Get federated prior probability for a technique.
        
        Args:
            signature: Model signature
            technique: Compression technique
            
        Returns:
            Prior probability (0.0 to 1.0) or None if not found
        """
        key = self._make_key(signature, technique)
        
        # Check local cache first
        if key in self._local_cache:
            entry = self._local_cache[key]
            sample_count = entry.get('sample_count', 0)
            if sample_count >= 3:  # Require at least 3 samples
                return entry.get('success_rate', None)
        
        # Check storage backend
        if self.storage_backend:
            try:
                entry = self.storage_backend.load(key)
                if entry:
                    sample_count = entry.get('sample_count', 0)
                    if sample_count >= 3:
                        self._local_cache[key] = entry
                        return entry.get('success_rate', None)
            except Exception:
                pass
        
        return None
    
    def update_result(
        self,
        signature: ModelSignature,
        technique: CompressionTechnique,
        result: CompressionResult,
        success_threshold: float = 0.95  # Speedup > 1.5x and accuracy drop < 5%
    ):
        """Update federated storage with new result.
        
        Args:
            signature: Model signature
            technique: Compression technique
            result: Compression result
            success_threshold: Threshold for considering result successful
        """
        key = self._make_key(signature, technique)
        
        # Determine if result is successful
        is_success = (
            result.speedup >= 1.5 and
            result.accuracy_drop <= 0.05 and
            result.compression_ratio >= 1.5
        )
        
        # Get existing entry
        entry = self._local_cache.get(key, {
            'success_count': 0,
            'total_count': 0,
            'sample_count': 0,
            'success_rate': 0.0
        })
        
        # Update statistics
        entry['total_count'] += 1
        entry['sample_count'] += 1
        if is_success:
            entry['success_count'] += 1
        
        # Calculate success rate
        entry['success_rate'] = entry['success_count'] / entry['total_count'] if entry['total_count'] > 0 else 0.0
        
        # Store average metrics
        if 'avg_speedup' not in entry:
            entry['avg_speedup'] = result.speedup
            entry['avg_compression'] = result.compression_ratio
            entry['avg_accuracy_drop'] = result.accuracy_drop
        else:
            # Running average
            n = entry['sample_count']
            entry['avg_speedup'] = (entry['avg_speedup'] * (n - 1) + result.speedup) / n
            entry['avg_compression'] = (entry['avg_compression'] * (n - 1) + result.compression_ratio) / n
            entry['avg_accuracy_drop'] = (entry['avg_accuracy_drop'] * (n - 1) + result.accuracy_drop) / n
        
        # Update cache
        self._local_cache[key] = entry
        
        # Persist to storage backend
        if self.storage_backend:
            try:
                self.storage_backend.save(key, entry)
            except Exception:
                pass
    
    def merge_results(
        self,
        signature: ModelSignature,
        results: List[Dict[str, Any]]
    ) -> Optional[CompressionResult]:
        """Merge multiple results with confidence weighting.
        
        Args:
            signature: Model signature
            results: List of result dictionaries with confidence scores
            
        Returns:
            Merged CompressionResult or None
        """
        if not results:
            return None
        
        # Weight by confidence and sample count
        total_weight = sum(
            r.get('confidence', 0.5) * max(1, r.get('sample_count', 0))
            for r in results
        )
        
        if total_weight == 0:
            return None
        
        # Weighted average
        weighted_speedup = sum(
            r.get('speedup', 0) * r.get('confidence', 0.5) * max(1, r.get('sample_count', 0))
            for r in results
        ) / total_weight
        
        weighted_compression = sum(
            r.get('compression_ratio', 0) * r.get('confidence', 0.5) * max(1, r.get('sample_count', 0))
            for r in results
        ) / total_weight
        
        weighted_accuracy_drop = sum(
            r.get('accuracy_drop', 0) * r.get('confidence', 0.5) * max(1, r.get('sample_count', 0))
            for r in results
        ) / total_weight
        
        # Get most common techniques
        all_techniques = []
        for r in results:
            techs = r.get('techniques', [])
            if isinstance(techs, list):
                all_techniques.extend(techs)
        
        # Count occurrences
        technique_counts = {}
        for tech in all_techniques:
            if isinstance(tech, str):
                tech = CompressionTechnique(tech)
            technique_counts[tech] = technique_counts.get(tech, 0) + 1
        
        # Get most common techniques (at least 50% of results)
        threshold = len(results) * 0.5
        common_techniques = [
            tech for tech, count in technique_counts.items()
            if count >= threshold
        ]
        
        return CompressionResult(
            techniques=common_techniques,
            speedup=weighted_speedup,
            compression_ratio=weighted_compression,
            accuracy_drop=weighted_accuracy_drop,
            memory_reduction=weighted_compression,
            inference_time_ms=0.0  # Would need to average this too
        )
    
    def get_sample_count(
        self,
        signature: ModelSignature,
        technique: CompressionTechnique
    ) -> int:
        """Get sample count for a technique signature.
        
        Args:
            signature: Model signature
            technique: Compression technique
            
        Returns:
            Sample count
        """
        key = self._make_key(signature, technique)
        entry = self._local_cache.get(key)
        if entry:
            return entry.get('sample_count', 0)
        
        if self.storage_backend:
            try:
                entry = self.storage_backend.load(key)
                if entry:
                    return entry.get('sample_count', 0)
            except Exception:
                pass
        
        return 0
    
    def _make_key(self, signature: ModelSignature, technique: CompressionTechnique) -> str:
        """Make storage key for signature and technique.
        
        Args:
            signature: Model signature
            technique: Compression technique
            
        Returns:
            Storage key
        """
        sig_hash = signature.to_hash()
        return f"{sig_hash}_{technique.value}"

