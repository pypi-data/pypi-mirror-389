# Federated Tree Operations

## API Submodule

This directory contains a git submodule pointing to the federated API service:

- **Submodule Path**: `src/model_opt/tree_search/federated/model-opt-api/`
- **Repository**: <https://github.com/Ramshankar07/model-opt-api.git>
- **Production API**: <https://model-opt-api-production-06d6.up.railway.app>

### Working with the Submodule

**Initial Setup** (for new clones):
```bash
# Clone repository with submodules
git clone --recurse-submodules <repository-url>

# Or if already cloned, initialize submodules
git submodule update --init --recursive
```

**Updating the Submodule**:
```bash
# Update to latest version
cd src/model_opt/tree_search/federated/model-opt-api
git pull origin main
cd ../../../../../../

# Or update from parent directory
git submodule update --remote src/model_opt/tree_search/federated/model-opt-api
```

**Making Changes to API**:
```bash
# Navigate to submodule
cd src/model_opt/tree_search/federated/model-opt-api

# Make changes and commit (in submodule repo)
git add .
git commit -m "Your changes"
git push origin main

# Return to parent repo and update submodule reference
cd ../../../../../
git add src/model_opt/tree_search/federated/model-opt-api
git commit -m "Update federated API submodule"
```

Note: The submodule is a separate repository. Changes should be committed in the submodule repository first, then the parent repository should be updated to reference the new commit.

# Federated Tree Operations

NetworkX-based tree management for distributed knowledge sharing across multiple optimization deployments.

## Overview

The federated tree system enables:
- **Tree cloning**: Filter federated knowledge by architecture and constraints
- **Paper expansion**: Automatically add nodes from research papers via vector DB
- **Change detection**: Identify significant weight changes and new discoveries
- **Confidence-weighted merging**: Merge local and federated results based on sample counts and validation quality
- **Statistical conflict resolution**: Use Welch's t-test to resolve significant disagreements
- **Multi-backend storage**: Support for MongoDB, Redis, and Neo4j

## Basic Usage

```python
from model_opt.tree_search import FederatedTreeManager
from model_opt.core.storage import MongoDBBackend
from model_opt.utils.vecdb import LocalVecDB

# Initialize storage backend
mongo_backend = MongoDBBackend(connection_string="mongodb://localhost:27017/")

# Initialize vector DB for paper expansion (optional)
vector_db = LocalVecDB(db_dir="rag_store")

# Create federated tree manager
tree_manager = FederatedTreeManager(
    storage_backend=mongo_backend,
    vector_db=vector_db,
    change_threshold=0.15,
    conflict_threshold=0.3
)

# Initialize local tree from federated knowledge
local_tree = tree_manager.initialize_local_tree(
    architecture_family="ResNet",
    user_constraints={
        'min_accuracy_retention': 0.95,
        'target_hardware': 'edge'
    }
)

# Sync with federated tree (merges local discoveries)
merged_tree, sync_report = tree_manager.sync_with_federated(
    local_tree,
    auto_resolve=True  # Auto-resolve conflicts using statistical testing
)

print(f"Merged {sync_report['merged_nodes']} nodes")
print(f"Detected {len(sync_report['changes_detected']['new_nodes'])} new nodes")
```

## Components

### FederatedTreeManager

Main orchestrator for tree operations:

```python
from model_opt.tree_search.federated import FederatedTreeManager

tree_manager = FederatedTreeManager(
    storage_backend=storage_backend,
    vector_db=vector_db,
    change_threshold=0.15,      # Threshold for significant changes
    conflict_threshold=0.3,     # Threshold for conflicts requiring resolution
    merge_confidence_cap=[0.1, 0.7]  # Min/max confidence for merging
)
```

### FederatedTreeOperations

Tree cloning, pruning, and expansion:

```python
from model_opt.tree_search.federated import FederatedTreeOperations

operations = FederatedTreeOperations(
    storage_backend=storage_backend,
    vector_db=vector_db
)

# Clone tree for specific architecture
local_tree = operations.clone_tree(
    architecture_family="ResNet",
    user_constraints={'min_accuracy_retention': 0.95}
)

# Prune irrelevant nodes
pruned_tree = operations.prune_irrelevant_nodes(
    local_tree,
    architecture="ResNet",
    constraints={'target_hardware': 'edge'}
)

# Expand tree with papers from vector DB
expanded_tree, new_nodes = operations.expand_tree_with_papers(
    pruned_tree,
    architecture="ResNet",
    vector_db=vector_db
)
```

### FederatedTreeStorage

NetworkX graph serialization and persistence:

```python
from model_opt.tree_search.federated import FederatedTreeStorage

storage = FederatedTreeStorage(storage_backend)

# Save tree to storage
storage.save_tree(local_tree, tree_id="resnet_compression_tree")

# Load tree from storage
loaded_tree = storage.load_tree(tree_id="resnet_compression_tree")

# List all trees
tree_ids = storage.list_trees()
```

### FederatedMergeOperations

Change detection and weighted merging:

