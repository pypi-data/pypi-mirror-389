"""ChromaDB backend for vector database."""
from typing import Dict, List, Optional, Any
from model_opt.core.storage.base import StorageBackend
from model_opt.core.exceptions import EnvironmentError

try:
    import chromadb
    from chromadb.config import Settings
    _CHROMADB_AVAILABLE = True
except ImportError:
    _CHROMADB_AVAILABLE = False
    chromadb = None


class ChromaDBBackend(StorageBackend):
    """ChromaDB backend for vector storage."""
    
    def __init__(
        self,
        collection_name: str = "compression_tree",
        persist_directory: Optional[str] = None
    ):
        """Initialize ChromaDB backend.
        
        Args:
            collection_name: Collection name
            persist_directory: Optional directory for persistence
        """
        if not _CHROMADB_AVAILABLE:
            raise EnvironmentError(
                "chromadb is not installed. Install with: pip install chromadb>=0.4.0"
            )
        
        try:
            if persist_directory:
                self.client = chromadb.PersistentClient(
                    path=persist_directory,
                    settings=Settings(anonymized_telemetry=False)
                )
            else:
                self.client = chromadb.Client(
                    settings=Settings(anonymized_telemetry=False)
                )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            raise EnvironmentError(f"ChromaDB initialization failed: {e}")
    
    def save(self, key: str, value: Dict[str, Any]) -> bool:
        """Save a value to ChromaDB.
        
        Args:
            key: Storage key
            value: Value to save (should include embeddings if available)
            
        Returns:
            True if successful
        """
        try:
            # Extract embeddings if present
            embeddings = value.pop('embeddings', None)
            metadata = value.copy()
            
            if embeddings is not None:
                self.collection.upsert(
                    ids=[key],
                    embeddings=[embeddings],
                    metadatas=[metadata]
                )
            else:
                # Store as metadata only
                self.collection.upsert(
                    ids=[key],
                    metadatas=[metadata]
                )
            return True
        except Exception as e:
            print(f"ChromaDB save error: {e}")
            return False
    
    def load(self, key: str) -> Optional[Dict[str, Any]]:
        """Load a value from ChromaDB.
        
        Args:
            key: Storage key
            
        Returns:
            Value if found, None otherwise
        """
        try:
            results = self.collection.get(ids=[key], include=['embeddings', 'metadatas'])
            if results['ids']:
                metadata = results['metadatas'][0] if results['metadatas'] else {}
                if results['embeddings']:
                    metadata['embeddings'] = results['embeddings'][0]
                return metadata
            return None
        except Exception as e:
            print(f"ChromaDB load error: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete a value from ChromaDB.
        
        Args:
            key: Storage key
            
        Returns:
            True if successful
        """
        try:
            self.collection.delete(ids=[key])
            return True
        except Exception as e:
            print(f"ChromaDB delete error: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if a key exists in ChromaDB.
        
        Args:
            key: Storage key
            
        Returns:
            True if key exists
        """
        try:
            results = self.collection.get(ids=[key])
            return len(results['ids']) > 0
        except Exception:
            return False
    
    def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """List all keys in ChromaDB.
        
        Args:
            prefix: Optional prefix to filter keys
            
        Returns:
            List of keys
        """
        try:
            results = self.collection.get()
            keys = results['ids']
            if prefix:
                keys = [k for k in keys if k.startswith(prefix)]
            return keys
        except Exception as e:
            print(f"ChromaDB list_keys error: {e}")
            return []
    
    def clear(self) -> bool:
        """Clear all data from ChromaDB collection.
        
        Returns:
            True if successful
        """
        try:
            self.collection.delete()
            # Recreate collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection.name,
                metadata={"hnsw:space": "cosine"}
            )
            return True
        except Exception as e:
            print(f"ChromaDB clear error: {e}")
            return False
    
    def query(
        self,
        query_embeddings: List[List[float]],
        n_results: int = 10,
        where: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Query by embeddings (vector search).
        
        Args:
            query_embeddings: Query embeddings
            n_results: Number of results
            where: Optional metadata filter
            
        Returns:
            Query results
        """
        try:
            results = self.collection.query(
                query_embeddings=query_embeddings,
                n_results=n_results,
                where=where
            )
            return results
        except Exception as e:
            print(f"ChromaDB query error: {e}")
            return {}

