"""HTTP API client for federated tree operations."""
from __future__ import annotations

from typing import Dict, Optional, Any
import os

try:
    import httpx
    _HTTPX_AVAILABLE = True
except ImportError:
    _HTTPX_AVAILABLE = False
    httpx = None


class FederatedAPIClient:
    """HTTP client for federated tree API operations."""

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: float = 30.0
    ):
        """Initialize federated API client.

        Args:
            base_url: Base URL of the federated API service
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
        """
        if not _HTTPX_AVAILABLE:
            raise ImportError(
                "httpx is required for FederatedAPIClient. "
                "Install with: pip install httpx"
            )

        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers=headers,
            timeout=timeout
        )

    async def __aenter__(self) -> "FederatedAPIClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        """Async context manager exit."""
        await self.client.aclose()

    async def clone_tree(self, architecture_family: str, constraints: Dict) -> Dict:
        """Clone tree from federated API.

        Args:
            architecture_family: Target architecture family
            constraints: User constraints dict

        Returns:
            Response JSON with tree data

        Raises:
            httpx.HTTPError: If API request fails
        """
        response = await self.client.post(
            "/api/v1/trees/clone",
            json={"architecture": architecture_family, "constraints": constraints},
        )
        response.raise_for_status()
        return response.json()

    async def expand_tree(self, tree_id: str, architecture: str) -> Dict:
        """Expand tree with papers from federated API.

        Args:
            tree_id: Tree identifier
            architecture: Architecture family

        Returns:
            Response JSON with new nodes

        Raises:
            httpx.HTTPError: If API request fails
        """
        response = await self.client.post(
            f"/api/v1/trees/{tree_id}/expand",
            json={"architecture": architecture},
        )
        response.raise_for_status()
        return response.json()

    async def sync_changes(self, tree_id: str, local_tree: Dict, changes: Dict) -> Dict:
        """Sync local changes to federated API.

        Args:
            tree_id: Tree identifier
            local_tree: Serialized local tree
            changes: Changes dictionary

        Returns:
            Response JSON with sync result

        Raises:
            httpx.HTTPError: If API request fails
        """
        response = await self.client.put(
            f"/api/v1/trees/{tree_id}/sync",
            json={"local_tree": local_tree, "changes": changes},
        )
        response.raise_for_status()
        return response.json()

    async def merge_changes(self, tree_id: str, local_tree: Dict, changes: Dict) -> Dict:
        """Merge changes with federated tree.

        Args:
            tree_id: Tree identifier
            local_tree: Serialized local tree
            changes: Changes dictionary

        Returns:
            Response JSON with merged tree

        Raises:
            httpx.HTTPError: If API request fails
        """
        response = await self.client.post(
            f"/api/v1/trees/{tree_id}/merge",
            json={"local_tree": local_tree, "changes": changes},
        )
        response.raise_for_status()
        return response.json()

    async def get_sample_tree(self) -> Dict:
        """Get sample tree from federated API.

        Returns:
            Response JSON with sample tree data

        Raises:
            httpx.HTTPError: If API request fails
        """
        response = await self.client.get("/api/v1/trees/sample")
        response.raise_for_status()
        return response.json()

    async def import_tree(self, tree_data: Dict) -> Dict:
        """Import legacy tree format to federated API.

        Args:
            tree_data: Legacy tree data (nodes, edges, metadata)

        Returns:
            Response JSON with imported tree_id

        Raises:
            httpx.HTTPError: If API request fails
        """
        response = await self.client.post(
            "/api/v1/trees/import",
            json=tree_data,
        )
        response.raise_for_status()
        return response.json()

    async def health_check(self) -> Dict:
        """Check API health.

        Returns:
            Response JSON with health status

        Raises:
            httpx.HTTPError: If API request fails
        """
        response = await self.client.get("/health")
        response.raise_for_status()
        return response.json()

