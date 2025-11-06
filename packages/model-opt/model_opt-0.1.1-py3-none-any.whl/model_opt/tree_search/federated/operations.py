"""Tree cloning, pruning, and expansion operations for federated trees."""
import networkx as nx
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import hashlib
import asyncio

try:
    import numpy as np
    _NUMPY_AVAILABLE = True
except ImportError:
    _NUMPY_AVAILABLE = False
    np = None

try:
    from .api_client import FederatedAPIClient
    _API_CLIENT_AVAILABLE = True
except ImportError:
    _API_CLIENT_AVAILABLE = False
    FederatedAPIClient = None


class FederatedTreeOperations:
    """Operations for federated tree management."""
    
    def __init__(
        self,
        storage_backend=None,
        vector_db=None,
        file_path: Optional[str] = None,
        api_client: Optional[Any] = None
    ):
        """Initialize federated tree operations.
        
        Args:
            storage_backend: Storage backend (MongoDB, Redis, etc.)
            vector_db: Optional vector database for paper expansion
            file_path: Optional path to JSON file for file-based loading
            api_client: Optional FederatedAPIClient for API-based operations
        """
        self.storage = storage_backend
        self.vector_db = vector_db
        self.file_path = file_path
        self.api_client = api_client
    
    def clone_tree(
        self,
        architecture_family: str,
        user_constraints: Dict[str, Any]
    ) -> nx.DiGraph:
        """Clone federated tree for local use with filtering.
        
        Args:
            architecture_family: Target architecture family (e.g., 'ResNet', 'Transformer')
            user_constraints: User-specific constraints dict
            
        Returns:
            Local copy of filtered tree as NetworkX DiGraph
        """
        # Priority: API client > storage backend > file_path
        if self.api_client is not None:
            return asyncio.run(self.clone_tree_async(architecture_family, user_constraints))
        
        # Load global federated tree from storage
        global_tree = self._load_federated_tree_from_db()
        
        if global_tree is None or global_tree.number_of_nodes() == 0:
            # Create empty tree if no global tree exists
            return nx.DiGraph()
        
        # Create new directed graph for local copy
        local_tree = nx.DiGraph()
        
        # Filter relevant nodes
        for node_id, node_data in global_tree.nodes(data=True):
            if self._is_relevant(node_data, architecture_family):
                # Copy node with all attributes
                local_tree.add_node(node_id, **node_data)
        
        # Copy edges between retained nodes
        for parent, child, edge_data in global_tree.edges(data=True):
            if parent in local_tree and child in local_tree:
                local_tree.add_edge(parent, child, **edge_data)
        
        # Initialize MCTS statistics for local use
        for node in local_tree.nodes():
            local_tree.nodes[node]['visit_count'] = 0
            local_tree.nodes[node]['q_value'] = 0.5  # neutral prior
            local_tree.nodes[node]['local_updated'] = datetime.now().isoformat()
        
        return local_tree
    
    def prune_irrelevant_nodes(
        self,
        tree: nx.DiGraph,
        architecture: str,
        constraints: Dict[str, Any]
    ) -> nx.DiGraph:
        """Prune nodes that don't match architecture or constraints.
        
        Args:
            tree: Tree to prune
            architecture: Target architecture
            constraints: Optimization constraints
            
        Returns:
            Pruned tree
        """
        nodes_to_remove = []
        
        for node_id, node_data in tree.nodes(data=True):
            # Architecture compatibility check
            if not self._is_compatible_architecture(node_data, architecture):
                nodes_to_remove.append(node_id)
                continue
            
            # Constraint validation
            config = node_data.get('compression_config', {})
            performance = node_data.get('performance', {})
            
            if constraints.get('min_accuracy_retention'):
                min_acc = constraints['min_accuracy_retention']
                acc_retention = performance.get('accuracy_retention', 0.0)
                if acc_retention < min_acc:
                    nodes_to_remove.append(node_id)
                    continue
            
            # Hardware feasibility
            if constraints.get('target_hardware') == 'edge':
                memory_gb = performance.get('memory_gb', 999)
                if memory_gb > 4.0:
                    nodes_to_remove.append(node_id)
                    continue
            
            # Latency constraints
            if constraints.get('max_latency_ms'):
                latency = performance.get('latency_ms', float('inf'))
                if latency > constraints['max_latency_ms']:
                    nodes_to_remove.append(node_id)
                    continue
        
        # Remove nodes and orphaned edges
        tree.remove_nodes_from(nodes_to_remove)
        
        # Remove isolated components (keep largest connected component)
        if tree.number_of_nodes() > 0:
            try:
                # For directed graphs, use weakly connected components
                components = list(nx.weakly_connected_components(tree))
                if components:
                    largest_cc = max(components, key=len)
                    isolated_nodes = set(tree.nodes()) - largest_cc
                    tree.remove_nodes_from(isolated_nodes)
            except Exception:
                # Fallback: keep all remaining nodes
                pass
        
        return tree
    
    def expand_tree_with_papers(
        self,
        tree: nx.DiGraph,
        architecture: str,
        vector_db=None
    ) -> Tuple[nx.DiGraph, int]:
        """Expand tree with nodes from relevant papers.
        
        Args:
            tree: Tree to expand
            architecture: Architecture family
            vector_db: Vector database (optional, uses self.vector_db if None)
            
        Returns:
            Tuple of (expanded_tree, new_nodes_added)
        """
        vector_db = vector_db or self.vector_db
        
        if vector_db is None:
            return tree, 0
        
        # Query vector DB for relevant papers
        query = f"{architecture} compression optimization"
        
        try:
            # Try to get embeddings model
            from model_opt.utils.embeddings import Embeddings
            emb = Embeddings()
            query_embedding = emb.encode([query])[0]
        except Exception:
            # Fallback: return tree unchanged
            return tree, 0
        
        # Query vector database
        try:
            results = vector_db.query(
                query_vec=query_embedding,
                top_k=15
            )
        except Exception:
            return tree, 0
        
        new_nodes_added = 0
        
        for score, paper_meta in results:
            # Extract technique from paper metadata
            technique = self._extract_technique_from_paper(paper_meta)
            
            if not technique:
                continue
            
            # Check if technique already in tree
            if self._technique_exists_in_tree(tree, technique):
                continue
            
            # Create new node
            new_node_id = self._generate_node_id(technique, architecture)
            
            new_node_data = {
                'architecture': {
                    'family': architecture,
                    'variant': technique.get('model', architecture)
                },
                'compression_config': technique.get('config', {}),
                'performance': {
                    'accuracy_retention': technique.get('reported_accuracy', 0.85) / 100.0,
                    'compression_ratio': technique.get('reported_compression', 2.0),
                    'latency_speedup': technique.get('speedup', 1.0)
                },
                'validation': {
                    'sample_count': 1,  # paper result only
                    'confidence': 0.3,  # low until community validates
                    'validators': 1,
                    'source': 'paper'
                },
                'source': {
                    'origin': 'paper',
                    'paper_refs': [paper_meta.get('title', 'unknown')],
                    'status': 'experimental',
                    'paper_score': float(score)
                }
            }
            
            tree.add_node(new_node_id, **new_node_data)
            
            # Connect to compatible parent nodes
            compatible_parents = self._find_compatible_nodes(tree, technique)
            for parent_id in compatible_parents:
                edge_weight = self._estimate_edge_weight(
                    parent_id, new_node_id, tree, technique
                )
                tree.add_edge(
                    parent_id, new_node_id,
                    weights={
                        'success_probability': edge_weight,
                        'sample_count': 1,
                        'confidence': 0.3
                    }
                )
            
            new_nodes_added += 1
        
        return tree, new_nodes_added
    
    def lookup_by_signature(
        self,
        signature,
        constraints: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict]:
        """Lookup node by model signature in federated tree.
        
        Args:
            signature: ModelSignature object
            constraints: Optional constraints dict
            
        Returns:
            Best matching node data dict or None
        """
        # Convert signature family to architecture family string
        try:
            from model_opt.autotuner.search_space import ArchitectureFamily
            arch_family_map = {
                ArchitectureFamily.CNN: "CNN",
                ArchitectureFamily.VIT: "ViT",
                ArchitectureFamily.HYBRID: "Hybrid",
                ArchitectureFamily.DIFFUSION: "Diffusion"
            }
            architecture_family = arch_family_map.get(signature.family, "CNN")
        except Exception:
            architecture_family = "CNN"
        
        # Prepare user constraints
        user_constraints = {}
        if constraints:
            if 'max_accuracy_drop' in constraints:
                user_constraints['min_accuracy_retention'] = 1.0 - constraints['max_accuracy_drop']
        
        # Clone tree for architecture
        local_tree = self.clone_tree(architecture_family, user_constraints)
        
        if local_tree is None or local_tree.number_of_nodes() == 0:
            return None
        
        # Find best matching node
        best_node = self._find_best_matching_node_for_signature(local_tree, signature, constraints)
        
        return best_node
    
    def _find_best_matching_node_for_signature(
        self,
        tree: nx.DiGraph,
        signature,
        constraints: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict]:
        """Find best matching node for signature.
        
        Args:
            tree: NetworkX DiGraph
            signature: ModelSignature object
            constraints: Optional constraints
            
        Returns:
            Best matching node data dict or None
        """
        best_node = None
        best_score = 0.0
        
        for node_id, node_data in tree.nodes(data=True):
            score = 0.0
            
            # Architecture match score
            arch = node_data.get('architecture', {})
            node_family = arch.get('family', '').lower()
            try:
                sig_family = signature.family.value.lower()
            except Exception:
                sig_family = "cnn"
            
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
                best_node = node_data.copy()
                best_node['node_id'] = node_id  # Include node ID in result
        
        return best_node if best_score > 0.0 else None
    
    def _load_federated_tree_from_db(self) -> Optional[nx.DiGraph]:
        """Load federated tree from storage backend or file."""
        tree_data = None
        
        # Try file-based loading first if file_path is provided
        if self.file_path:
            try:
                import json
                from pathlib import Path
                json_path = Path(self.file_path)
                if json_path.exists():
                    with open(json_path, 'r') as f:
                        tree_data = json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load tree from file {self.file_path}: {e}")
        
        # Try storage backend if file loading failed or not provided
        # Only if storage is not a string (file path)
        if tree_data is None and self.storage is not None and not isinstance(self.storage, str):
            try:
                tree_data = self.storage.load('federated_tree')
            except Exception:
                pass
        
        if tree_data is None:
            return None
        
        # Reconstruct NetworkX graph from serialized data
        tree = nx.DiGraph()
        
        # Add nodes
        for node_id, node_attrs in tree_data.get('nodes', {}).items():
            tree.add_node(node_id, **node_attrs)
        
        # Add edges
        for edge in tree_data.get('edges', []):
            parent, child = edge['parent'], edge['child']
            edge_attrs = edge.get('data', {})
            tree.add_edge(parent, child, **edge_attrs)
        
        return tree
    
    def _is_relevant(self, node_data: Dict, architecture_family: str) -> bool:
        """Check if node is relevant for architecture family."""
        arch = node_data.get('architecture', {})
        node_family = arch.get('family', '').lower()
        target_family = architecture_family.lower()
        
        # Exact match or partial match
        return target_family in node_family or node_family in target_family
    
    def _is_compatible_architecture(self, node_data: Dict, architecture: str) -> bool:
        """Check if node architecture is compatible."""
        arch = node_data.get('architecture', {})
        node_family = arch.get('family', '').lower()
        target = architecture.lower()
        
        # Generic compatibility checks
        if 'transformer' in target and 'transformer' in node_family:
            return True
        if 'resnet' in target or 'cnn' in target:
            if 'resnet' in node_family or 'cnn' in node_family:
                return True
        
        return node_family == target
    
    def _extract_technique_from_paper(self, paper_meta: Dict) -> Optional[Dict]:
        """Extract compression technique information from paper metadata."""
        techniques_str = paper_meta.get('techniques', 'Unknown')
        
        if techniques_str == 'Unknown':
            return None
        
        # Parse technique string
        technique_map = {
            'quantization': {'type': 'quantization', 'bits': 8},
            'pruning': {'type': 'pruning', 'ratio': 0.5},
            'distillation': {'type': 'distillation', 'temperature': 4.0},
            'fusion': {'type': 'fusion'}
        }
        
        technique_config = {}
        for tech_name, tech_config in technique_map.items():
            if tech_name.lower() in techniques_str.lower():
                technique_config.update(tech_config)
        
        if not technique_config:
            return None
        
        return {
            'config': technique_config,
            'model': paper_meta.get('architecture', 'Unknown'),
            'reported_accuracy': float(paper_meta.get('citations', 0)) * 10,  # Estimate
            'reported_compression': 2.0,  # Default estimate
            'speedup': 1.5  # Default estimate
        }
    
    def _technique_exists_in_tree(self, tree: nx.DiGraph, technique: Dict) -> bool:
        """Check if technique already exists in tree."""
        for node_id, node_data in tree.nodes(data=True):
            config = node_data.get('compression_config', {})
            tech_type = technique.get('config', {}).get('type')
            
            if tech_type and tech_type in str(config):
                return True
        
        return False
    
    def _generate_node_id(self, technique: Dict, architecture: str) -> str:
        """Generate unique node ID."""
        tech_str = str(technique.get('config', {}))
        hash_input = f"{architecture}_{tech_str}"
        hash_obj = hashlib.md5(hash_input.encode())
        return f"node_{hash_obj.hexdigest()[:12]}"
    
    def _find_compatible_nodes(self, tree: nx.DiGraph, technique: Dict) -> List[str]:
        """Find compatible parent nodes for new technique."""
        compatible = []
        tech_type = technique.get('config', {}).get('type', '')
        
        for node_id, node_data in tree.nodes(data=True):
            config = node_data.get('compression_config', {})
            
            # Check if compatible (e.g., quantization before pruning)
            if tech_type == 'pruning' and 'quantization' in str(config):
                compatible.append(node_id)
            elif tech_type == 'distillation' and any(k in str(config) for k in ['quantization', 'pruning']):
                compatible.append(node_id)
        
        return compatible[:5]  # Limit to top 5 compatible parents
    
    def _estimate_edge_weight(
        self,
        parent_id: str,
        child_id: str,
        tree: nx.DiGraph,
        technique: Dict
    ) -> float:
        """Estimate edge weight between parent and child."""
        # Base weight from paper score
        base_weight = technique.get('source', {}).get('paper_score', 0.5)
        
        # Adjust based on parent performance
        if parent_id in tree.nodes():
            parent_perf = tree.nodes[parent_id].get('performance', {})
            parent_acc = parent_perf.get('accuracy_retention', 0.9)
            base_weight *= parent_acc
        
        # Cap between 0.1 and 0.9
        return max(0.1, min(0.9, base_weight))

    async def clone_tree_async(
        self,
        architecture_family: str,
        user_constraints: Dict[str, Any]
    ) -> nx.DiGraph:
        """Async clone tree from API.
        
        Args:
            architecture_family: Target architecture family
            user_constraints: User constraints dict
            
        Returns:
            NetworkX DiGraph tree
        """
        if self.api_client is None:
            raise ValueError("API client not initialized")
        
        response = await self.api_client.clone_tree(architecture_family, user_constraints)
        tree_data = response.get("tree", {})
        
        if not tree_data:
            # Fallback to sample tree if clone returns empty
            try:
                sample_response = await self.api_client.get_sample_tree()
                tree_data = sample_response
            except Exception:
                return nx.DiGraph()
        
        return self._deserialize_tree(tree_data)

    async def expand_tree_with_papers_async(
        self,
        tree: nx.DiGraph,
        architecture: str
    ) -> Tuple[nx.DiGraph, int]:
        """Async expand tree with papers from API.
        
        Args:
            tree: Tree to expand
            architecture: Architecture family
            
        Returns:
            Tuple of (expanded_tree, new_nodes_added)
        """
        if self.api_client is None:
            raise ValueError("API client not initialized")
        
        tree_id = tree.graph.get("federated_id")
        if not tree_id:
            # Create new tree ID if not set
            tree_id = await self._create_new_tree_async(tree, architecture)
        
        response = await self.api_client.expand_tree(tree_id, architecture)
        new_nodes = response.get("new_nodes", [])
        
        for node_data in new_nodes:
            node_id = node_data.get("id") or node_data.get("node_id")
            if node_id:
                # Remove id from data to avoid duplication
                node_attrs = {k: v for k, v in node_data.items() if k not in ("id", "node_id")}
                tree.add_node(node_id, **node_attrs)
        
        return tree, len(new_nodes)

    async def sync_local_discoveries_async(
        self,
        local_tree: nx.DiGraph
    ) -> Dict[str, Any]:
        """Async sync local discoveries to API.
        
        Args:
            local_tree: Local tree to sync
            
        Returns:
            Sync result dictionary
        """
        if self.api_client is None:
            raise ValueError("API client not initialized")
        
        tree_id = local_tree.graph.get("federated_id")
        if not tree_id:
            return {"status": "skipped", "reason": "No federated_id"}
        
        changes = {"updated_edges": [], "new_nodes": []}
        serialized_tree = self._serialize_tree(local_tree)
        
        response = await self.api_client.sync_changes(tree_id, serialized_tree, changes)
        return response

    async def merge_changes_async(
        self,
        local_tree: nx.DiGraph,
        changes: Dict[str, Any]
    ) -> nx.DiGraph:
        """Async merge changes with federated tree.
        
        Args:
            local_tree: Local tree
            changes: Changes dictionary
            
        Returns:
            Merged tree
        """
        if self.api_client is None:
            raise ValueError("API client not initialized")
        
        tree_id = local_tree.graph.get("federated_id")
        if not tree_id:
            tree_id = await self._create_new_tree_async(local_tree, "unknown")
        
        serialized_tree = self._serialize_tree(local_tree)
        response = await self.api_client.merge_changes(tree_id, serialized_tree, changes)
        
        merged_tree_data = response.get("tree", {})
        if merged_tree_data:
            merged_tree = self._deserialize_tree(merged_tree_data)
            return merged_tree
        
        return local_tree

    def _serialize_tree(self, tree: nx.DiGraph) -> Dict:
        """Serialize NetworkX tree to API format.
        
        Args:
            tree: NetworkX DiGraph
            
        Returns:
            Serialized tree dictionary
        """
        nodes = []
        for node_id, node_data in tree.nodes(data=True):
            node_dict = {"id": node_id, **node_data}
            nodes.append(node_dict)
        
        edges = []
        for u, v, edge_data in tree.edges(data=True):
            edge_dict = {"source": u, "target": v, **edge_data}
            edges.append(edge_dict)
        
        return {
            "nodes": nodes,
            "edges": edges,
            "meta": dict(tree.graph),
        }

    def _deserialize_tree(self, tree_dict: Dict) -> nx.DiGraph:
        """Deserialize API format to NetworkX tree.
        
        Args:
            tree_dict: Serialized tree dictionary
            
        Returns:
            NetworkX DiGraph
        """
        g = nx.DiGraph()
        
        # Add nodes
        for node in tree_dict.get("nodes", []):
            node_id = node.get("id") or node.get("node_id")
            if node_id is not None:
                # Remove id from attributes
                node_attrs = {k: v for k, v in node.items() if k not in ("id", "node_id")}
                g.add_node(node_id, **node_attrs)
        
        # Add edges
        for edge in tree_dict.get("edges", []):
            source = edge.get("source")
            target = edge.get("target")
            if source and target:
                # Remove source/target from attributes
                edge_attrs = {k: v for k, v in edge.items() if k not in ("source", "target")}
                g.add_edge(source, target, **edge_attrs)
        
        # Update graph metadata
        meta = tree_dict.get("meta", {})
        g.graph.update(meta)
        
        return g

    async def _create_new_tree_async(
        self,
        tree: nx.DiGraph,
        architecture: str
    ) -> str:
        """Create new tree ID in API (for stub v1, just set locally).
        
        Args:
            tree: Tree to create ID for
            architecture: Architecture family
            
        Returns:
            Tree ID string
        """
        # For stub v1, generate a local ID
        import hashlib
        tree_hash = hashlib.md5(f"{architecture}_{len(tree.nodes())}".encode()).hexdigest()[:12]
        fake_id = f"local-{tree_hash}"
        tree.graph["federated_id"] = fake_id
        return fake_id

