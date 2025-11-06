"""Main federated tree manager."""
import networkx as nx
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from .operations import FederatedTreeOperations
from .storage import FederatedTreeStorage
from .merge_operations import FederatedMergeOperations
from .conflict_resolver import ConflictResolver

from model_opt.core.storage.base import StorageBackend

try:
    from .api_client import FederatedAPIClient
    from model_opt.core.config import FEDERATED_API_CONFIG
    _API_CLIENT_AVAILABLE = True
except ImportError:
    _API_CLIENT_AVAILABLE = False
    FederatedAPIClient = None


class FederatedTreeManager:
    """Main manager for federated tree operations."""
    
    def __init__(
        self,
        storage_backend: Optional[StorageBackend] = None,
        vector_db=None,
        change_threshold: float = 0.15,
        conflict_threshold: float = 0.3,
        file_path: Optional[str] = None,
        api_client: Optional[Any] = None,
        use_api: bool = False
    ):
        """Initialize federated tree manager.
        
        Args:
            storage_backend: Storage backend for persistence
            vector_db: Optional vector database for paper expansion
            change_threshold: Threshold for significant changes
            conflict_threshold: Threshold for conflicts
            file_path: Optional path to JSON file for file-based loading
            api_client: Optional FederatedAPIClient instance
            use_api: If True, initialize API client from config
        """
        # Initialize API client if requested or provided
        self.api_client = api_client
        if use_api and self.api_client is None and _API_CLIENT_AVAILABLE:
            try:
                self.api_client = FederatedAPIClient(
                    base_url=FEDERATED_API_CONFIG['base_url'],
                    api_key=FEDERATED_API_CONFIG['api_key'],
                    timeout=FEDERATED_API_CONFIG['timeout']
                )
            except Exception:
                self.api_client = None
        
        # If storage_backend is a string (file path), pass None to storage and use file_path
        if isinstance(storage_backend, str):
            self.storage = FederatedTreeStorage(storage_backend=None, file_path=storage_backend)
            self.operations = FederatedTreeOperations(
                storage_backend=None,
                vector_db=vector_db,
                file_path=storage_backend,
                api_client=self.api_client
            )
        else:
            self.storage = FederatedTreeStorage(storage_backend, file_path=file_path)
            self.operations = FederatedTreeOperations(
                storage_backend,
                vector_db,
                file_path=file_path,
                api_client=self.api_client
            )
        self.merge_ops = FederatedMergeOperations(change_threshold, conflict_threshold)
        self.conflict_resolver = ConflictResolver()
        
        self.vector_db = vector_db
    
    def initialize_local_tree(
        self,
        architecture_family: str,
        user_constraints: Dict[str, Any]
    ) -> nx.DiGraph:
        """Initialize local tree from federated tree.
        
        Args:
            architecture_family: Target architecture family
            user_constraints: User-specific constraints
            
        Returns:
            Local tree as NetworkX DiGraph
        """
        # Clone tree from federated storage
        local_tree = self.operations.clone_tree(architecture_family, user_constraints)
        
        # Prune irrelevant nodes
        local_tree = self.operations.prune_irrelevant_nodes(
            local_tree,
            architecture_family,
            user_constraints
        )
        
        # Expand with papers from vector DB if available
        if self.vector_db:
            local_tree, new_nodes = self.operations.expand_tree_with_papers(
                local_tree,
                architecture_family,
                self.vector_db
            )
            if new_nodes > 0:
                print(f"✓ Expanded tree with {new_nodes} new nodes from papers")
        
        return local_tree
    
    def sync_with_federated(
        self,
        local_tree: nx.DiGraph,
        auto_resolve: bool = True
    ) -> Tuple[nx.DiGraph, Dict[str, Any]]:
        """Synchronize local tree with federated tree.
        
        Args:
            local_tree: Local tree to sync
            auto_resolve: Whether to auto-resolve conflicts
            
        Returns:
            Tuple of (merged_tree, sync_report)
        """
        # Load federated tree
        fed_tree = self.storage.load_tree(file_path=self.storage.file_path)
        
        if fed_tree is None or fed_tree.number_of_nodes() == 0:
            # No federated tree exists, save local as federated
            self.storage.save_tree(local_tree)
            return local_tree, {
                'status': 'initialized',
                'new_tree': True
            }
        
        # Detect changes
        changes = self.merge_ops.detect_changes(local_tree, fed_tree)
        
        # Resolve conflicts if any
        if changes['conflicts'] and auto_resolve:
            for conflict in changes['conflicts']:
                parent, child = conflict['edge']
                
                if local_tree.has_edge(parent, child) and fed_tree.has_edge(parent, child):
                    local_edge = local_tree.edges[parent, child]
                    fed_edge = fed_tree.edges[parent, child]
                    
                    # Resolve conflict
                    resolution = self.conflict_resolver.resolve_conflict(
                        local_edge, fed_edge
                    )
                    
                    # Apply resolution
                    resolved_edge = self.conflict_resolver.apply_resolution(
                        resolution, local_edge, fed_edge
                    )
                    
                    # Update federated tree with resolved edge
                    fed_tree.edges[parent, child].update(resolved_edge)
        
        # Merge trees
        merged_tree = self.merge_ops.merge_trees(local_tree, fed_tree)
        
        # Save merged tree back to storage
        self.storage.save_tree(merged_tree)
        
        sync_report = {
            'status': 'merged',
            'changes_detected': {
                'updated_edges': len(changes['updated_edges']),
                'new_edges': len(changes['new_edges']),
                'new_nodes': len(changes['new_nodes']),
                'conflicts': len(changes['conflicts'])
            },
            'merged_nodes': merged_tree.number_of_nodes(),
            'merged_edges': merged_tree.number_of_edges()
        }
        
        return merged_tree, sync_report
    
    def save_local_tree(self, local_tree: nx.DiGraph, tree_id: str = "local_tree") -> bool:
        """Save local tree to storage.
        
        Args:
            local_tree: Local tree to save
            tree_id: Tree identifier
            
        Returns:
            True if successful
        """
        return self.storage.save_tree(local_tree, tree_id)
    
    def load_local_tree(self, tree_id: str = "local_tree") -> Optional[nx.DiGraph]:
        """Load local tree from storage.
        
        Args:
            tree_id: Tree identifier
            
        Returns:
            Local tree or None
        """
        return self.storage.load_tree(tree_id)
    
    def update_node_result(
        self,
        node_id: str,
        result: Dict[str, Any],
        architecture: str,
        technique: str
    ) -> bool:
        """Update node result in federated storage.
        
        Args:
            node_id: Node identifier
            result: Compression result
            architecture: Architecture family
            technique: Compression technique
            
        Returns:
            True if successful
        """
        return self.storage.save_node_result(node_id, result, architecture, technique)
    
    def get_node_statistics(
        self,
        architecture: str,
        technique: str
    ) -> Dict[str, Any]:
        """Get aggregated statistics for nodes.
        
        Args:
            architecture: Architecture family
            technique: Compression technique
            
        Returns:
            Statistics dictionary
        """
        return self.storage.get_node_statistics(architecture, technique)

