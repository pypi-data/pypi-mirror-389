"""Tests for federated tree operations with API client."""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
import networkx as nx


@pytest.mark.asyncio
async def test_clone_uses_client():
    """Test clone tree uses API client when available."""
    from model_opt.tree_search.federated.operations import FederatedTreeOperations
    
    # Mock API client
    mock_client = AsyncMock()
    mock_client.clone_tree.return_value = {
        "tree": {
            "nodes": [
                {"id": "node1", "architecture": {"family": "CNN"}},
                {"id": "node2", "architecture": {"family": "CNN"}}
            ],
            "edges": [
                {"source": "node1", "target": "node2"}
            ],
            "meta": {}
        }
    }
    
    ops = FederatedTreeOperations(api_client=mock_client)
    tree = await ops.clone_tree_async("transformer", {"depth": 12})
    
    assert isinstance(tree, nx.DiGraph)
    assert tree.number_of_nodes() == 2
    assert tree.number_of_edges() == 1
    mock_client.clone_tree.assert_awaited_once()


@pytest.mark.asyncio
async def test_tree_serialization():
    """Test tree serialization and deserialization."""
    from model_opt.tree_search.federated.operations import FederatedTreeOperations
    
    ops = FederatedTreeOperations()
    
    # Create test tree
    tree = nx.DiGraph()
    tree.add_node("node1", architecture={"family": "CNN"}, performance={"accuracy": 0.95})
    tree.add_node("node2", architecture={"family": "CNN"}, performance={"accuracy": 0.92})
    tree.add_edge("node1", "node2", weight=0.8)
    tree.graph["federated_id"] = "test-tree-123"
    
    # Serialize
    serialized = ops._serialize_tree(tree)
    
    assert "nodes" in serialized
    assert "edges" in serialized
    assert "meta" in serialized
    assert len(serialized["nodes"]) == 2
    assert len(serialized["edges"]) == 1
    assert serialized["meta"]["federated_id"] == "test-tree-123"
    
    # Deserialize
    deserialized = ops._deserialize_tree(serialized)
    
    assert isinstance(deserialized, nx.DiGraph)
    assert deserialized.number_of_nodes() == 2
    assert deserialized.number_of_edges() == 1
    assert deserialized.graph["federated_id"] == "test-tree-123"
    assert deserialized.nodes["node1"]["architecture"]["family"] == "CNN"


def test_fallback_to_storage():
    """Test fallback to storage when API client unavailable."""
    from model_opt.tree_search.federated.operations import FederatedTreeOperations
    
    # Mock storage backend
    mock_storage = MagicMock()
    mock_storage.load.return_value = {
        "nodes": {
            "node1": {"architecture": {"family": "CNN"}}
        },
        "edges": []
    }
    
    ops = FederatedTreeOperations(storage_backend=mock_storage)
    tree = ops.clone_tree("CNN", {})
    
    assert isinstance(tree, nx.DiGraph)
    # Should have tried to load from storage
    assert mock_storage.load.called


@pytest.mark.asyncio
async def test_expand_tree_with_papers():
    """Test expand tree with papers from API."""
    from model_opt.tree_search.federated.operations import FederatedTreeOperations
    
    mock_client = AsyncMock()
    mock_client.expand_tree.return_value = {
        "new_nodes": [
            {"id": "new_node1", "architecture": {"family": "CNN"}},
            {"id": "new_node2", "architecture": {"family": "CNN"}}
        ]
    }
    
    ops = FederatedTreeOperations(api_client=mock_client)
    tree = nx.DiGraph()
    tree.graph["federated_id"] = "test-tree"
    tree.add_node("existing_node")
    
    expanded_tree, new_count = await ops.expand_tree_with_papers_async(tree, "CNN")
    
    assert expanded_tree.number_of_nodes() == 3  # 1 existing + 2 new
    assert new_count == 2
    mock_client.expand_tree.assert_awaited_once()

