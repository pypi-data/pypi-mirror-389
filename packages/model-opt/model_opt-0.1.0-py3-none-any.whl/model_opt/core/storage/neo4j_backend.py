"""Neo4j backend for advanced graph analytics (optional)."""
from typing import Dict, List, Optional, Any
from model_opt.core.storage.base import StorageBackend
from model_opt.core.exceptions import EnvironmentError

try:
    from neo4j import GraphDatabase
    _NEO4J_AVAILABLE = True
except ImportError:
    _NEO4J_AVAILABLE = False
    GraphDatabase = None


class Neo4jBackend(StorageBackend):
    """Neo4j backend for graph storage (optional)."""
    
    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        user: str = "neo4j",
        password: str = "password"
    ):
        """Initialize Neo4j backend.
        
        Args:
            uri: Neo4j URI
            user: Username
            password: Password
        """
        if not _NEO4J_AVAILABLE:
            raise EnvironmentError(
                "neo4j driver is not installed. Install with: pip install neo4j"
            )
        
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
        except Exception as e:
            raise EnvironmentError(f"Neo4j initialization failed: {e}")
    
    def save(self, key: str, value: Dict[str, Any]) -> bool:
        """Save a value to Neo4j as node property.
        
        Args:
            key: Storage key (node label + id)
            value: Value to save
            
        Returns:
            True if successful
        """
        try:
            with self.driver.session() as session:
                # Create or update node
                query = """
                MERGE (n:CompressionResult {id: $key})
                SET n += $props
                RETURN n
                """
                session.run(query, key=key, props=value)
            return True
        except Exception as e:
            print(f"Neo4j save error: {e}")
            return False
    
    def load(self, key: str) -> Optional[Dict[str, Any]]:
        """Load a value from Neo4j.
        
        Args:
            key: Storage key
            
        Returns:
            Value if found, None otherwise
        """
        try:
            with self.driver.session() as session:
                query = "MATCH (n:CompressionResult {id: $key}) RETURN n"
                result = session.run(query, key=key)
                record = result.single()
                if record:
                    node = record['n']
                    props = dict(node)
                    props.pop('id', None)  # Remove id from props
                    return props
            return None
        except Exception as e:
            print(f"Neo4j load error: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete a value from Neo4j.
        
        Args:
            key: Storage key
            
        Returns:
            True if successful
        """
        try:
            with self.driver.session() as session:
                query = "MATCH (n:CompressionResult {id: $key}) DELETE n"
                result = session.run(query, key=key)
                return True
        except Exception as e:
            print(f"Neo4j delete error: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if a key exists in Neo4j.
        
        Args:
            key: Storage key
            
        Returns:
            True if key exists
        """
        try:
            with self.driver.session() as session:
                query = "MATCH (n:CompressionResult {id: $key}) RETURN n LIMIT 1"
                result = session.run(query, key=key)
                return result.single() is not None
        except Exception:
            return False
    
    def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """List all keys in Neo4j.
        
        Args:
            prefix: Optional prefix to filter keys
            
        Returns:
            List of keys
        """
        try:
            with self.driver.session() as session:
                if prefix:
                    query = "MATCH (n:CompressionResult) WHERE n.id STARTS WITH $prefix RETURN n.id"
                    result = session.run(query, prefix=prefix)
                else:
                    query = "MATCH (n:CompressionResult) RETURN n.id"
                    result = session.run(query)
                
                keys = [record['n.id'] for record in result]
                return keys
        except Exception as e:
            print(f"Neo4j list_keys error: {e}")
            return []
    
    def clear(self) -> bool:
        """Clear all data from Neo4j.
        
        Returns:
            True if successful
        """
        try:
            with self.driver.session() as session:
                query = "MATCH (n:CompressionResult) DETACH DELETE n"
                session.run(query)
            return True
        except Exception as e:
            print(f"Neo4j clear error: {e}")
            return False
    
    def close(self):
        """Close Neo4j connection."""
        if hasattr(self, 'driver'):
            self.driver.close()

