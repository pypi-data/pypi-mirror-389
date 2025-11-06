"""Federated tree operations for distributed knowledge sharing."""
from .operations import FederatedTreeOperations
from .storage import FederatedTreeStorage
from .merge_operations import FederatedMergeOperations
from .conflict_resolver import ConflictResolver
from .manager import FederatedTreeManager

# Optional API client export
try:
    from .api_client import FederatedAPIClient
    _API_CLIENT_AVAILABLE = True
    _EXPORTS = [
        'FederatedTreeOperations',
        'FederatedTreeStorage',
        'FederatedMergeOperations',
        'ConflictResolver',
        'FederatedTreeManager',
        'FederatedAPIClient',
    ]
except ImportError:
    _API_CLIENT_AVAILABLE = False
    FederatedAPIClient = None
    _EXPORTS = [
        'FederatedTreeOperations',
        'FederatedTreeStorage',
        'FederatedMergeOperations',
        'ConflictResolver',
        'FederatedTreeManager',
    ]

__all__ = _EXPORTS

