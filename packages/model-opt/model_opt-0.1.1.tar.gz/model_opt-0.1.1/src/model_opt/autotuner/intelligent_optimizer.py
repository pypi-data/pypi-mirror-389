"""Intelligent optimizer with automatic compression strategy selection."""

from typing import Dict, Optional, Tuple, Any, Literal, List
import time

try:
    import torch
    import torch.nn as nn
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False

import numpy as np

from .search_space import (
    ArchitectureFamily,
    CompressionTechnique,
    ModelSignature,
    CompressionResult,
)
from .tree_search import CompressionTreeSearch
from model_opt.techniques.quantize import Quantizer
from model_opt.techniques.prune import Pruner
from model_opt.techniques.decompose import Decomposer
from model_opt.techniques.fuse import LayerFuser

# Optional MCTS import
try:
    from model_opt.tree_search import MCTSEngine
    _MCTS_AVAILABLE = True
except ImportError:
    _MCTS_AVAILABLE = False


class IntelligentOptimizer:
    """Main optimizer with tree search autotuning."""

    def __init__(
        self,
        knowledge_base_path: Optional[str] = None,
        storage_backend: Optional[Any] = None,
        use_federated_api: bool = False,
        federated_api_url: Optional[str] = None,
        federated_api_key: Optional[str] = None
    ):
        """Initialize IntelligentOptimizer.

        Args:
            knowledge_base_path: Optional path to knowledge base JSON file.
                If None, uses default 'compression_kb.json' in current directory.
            storage_backend: Optional storage backend for federated learning (MongoDB, Redis, etc.)
            use_federated_api: If True, use federated tree API (default: False)
            federated_api_url: Optional API URL override (defaults to config value)
            federated_api_key: Optional API key override (defaults to config value)
        """
        if not _TORCH_AVAILABLE:
            raise ImportError("PyTorch is required for IntelligentOptimizer")

        kb_path = knowledge_base_path or "compression_kb.json"
        self.tree_search = CompressionTreeSearch(
            knowledge_base_path=kb_path,
            storage_backend=storage_backend
        )
        self.quantizer = Quantizer()
        self.pruner = Pruner()
        self.decomposer = Decomposer()
        self.fuser = LayerFuser()
        self.storage_backend = storage_backend
        self._mcts_engine: Optional[MCTSEngine] = None
        
        # Initialize federated tree manager
        # Priority: API client > file path > storage backend
        self._federated_tree_manager = None
        self._federated_tree_file_path = None
        
        # Check if storage_backend is a file path string (for testing/fallback)
        if isinstance(storage_backend, str) and storage_backend.endswith('.json'):
            self._federated_tree_file_path = storage_backend
            storage_backend = None  # Use file-based instead
        
        # Initialize API client if requested
        api_client = None
        if use_federated_api or federated_api_url:
            try:
                from model_opt.tree_search.federated import FederatedAPIClient
                from model_opt.core.config import FEDERATED_API_CONFIG
                
                # Use provided URL/key or fall back to config
                api_url = federated_api_url or FEDERATED_API_CONFIG['base_url']
                api_key = federated_api_key or FEDERATED_API_CONFIG['api_key']
                
                api_client = FederatedAPIClient(
                    base_url=api_url,
                    api_key=api_key,
                    timeout=FEDERATED_API_CONFIG['timeout']
                )
            except ImportError:
                # httpx or API client not available
                pass
            except Exception as e:
                # API client initialization failed, will fall back to file-based
                print(f"Warning: Failed to initialize federated API client: {e}")
                api_client = None
        
        # Initialize federated tree manager if API client, file path, or storage backend is available
        if api_client is not None or storage_backend is not None or self._federated_tree_file_path is not None:
            try:
                from model_opt.tree_search.federated import FederatedTreeManager
                
                if api_client is not None:
                    # Use API client (highest priority)
                    self._federated_tree_manager = FederatedTreeManager(
                        storage_backend=None,
                        vector_db=None,
                        api_client=api_client,
                        use_api=False  # Already have client, don't initialize again
                    )
                else:
                    # Use file path or storage backend
                    self._federated_tree_manager = FederatedTreeManager(
                        storage_backend=storage_backend,
                        vector_db=None,
                        file_path=self._federated_tree_file_path,
                        use_api=False
                    )
            except ImportError:
                # Federated tree operations not available
                pass

    def optimize_auto(
        self,
        model: Any,
        constraints: Optional[Dict[str, float]] = None,
        example_input: Optional[Any] = None,
        method: Literal['rule', 'mcts', 'hybrid'] = 'hybrid',
        n_simulations: int = 50,
        timeout_seconds: float = 300.0
    ) -> Tuple[Any, CompressionResult]:
        """Automatic optimization using tree search or MCTS.

        Args:
            model: PyTorch model to optimize.
            constraints: Optional constraints dict with keys like 'max_accuracy_drop'.
            example_input: Optional example input tensor for benchmarking and pruning.
                If None, will attempt to create a dummy input.
            method: Optimization method - 'hybrid' (default), 'rule', or 'mcts'.
            n_simulations: Number of MCTS simulations (only for 'mcts' or 'hybrid').
            timeout_seconds: Maximum time for MCTS search (only for 'mcts' or 'hybrid').

        Returns:
            Tuple of (optimized_model, CompressionResult).

        Raises:
            RuntimeError: If model is not a PyTorch model.
            ImportError: If MCTS is requested but not available.
        """
        if not isinstance(model, nn.Module):
            raise RuntimeError("IntelligentOptimizer only supports PyTorch models")

        # Step 1: Analyze model and create signature
        print("🔍 Analyzing model architecture...")
        signature = self._create_signature(model)
        print(f"  Family: {signature.family.value}")
        print(f"  Parameters: {signature.total_params:,}")

        # Step 2: Select optimization method
        if method in ('mcts', 'hybrid') and not _MCTS_AVAILABLE:
            print("⚠ MCTS not available, falling back to rule-based method")
            method = 'rule'
        
        # Step 3: Get compression strategy
        if method == 'mcts':
            print("\n🎯 Using MCTS search...")
            techniques, result = self._optimize_mcts(
                model, signature, constraints, example_input,
                n_simulations, timeout_seconds
            )
            print(f"  MCTS recommended: {[t.value for t in techniques]}")
        elif method == 'hybrid':
            print("\n🎯 Using hybrid (Federated tree + cache + MCTS)...")
            # First try federated tree lookup (rule-based from federated knowledge)
            cached = None
            if self._federated_tree_manager is not None:
                cached = self._lookup_federated_tree(signature, constraints)
                if cached:
                    print(f"✓ Found result in federated tree!")
                    techniques = cached.techniques
                    result = cached
                else:
                    print("  No match in federated tree, checking local cache...")
            
            # If federated tree lookup failed, try local cache
            if cached is None:
                cached = self.tree_search.lookup(signature)
                if cached:
                    print(f"✓ Found cached result!")
                    techniques = cached.techniques
                    result = cached
            
            # If both failed, use MCTS for exploration
            if cached is None:
                print("  No cached results, using MCTS exploration...")
                techniques, result = self._optimize_mcts(
                    model, signature, constraints, example_input,
                    n_simulations, timeout_seconds
                )
        else:  # method == 'rule'
            print("\n📚 Checking knowledge base...")
            cached = self.tree_search.lookup(signature)

            if cached:
                print(f"✓ Found cached result!")
                print(f"  Speedup: {cached.speedup:.2f}x")
                print(f"  Accuracy drop: {cached.accuracy_drop:.2%}")
                print(f"  Using techniques: {[t.value for t in cached.techniques]}")
                techniques = cached.techniques
                result = None  # Will be computed after applying techniques
            else:
                print("⚠ No cached result, using learned rules...")
                techniques = self.tree_search.recommend_techniques(signature, constraints)
                print(f"  Recommended: {[t.value for t in techniques]}")
                result = None

        # Step 4: Apply techniques sequentially
        print("\n⚡ Applying optimizations...")
        original_size = self._get_model_size(model)
        current_model = model
        
        for technique in techniques:
            print(f"  Applying {technique.value}...")
            try:
                current_model = self._apply_technique(
                    current_model,
                    technique,
                    example_input=example_input
                )
            except Exception as e:
                print(f"  ⚠ Warning: Failed to apply {technique.value}: {e}")
                continue

        # Step 5: Benchmark (if not already evaluated by MCTS)
        if result is None:
            print("\n📊 Benchmarking results...")
            if example_input is None:
                example_input = self._create_dummy_input(model)
            result = self._benchmark_model(current_model, original_size, example_input)
            result.techniques = techniques

        # Step 6: Update knowledge base
        print("\n💾 Updating knowledge base...")
        self.tree_search.update_knowledge_base(signature, result)

        return current_model, result
    
    def _optimize_mcts(
        self,
        model: nn.Module,
        signature: ModelSignature,
        constraints: Optional[Dict[str, float]],
        example_input: Optional[Any],
        n_simulations: int,
        timeout_seconds: float
    ) -> Tuple[list, CompressionResult]:
        """Optimize using MCTS engine.
        
        Args:
            model: PyTorch model
            signature: Model signature
            constraints: Optional constraints
            example_input: Optional example input
            n_simulations: Number of MCTS simulations
            timeout_seconds: Maximum time for search
            
        Returns:
            Tuple of (techniques, result)
        """
        if not _MCTS_AVAILABLE:
            raise ImportError("MCTS engine not available. Install tree_search module.")
        
        # Initialize MCTS engine if needed
        if self._mcts_engine is None:
            self._mcts_engine = MCTSEngine(
                tree_search=self.tree_search,
                storage_backend=self.storage_backend,
                n_simulations=n_simulations,
                timeout_seconds=timeout_seconds
            )
        
        # Run MCTS search
        techniques, result = self._mcts_engine.search(
            model,
            signature,
            constraints=constraints,
            example_input=example_input
        )
        
        return techniques, result

    def _lookup_federated_tree(
        self,
        signature: ModelSignature,
        constraints: Optional[Dict[str, float]] = None
    ) -> Optional[CompressionResult]:
        """Lookup compression strategy from federated tree.
        
        Args:
            signature: Model signature for lookup
            constraints: Optional constraints dict
            
        Returns:
            CompressionResult if found, None otherwise
        """
        if self._federated_tree_manager is None:
            return None
        
        try:
            # Convert signature family to architecture family string
            arch_family_map = {
                ArchitectureFamily.CNN: "CNN",
                ArchitectureFamily.VIT: "ViT",
                ArchitectureFamily.HYBRID: "Hybrid",
                ArchitectureFamily.DIFFUSION: "Diffusion"
            }
            architecture_family = arch_family_map.get(signature.family, "CNN")
            
            # Prepare user constraints for tree filtering
            user_constraints = {}
            if constraints:
                if 'max_accuracy_drop' in constraints:
                    user_constraints['min_accuracy_retention'] = 1.0 - constraints['max_accuracy_drop']
            
            # Initialize local tree from federated tree
            local_tree = self._federated_tree_manager.initialize_local_tree(
                architecture_family=architecture_family,
                user_constraints=user_constraints
            )
            
            if local_tree is None or local_tree.number_of_nodes() == 0:
                return None
            
            # Find best matching node
            best_node = self._find_best_matching_node(local_tree, signature, constraints)
            
            if best_node is None:
                return None
            
            # Extract techniques from node
            techniques = self._extract_techniques_from_node(best_node)
            
            if not techniques:
                return None
            
            # Create CompressionResult from node performance data
            node_data = best_node[1] if isinstance(best_node, tuple) else best_node
            performance = node_data.get('performance', {})
            
            result = CompressionResult(
                techniques=techniques,
                speedup=performance.get('latency_speedup', 1.0),
                compression_ratio=performance.get('compression_ratio', 1.0),
                accuracy_drop=1.0 - performance.get('accuracy_retention', 1.0),
                memory_reduction=performance.get('compression_ratio', 1.0),
                inference_time_ms=0.0  # Not available from federated tree
            )
            
            return result
            
        except Exception as e:
            print(f"  ⚠ Federated tree lookup failed: {e}")
            return None
    
    def _find_best_matching_node(
        self,
        tree,
        signature: ModelSignature,
        constraints: Optional[Dict[str, float]] = None
    ):
        """Find best matching node in tree.
        
        Args:
            tree: NetworkX DiGraph
            signature: Model signature
            constraints: Optional constraints
            
        Returns:
            Best matching node (node_id, node_data) or None
        """
        best_node = None
        best_score = 0.0
        
        for node_id, node_data in tree.nodes(data=True):
            score = 0.0
            
            # Architecture match score
            arch = node_data.get('architecture', {})
            node_family = arch.get('family', '').lower()
            sig_family = signature.family.value.lower()
            
            if node_family == sig_family:
                score += 2.0  # Exact match
            elif sig_family in node_family or node_family in sig_family:
                score += 1.0  # Partial match
            
            # Validation confidence score
            validation = node_data.get('validation', {})
            confidence = validation.get('confidence', 0.0)
            sample_count = validation.get('sample_count', 0)
            score += confidence * 2.0
            score += min(sample_count / 10.0, 1.0)  # Cap at 10 samples
            
            # Constraint satisfaction
            if constraints:
                performance = node_data.get('performance', {})
                if 'max_accuracy_drop' in constraints:
                    acc_retention = performance.get('accuracy_retention', 1.0)
                    acc_drop = 1.0 - acc_retention
                    if acc_drop <= constraints['max_accuracy_drop']:
                        score += 1.0
                    else:
                        score -= 2.0  # Penalize constraint violations
            
            if score > best_score:
                best_score = score
                best_node = (node_id, node_data)
        
        return best_node if best_score > 0.0 else None
    
    def _extract_techniques_from_node(self, node) -> List[CompressionTechnique]:
        """Extract CompressionTechnique list from federated tree node.
        
        Args:
            node: Node tuple (node_id, node_data) or node_data dict
            
        Returns:
            List of CompressionTechnique enums
        """
        if isinstance(node, tuple):
            node_data = node[1]
        else:
            node_data = node
        
        techniques = []
        compression_config = node_data.get('compression_config', {})
        
        # Map compression_config keys to CompressionTechnique enums
        # The config may contain technique names or parameters
        config_keys = compression_config.keys() if isinstance(compression_config, dict) else []
        config_str = str(compression_config).lower()
        
        # Check for quantization
        if 'quantize' in config_str or 'quantization' in config_str:
            if 'int8' in config_str or compression_config.get('bits') == 8:
                techniques.append(CompressionTechnique.QUANTIZE_INT8)
            elif 'int4' in config_str or compression_config.get('bits') == 4:
                techniques.append(CompressionTechnique.QUANTIZE_INT4)
            elif 'fp8' in config_str:
                techniques.append(CompressionTechnique.QUANTIZE_FP8)
        
        # Check for pruning
        if 'prune' in config_str or 'pruning' in config_str:
            if 'structured' in config_str:
                ratio = compression_config.get('ratio', 0.3)
                if ratio >= 0.5:
                    techniques.append(CompressionTechnique.PRUNE_STRUCTURED_50)
                else:
                    techniques.append(CompressionTechnique.PRUNE_STRUCTURED_30)
            elif 'token' in config_str or 'merge' in config_str:
                techniques.append(CompressionTechnique.TOKEN_MERGE_30)
        
        # Check for layer fusion
        if 'fuse' in config_str or 'fusion' in config_str:
            techniques.append(CompressionTechnique.FUSE_LAYERS)
        
        # Check for SVD decomposition
        if 'svd' in config_str or 'decompose' in config_str:
            techniques.append(CompressionTechnique.SVD_50)
        
        # Fallback: Try to extract from node source or metadata
        if not techniques:
            source = node_data.get('source', {})
            paper_refs = source.get('paper_refs', [])
            if paper_refs:
                # Try to infer from paper references (simplified)
                paper_str = ' '.join(paper_refs).lower()
                if 'quantize' in paper_str or 'quantization' in paper_str:
                    techniques.append(CompressionTechnique.QUANTIZE_INT8)
                if 'prune' in paper_str or 'pruning' in paper_str:
                    techniques.append(CompressionTechnique.PRUNE_STRUCTURED_30)
        
        return techniques

    def _create_signature(self, model: nn.Module) -> ModelSignature:
        """Create model signature for search.

        Args:
            model: PyTorch model.

        Returns:
            ModelSignature with architecture characteristics.
        """
        total_params = sum(p.numel() for p in model.parameters())

        # Detect architecture family
        model_str = str(model).lower()
        class_name = model.__class__.__name__.lower()
        module_names = [name.lower() for name, _ in model.named_modules()]

        # Check for diffusion models
        has_diffusion_keywords = any(
            keyword in model_str or keyword in class_name or any(keyword in name for name in module_names)
            for keyword in ['diffusion', 'unet', 'latent', 'vae']
        )

        # Check for attention mechanisms
        has_attention = any(
            'attention' in name.lower() or 'attn' in name.lower() or 'self_attn' in name.lower()
            for name, _ in model.named_modules()
        ) or any(isinstance(m, (nn.MultiheadAttention,)) for m in model.modules())

        # Check for Vision Transformer specific patterns
        has_vit_patterns = any(
            keyword in model_str or keyword in class_name or any(keyword in name for name in module_names)
            for keyword in ['vit', 'vision_transformer', 'patch_embed', 'transformer']
        )

        # Check for convolutional layers
        has_conv = any(isinstance(m, (nn.Conv1d, nn.Conv2d, nn.Conv3d)) for m in model.modules())

        # Determine family
        if has_diffusion_keywords:
            family = ArchitectureFamily.DIFFUSION
        elif has_vit_patterns and has_attention:
            family = ArchitectureFamily.VIT
        elif has_attention and has_conv:
            family = ArchitectureFamily.HYBRID
        elif has_conv:
            family = ArchitectureFamily.CNN
        else:
            # Default to CNN if unclear
            family = ArchitectureFamily.CNN

        num_layers = len(list(model.modules()))

        return ModelSignature(
            family=family,
            total_params=total_params,
            num_layers=num_layers,
            has_attention=has_attention,
            has_conv=has_conv
        )

    def _apply_technique(
        self,
        model: nn.Module,
        technique: CompressionTechnique,
        example_input: Optional[Any] = None,
    ) -> nn.Module:
        """Apply single compression technique.

        Args:
            model: Model to optimize.
            technique: CompressionTechnique to apply.
            example_input: Optional example input for techniques that need it.

        Returns:
            Optimized model.
        """
        if technique == CompressionTechnique.QUANTIZE_INT8:
            quantized_model, _ = self.quantizer.quantize(model, method='int8_weight_only')
            return quantized_model

        elif technique == CompressionTechnique.QUANTIZE_INT4:
            # Note: INT4 might not be available in all backends
            quantized_model, _ = self.quantizer.quantize(model, method='int8_weight_only')  # Fallback
            return quantized_model

        elif technique == CompressionTechnique.QUANTIZE_FP8:
            # Note: FP8 might not be available in all backends
            quantized_model, _ = self.quantizer.quantize(model, method='int8_weight_only')  # Fallback
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
            # Try to determine if it's SD or ViT based on model structure
            model_str = str(model).lower()
            if 'unet' in model_str or 'diffusion' in model_str:
                # Stable Diffusion
                return self.pruner.prune_model(
                    model,
                    amount=0.3,
                    prune_type='sd',
                    ratio=0.3
                )
            else:
                # Vision Transformer
                return self.pruner.prune_model(
                    model,
                    amount=0.3,
                    prune_type='vit',
                    r=int(0.3 * 16)  # Convert ratio to token count
                )

        elif technique == CompressionTechnique.SVD_50:
            return self.decomposer.decompose_model(
                model,
                rank_ratio=0.5
            )

        elif technique == CompressionTechnique.FUSE_LAYERS:
            return self.fuser.fuse_model(
                model,
                fusion_types=['conv_bn_relu', 'linear_gelu']
            )

        else:
            print(f"Warning: Unknown technique {technique.value}, skipping")
            return model

    def _benchmark_model(
        self,
        model: nn.Module,
        original_size: float,
        example_input: Any,
    ) -> CompressionResult:
        """Benchmark optimized model.

        Args:
            model: Optimized model to benchmark.
            original_size: Original model size in MB.
            example_input: Example input tensor for inference benchmarking.

        Returns:
            CompressionResult with benchmark metrics.
        """
        # Measure size
        optimized_size = self._get_model_size(model)
        compression_ratio = original_size / optimized_size if optimized_size > 0 else 1.0

        # Measure speed using existing benchmark utility
        try:
            from model_opt.utils.benchmark import measure_inference_time
            inference_time_ms = measure_inference_time(model, example_input, device='cpu', iterations=100)
        except Exception:
            # Fallback: simple timing
            model.eval()
            times = []
            for _ in range(100):
                start = time.time()
                with torch.no_grad():
                    _ = model(example_input)
                times.append((time.time() - start) * 1000)
            inference_time_ms = np.mean(times)

        return CompressionResult(
            techniques=[],  # Will be filled by caller
            speedup=1.0,  # Would need baseline comparison for accurate speedup
            compression_ratio=compression_ratio,
            accuracy_drop=0.0,  # Would need validation data for accuracy
            memory_reduction=compression_ratio,
            inference_time_ms=inference_time_ms
        )

    def _get_model_size(self, model: nn.Module) -> float:
        """Get model size in MB.

        Args:
            model: Model to measure.

        Returns:
            Size in megabytes.
        """
        param_size = sum(p.numel() * p.element_size() for p in model.parameters())
        buffer_size = sum(b.numel() * b.element_size() for b in model.buffers())
        total_size = param_size + buffer_size
        return total_size / (1024 * 1024)

    def _create_dummy_input(self, model: nn.Module) -> Any:
        """Create dummy input tensor for model.

        Args:
            model: Model to create input for.

        Returns:
            Dummy input tensor.
        """
        # Try to infer input shape from first layer
        dummy_shape = None

        # Check first Conv2d or Linear layer
        for module in model.modules():
            if isinstance(module, nn.Conv2d):
                in_channels = module.in_channels
                # Common image sizes
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

        # Default fallback
        if dummy_shape is None:
            dummy_shape = (1, 3, 224, 224)  # Common image input

        return torch.randn(*dummy_shape)