```python
from model_opt.tree_search.federated import FederatedMergeOperations

merge_ops = FederatedMergeOperations()

# Detect changes between local and federated trees
changes = merge_ops.detect_changes(local_tree, federated_tree)

# Compute merge confidence
confidence = merge_ops.compute_merge_confidence(
    local_stats={'sample_count': 10, 'variance': 0.02},
    fed_stats={'sample_count': 50, 'validators': 5}
)

# Merge edge weights
merged_weight = merge_ops.merge_edge_weight(
    local_edge=edge_data,
    fed_edge=fed_edge_data,
    beta=confidence['merge_weight_beta']
)
```

### ConflictResolver

Statistical testing for conflict resolution:

```python
from model_opt.tree_search.federated import ConflictResolver

resolver = ConflictResolver()

# Resolve conflict using Welch's t-test
resolution = resolver.resolve_conflict(
    local_edge=local_edge_data,
    fed_edge=fed_edge_data
)

if resolution['action'] == 'accept_local':
    print("Local result is statistically significant")
elif resolution['action'] == 'keep_federated':
    print("Insufficient evidence, keeping federated result")
elif resolution['action'] == 'request_validation':
    print(f"Need {resolution['required_samples']} more samples")
```

## Conflict Resolution

The system automatically resolves conflicts using statistical testing:

### Welch's t-test

Determines if local improvements are statistically significant:

```python
# Large delta between local and federated
delta = abs(local_weight - fed_weight)  # > 0.3

# Perform Welch's t-test
resolution = resolver.resolve_conflict(local_edge, fed_edge)

if resolution['p_value'] < 0.05:
    # Statistically significant difference
    if local_samples >= 20:
        # Accept local result
        resolution['action'] = 'accept_local'
    else:
        # Request more samples
        resolution['action'] = 'request_validation'
else:
    # Not significant, keep federated
    resolution['action'] = 'keep_federated'
```

### Sample Count Weighting

Local results with more samples get higher weight:

```python
confidence = merge_ops.compute_merge_confidence(
    local_stats={'sample_count': 20, 'variance': 0.01},
    fed_stats={'sample_count': 5, 'validators': 1}
)

# beta = confidence_local / (confidence_local + confidence_fed)
# Higher local samples → higher beta → more weight to local result
```

### Validator Diversity

Federated results validated by multiple sources get higher confidence:

```python
confidence = merge_ops.compute_merge_confidence(
    local_stats={'sample_count': 10},
    fed_stats={'sample_count': 10, 'validators': 5}  # 5 validators
)

# Higher validator count → higher confidence_fed → more weight to federated
```

### Auto-merge Thresholds

- **Small differences** (< 0.3): Automatically merged
- **Large conflicts** (> 0.3): Statistically tested
- **Very large conflicts** (> 0.5): Flagged for manual review

## Paper-Based Expansion

The tree can be expanded with nodes from research papers:

```python
# Papers are automatically queried from vector DB
# based on architecture and compression keywords
tree, new_nodes = tree_manager.operations.expand_tree_with_papers(
    local_tree,
    architecture="ResNet",
    vector_db=vector_db
)

print(f"Added {new_nodes} new nodes from research papers")
```

The expansion process:
1. Queries vector DB for relevant papers using architecture + compression keywords
2. Extracts techniques from paper metadata
3. Creates new nodes with low confidence (until validated)
4. Connects to compatible parent nodes based on technique compatibility

## Installation

```bash
# Install with federated tree support
pip install -e ".[federated]"

# Includes:
# - pymongo>=4.0 (MongoDB)
# - redis>=5.0 (Redis caching)
# - neo4j>=5.0 (Graph database, optional)
# - networkx>=3.1 (Graph operations)
# - numpy>=1.21 (Statistical operations)
# - scipy>=1.9 (t-distribution for conflict resolution)
```

## Configuration

```python
from model_opt.core.config import FEDERATED_CONFIG

# Default configuration
FEDERATED_CONFIG = {
    'mongodb_uri': 'mongodb://localhost:27017/',
    'redis_uri': 'redis://localhost:6379/',
    'neo4j_uri': 'bolt://localhost:7687',
    'change_threshold': 0.15,
    'conflict_threshold': 0.3,
    'merge_confidence_cap': [0.1, 0.7],
    'tree_collection': 'compression_trees'
}
```

## Storage Backends

### MongoDB

```python
from model_opt.core.storage import MongoDBBackend

backend = MongoDBBackend(connection_string="mongodb://localhost:27017/")
tree_manager = FederatedTreeManager(storage_backend=backend)
```

### Redis

```python
from model_opt.core.storage import RedisBackend

backend = RedisBackend(host="localhost", port=6379)
tree_manager = FederatedTreeManager(storage_backend=backend)
```

### Neo4j

```python
from model_opt.core.storage import Neo4jBackend

backend = Neo4jBackend(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="password"
)
tree_manager = FederatedTreeManager(storage_backend=backend)
```

## See Also

- [MCTS Tree Search Documentation](../README.md) - MCTS implementation details
- [Autotuner Documentation](../../autotuner/README.md) - High-level usage

