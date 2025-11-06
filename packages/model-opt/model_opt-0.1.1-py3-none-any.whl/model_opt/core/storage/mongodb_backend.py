"""MongoDB backend for federated tree persistence."""
from typing import Dict, List, Optional, Any
from model_opt.core.storage.base import StorageBackend
from model_opt.core.exceptions import EnvironmentError

try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, PyMongoError
    _MONGODB_AVAILABLE = True
except ImportError:
    _MONGODB_AVAILABLE = False
    MongoClient = None


class MongoDBBackend(StorageBackend):
    """MongoDB backend for storage."""
    
    def __init__(
        self,
        connection_string: str = "mongodb://localhost:27017/",
        database_name: str = "model_opt",
        collection_name: str = "compression_tree"
    ):
        """Initialize MongoDB backend.
        
        Args:
            connection_string: MongoDB connection string
            database_name: Database name
            collection_name: Collection name
        """
        if not _MONGODB_AVAILABLE:
            raise EnvironmentError(
                "pymongo is not installed. Install with: pip install pymongo>=4.0"
            )
        
        try:
            self.client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client[database_name]
            self.collection = self.db[collection_name]
        except ConnectionFailure:
            raise EnvironmentError(f"Failed to connect to MongoDB at {connection_string}")
        except Exception as e:
            raise EnvironmentError(f"MongoDB initialization failed: {e}")
    
    def save(self, key: str, value: Dict[str, Any]) -> bool:
        """Save a value to MongoDB.
        
        Args:
            key: Storage key
            value: Value to save
            
        Returns:
            True if successful
        """
        try:
            document = {'_id': key, **value}
            self.collection.replace_one({'_id': key}, document, upsert=True)
            return True
        except PyMongoError as e:
            print(f"MongoDB save error: {e}")
            return False
    
    def load(self, key: str) -> Optional[Dict[str, Any]]:
        """Load a value from MongoDB.
        
        Args:
            key: Storage key
            
        Returns:
            Value if found, None otherwise
        """
        try:
            document = self.collection.find_one({'_id': key})
            if document:
                # Remove _id from result
                document.pop('_id', None)
                return document
            return None
        except PyMongoError as e:
            print(f"MongoDB load error: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete a value from MongoDB.
        
        Args:
            key: Storage key
            
        Returns:
            True if successful
        """
        try:
            result = self.collection.delete_one({'_id': key})
            return result.deleted_count > 0
        except PyMongoError as e:
            print(f"MongoDB delete error: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if a key exists in MongoDB.
        
        Args:
            key: Storage key
            
        Returns:
            True if key exists
        """
        try:
            return self.collection.count_documents({'_id': key}) > 0
        except PyMongoError:
            return False
    
    def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """List all keys in MongoDB.
        
        Args:
            prefix: Optional prefix to filter keys
            
        Returns:
            List of keys
        """
        try:
            query = {}
            if prefix:
                query['_id'] = {'$regex': f'^{prefix}'}
            
            keys = [doc['_id'] for doc in self.collection.find(query, {'_id': 1})]
            return keys
        except PyMongoError as e:
            print(f"MongoDB list_keys error: {e}")
            return []
    
    def clear(self) -> bool:
        """Clear all data from MongoDB collection.
        
        Returns:
            True if successful
        """
        try:
            self.collection.delete_many({})
            return True
        except PyMongoError as e:
            print(f"MongoDB clear error: {e}")
            return False
    
    def close(self):
        """Close MongoDB connection."""
        if hasattr(self, 'client'):
            self.client.close()

