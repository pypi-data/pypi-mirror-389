"""Abstract base class for storage backends."""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class StorageBackend(ABC):
    """Abstract base class for storage backends."""
    
    @abstractmethod
    def save(self, key: str, value: Dict[str, Any]) -> bool:
        """Save a value to storage.
        
        Args:
            key: Storage key
            value: Value to save (must be JSON-serializable)
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def load(self, key: str) -> Optional[Dict[str, Any]]:
        """Load a value from storage.
        
        Args:
            key: Storage key
            
        Returns:
            Value if found, None otherwise
        """
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a value from storage.
        
        Args:
            key: Storage key
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if a key exists in storage.
        
        Args:
            key: Storage key
            
        Returns:
            True if key exists
        """
        pass
    
    @abstractmethod
    def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """List all keys in storage.
        
        Args:
            prefix: Optional prefix to filter keys
            
        Returns:
            List of keys
        """
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        """Clear all data from storage.
        
        Returns:
            True if successful
        """
        pass

