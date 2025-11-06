"""Storage integration for federated trees (MongoDB/Redis/Neo4j)."""
import networkx as nx
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from model_opt.core.storage.base import StorageBackend
from model_opt.core.storage.mongodb_backend import MongoDBBackend
from model_opt.core.storage.redis_backend import RedisBackend
from model_opt.core.storage.neo4j_backend import Neo4jBackend


class FederatedTreeStorage:
    """Storage manager for federated trees."""
    
    def __init__(self, storage_backend: Optional[StorageBackend] = None, file_path: Optional[str] = None):
        """Initialize federated tree storage.
        
        Args:
            storage_backend: Storage backend instance (MongoDB, Redis, or Neo4j)
            file_path: Optional path to JSON file for file-based storage
        """
        # If storage_backend is a string, treat it as file_path and set storage to None
        if isinstance(storage_backend, str):
            self.file_path = storage_backend
            self.storage = None
        else:
            self.storage = storage_backend
            self.file_path = file_path
    
    def save_tree(self, tree: nx.DiGraph, tree_id: str = "federated_tree") -> bool:
        """Save tree to storage backend or file.
        
        Args:
            tree: NetworkX DiGraph to save
            tree_id: Identifier for the tree (for storage backend)
            
        Returns:
            True if successful
        """
        # Try file-based saving if file_path is set
        if self.file_path:
            try:
                import json
                from pathlib import Path
                from datetime import datetime
                
                tree_data = {
                    'nodes': {},
                    'edges': [],
                    'metadata': {
                        'node_count': tree.number_of_nodes(),
                        'edge_count': tree.number_of_edges(),
                        'saved_at': datetime.now().isoformat()
                    }
                }
                
                # Serialize nodes
                for node_id, node_attrs in tree.nodes(data=True):
                    serialized_data = {}
                    for key, value in node_attrs.items():
                        if isinstance(value, (dict, list, str, int, float, bool, type(None))):
                            serialized_data[key] = value
                        else:
                            serialized_data[key] = str(value)
                    tree_data['nodes'][node_id] = serialized_data
                
                # Serialize edges
                for parent, child, edge_attrs in tree.edges(data=True):
                    serialized_edge = {
                        'parent': parent,
                        'child': child,
                        'data': {}
                    }
                    for key, value in edge_attrs.items():
                        if isinstance(value, (dict, list, str, int, float, bool, type(None))):
                            serialized_edge['data'][key] = value
                        else:
                            serialized_edge['data'][key] = str(value)
                    tree_data['edges'].append(serialized_edge)
                
                json_path = Path(self.file_path)
                json_path.parent.mkdir(parents=True, exist_ok=True)
                with open(json_path, 'w') as f:
                    json.dump(tree_data, f, indent=2)
                return True
            except Exception as e:
                print(f"Warning: Failed to save tree to file {self.file_path}: {e}")
        
        # Fall back to storage backend
        if self.storage is None or isinstance(self.storage, str):
            return False
        
        # Serialize tree to JSON-compatible format
        tree_data = {
            'nodes': {},
            'edges': [],
            'metadata': {
                'node_count': tree.number_of_nodes(),
                'edge_count': tree.number_of_edges(),
                'saved_at': datetime.now().isoformat()
            }
        }
        
        # Serialize nodes
        for node_id, node_data in tree.nodes(data=True):
            # Convert node data to serializable format
            serialized_data = {}
            for key, value in node_data.items():
                if isinstance(value, (dict, list, str, int, float, bool, type(None))):
                    serialized_data[key] = value
                else:
                    # Convert other types to string
                    serialized_data[key] = str(value)
            tree_data['nodes'][node_id] = serialized_data
        
        # Serialize edges
        for parent, child, edge_data in tree.edges(data=True):
            serialized_edge = {
                'parent': parent,
                'child': child,
                'data': {}
            }
            for key, value in edge_data.items():
                if isinstance(value, (dict, list, str, int, float, bool, type(None))):
                    serialized_edge['data'][key] = value
                else:
                    serialized_edge['data'][key] = str(value)
            tree_data['edges'].append(serialized_edge)
        
        return self.storage.save(tree_id, tree_data)
    
    def load_tree(self, tree_id: str = "federated_tree", file_path: Optional[str] = None) -> Optional[nx.DiGraph]:
        """Load tree from storage backend or file.
        
        Args:
            tree_id: Identifier for the tree (for storage backend)
            file_path: Optional path to JSON file (for file-based loading)
            
        Returns:
            NetworkX DiGraph or None if not found
        """
        tree_data = None
        
        # Try file-based loading first if file_path is provided
        if file_path:
            try:
                import json
                from pathlib import Path
                json_path = Path(file_path)
                if json_path.exists():
                    with open(json_path, 'r') as f:
                        tree_data = json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load tree from file {file_path}: {e}")
        
        # Try storage backend if file loading failed or not provided
        # Only if storage is not a string (file path)
        if tree_data is None and self.storage is not None and not isinstance(self.storage, str):
            try:
                tree_data = self.storage.load(tree_id)
            except Exception:
                pass
        
        if tree_data is None:
            return None
        
        # Reconstruct NetworkX graph
        tree = nx.DiGraph()
        
        # Add nodes
        for node_id, node_attrs in tree_data.get('nodes', {}).items():
            tree.add_node(node_id, **node_attrs)
        
        # Add edges
        for edge in tree_data.get('edges', []):
            parent = edge['parent']
            child = edge['child']
            edge_data = edge.get('data', {})
            tree.add_edge(parent, child, **edge_data)
        
        return tree
    
    def save_node_result(
        self,
        node_id: str,
        result: Dict[str, Any],
        architecture: str,
        technique: str
    ) -> bool:
        """Save individual node result for federated learning.
        
        Args:
            node_id: Node identifier
            result: Compression result dictionary
            architecture: Architecture family
            technique: Compression technique
            
        Returns:
            True if successful
        """
        if self.storage is None or isinstance(self.storage, str):
            return False
        
        key = f"node_result:{architecture}:{technique}:{node_id}"
        
        result_data = {
            'node_id': node_id,
            'architecture': architecture,
            'technique': technique,
            'result': result,
            'timestamp': datetime.now().isoformat()
        }
        
        return self.storage.save(key, result_data)
    
    def load_node_result(
        self,
        node_id: str,
        architecture: str,
        technique: str
    ) -> Optional[Dict[str, Any]]:
        """Load node result from storage.
        
        Args:
            node_id: Node identifier
            architecture: Architecture family
            technique: Compression technique
            
        Returns:
            Result dictionary or None
        """
        if self.storage is None or isinstance(self.storage, str):
            return None
        
        key = f"node_result:{architecture}:{technique}:{node_id}"
        return self.storage.load(key)
    
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
        if self.storage is None or isinstance(self.storage, str):
            return {}
        
        # Query all related results
        prefix = f"node_result:{architecture}:{technique}:"
        keys = self.storage.list_keys(prefix=prefix)
        
        results = []
        for key in keys:
            result_data = self.storage.load(key)
            if result_data:
                results.append(result_data.get('result', {}))
        
        if not results:
            return {
                'sample_count': 0,
                'avg_accuracy_retention': 0.0,
                'avg_compression_ratio': 0.0
            }
        
        # Aggregate statistics
        acc_retentions = [
            r.get('accuracy_retention', 0.0) for r in results
            if 'accuracy_retention' in r
        ]
        comp_ratios = [
            r.get('compression_ratio', 0.0) for r in results
            if 'compression_ratio' in r
        ]
        
        return {
            'sample_count': len(results),
            'avg_accuracy_retention': sum(acc_retentions) / len(acc_retentions) if acc_retentions else 0.0,
            'avg_compression_ratio': sum(comp_ratios) / len(comp_ratios) if comp_ratios else 0.0,
            'min_accuracy_retention': min(acc_retentions) if acc_retentions else 0.0,
            'max_accuracy_retention': max(acc_retentions) if acc_retentions else 0.0,
        }

