"""Redis backend for session caching."""
from typing import Dict, List, Optional, Any
import json
from model_opt.core.storage.base import StorageBackend
from model_opt.core.exceptions import EnvironmentError

try:
    import redis
    _REDIS_AVAILABLE = True
except ImportError:
    _REDIS_AVAILABLE = False
    redis = None


class RedisBackend(StorageBackend):
    """Redis backend for storage."""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        decode_responses: bool = True
    ):
        """Initialize Redis backend.
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Optional password
            decode_responses: Whether to decode responses
        """
        if not _REDIS_AVAILABLE:
            raise EnvironmentError(
                "redis is not installed. Install with: pip install redis>=5.0"
            )
        
        try:
            self.client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=decode_responses
            )
            # Test connection
            self.client.ping()
        except redis.ConnectionError:
            raise EnvironmentError(f"Failed to connect to Redis at {host}:{port}")
        except Exception as e:
            raise EnvironmentError(f"Redis initialization failed: {e}")
    
    def save(self, key: str, value: Dict[str, Any]) -> bool:
        """Save a value to Redis.
        
        Args:
            key: Storage key
            value: Value to save
            
        Returns:
            True if successful
        """
        try:
            json_str = json.dumps(value)
            self.client.set(key, json_str)
            return True
        except Exception as e:
            print(f"Redis save error: {e}")
            return False
    
    def load(self, key: str) -> Optional[Dict[str, Any]]:
        """Load a value from Redis.
        
        Args:
            key: Storage key
            
        Returns:
            Value if found, None otherwise
        """
        try:
            json_str = self.client.get(key)
            if json_str:
                return json.loads(json_str)
            return None
        except Exception as e:
            print(f"Redis load error: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete a value from Redis.
        
        Args:
            key: Storage key
            
        Returns:
            True if successful
        """
        try:
            return self.client.delete(key) > 0
        except Exception as e:
            print(f"Redis delete error: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if a key exists in Redis.
        
        Args:
            key: Storage key
            
        Returns:
            True if key exists
        """
        try:
            return self.client.exists(key) > 0
        except Exception:
            return False
    
    def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """List all keys in Redis.
        
        Args:
            prefix: Optional prefix to filter keys
            
        Returns:
            List of keys
        """
        try:
            pattern = f"{prefix}*" if prefix else "*"
            keys = [key.decode() if isinstance(key, bytes) else key 
                   for key in self.client.keys(pattern)]
            return keys
        except Exception as e:
            print(f"Redis list_keys error: {e}")
            return []
    
    def clear(self) -> bool:
        """Clear all data from Redis database.
        
        Returns:
            True if successful
        """
        try:
            self.client.flushdb()
            return True
        except Exception as e:
            print(f"Redis clear error: {e}")
            return False
    
    def close(self):
        """Close Redis connection."""
        if hasattr(self, 'client'):
            self.client.close()

