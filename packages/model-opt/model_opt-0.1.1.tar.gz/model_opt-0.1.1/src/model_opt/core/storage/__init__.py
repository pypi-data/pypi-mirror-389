"""Storage backends for tree search persistence."""
from typing import Optional

from .base import StorageBackend

try:
    from .mongodb_backend import MongoDBBackend
    _MONGODB_AVAILABLE = True
except ImportError:
    _MONGODB_AVAILABLE = False
    MongoDBBackend = None

try:
    from .redis_backend import RedisBackend
    _REDIS_AVAILABLE = True
except ImportError:
    _REDIS_AVAILABLE = False
    RedisBackend = None

try:
    from .neo4j_backend import Neo4jBackend
    _NEO4J_AVAILABLE = True
except ImportError:
    _NEO4J_AVAILABLE = False
    Neo4jBackend = None

try:
    from .chromadb_backend import ChromaDBBackend
    _CHROMADB_AVAILABLE = True
except (ImportError, AttributeError):
    # ImportError: chromadb not installed
    # AttributeError: chromadb incompatible with numpy 2.0 (np.float_ removed)
    _CHROMADB_AVAILABLE = False
    ChromaDBBackend = None

__all__ = [
    'StorageBackend',
    'MongoDBBackend',
    'RedisBackend',
    'Neo4jBackend',
    'ChromaDBBackend',
    '_MONGODB_AVAILABLE',
    '_REDIS_AVAILABLE',
    '_NEO4J_AVAILABLE',
    '_CHROMADB_AVAILABLE',
]

