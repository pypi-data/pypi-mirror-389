# MCTS Tree Search

Monte Carlo Tree Search (MCTS) implementation for compression strategy optimization.

## Overview

The MCTS engine provides advanced exploration and optimization capabilities beyond rule-based search. It uses zero-shot evaluation, federated learning, and architecture-specific priors.

## Features

- **Zero-shot evaluation**: Fast rollout evaluation without validation data
- **Federated learning**: Confidence-weighted merging from multiple sources
- **Architecture priors**: Intelligent prior probabilities based on model family
- **Knowledge base integration**: Learns from previous optimizations
- **Federated tree operations**: NetworkX-based tree management with distributed knowledge sharing

## Components

### MCTSEngine

Main orchestrator with selection, expansion, simulation, and backpropagation:

```python
from model_opt.tree_search import MCTSEngine
from model_opt.autotuner.search_space import ModelSignature, ArchitectureFamily

# Create MCTS engine
mcts_engine = MCTSEngine(
    tree_search=compression_tree_search,
    storage_backend=storage_backend,
    n_simulations=50,
    timeout_seconds=300.0
)

# Run search
signature = ModelSignature(
    family=ArchitectureFamily.CNN,
    total_params=25000000,
    num_layers=50,
    has_attention=False,
    has_conv=True
)

techniques, result = mcts_engine.search(
    model,
    signature,
    constraints={'max_accuracy_drop': 0.05},
    example_input=example_input
)
```

### ZeroShotRollout

Fast evaluation using proxy metrics (compression ratio, speedup estimation):

```python
from model_opt.tree_search import ZeroShotRollout

rollout = ZeroShotRollout()
result = rollout.evaluate(
    model,
    techniques=[CompressionTechnique.QUANTIZE_INT8, CompressionTechnique.PRUNE_STRUCTURED],
    example_input=example_input
)

# Returns estimated compression_ratio, speedup, accuracy_drop
```

### FederatedStorage

Confidence-weighted result merging from storage backends:

```python
from model_opt.tree_search import FederatedStorage
from model_opt.core.storage import MongoDBBackend

storage_backend = MongoDBBackend(connection_string="mongodb://localhost:27017/")
federated = FederatedStorage(storage_backend)

# Update result with confidence weighting
federated.update_result(signature, technique, compression_result)

# Get merged results
merged_result = federated.get_result(signature, technique)
```

### ArchitecturePriors

Architecture-specific probability distributions for techniques:

```python
from model_opt.tree_search import ArchitecturePriors

priors = ArchitecturePriors()

# Get prior probabilities for CNN architecture
cnn_priors = priors.get_priors(ArchitectureFamily.CNN)

# Get prior for specific technique
quantize_prior = priors.get_technique_prior(
    ArchitectureFamily.CNN,
    CompressionTechnique.QUANTIZE_INT8
)
```

### EnhancedSearchNode

Search nodes with Q-values, confidence scores, and priors:

```python
from model_opt.tree_search import EnhancedSearchNode
from model_opt.autotuner.search_space import CompressionTechnique

# Create node
node = EnhancedSearchNode(
    signature=signature,
    techniques_applied=[CompressionTechnique.QUANTIZE_INT8],
    parent=None
)

# Update from result
node.update_from_result(compression_result)

# Get UCB score with prior
ucb_score = node.ucb_score_with_prior(exploration_weight=1.41)
```

## Integration with IntelligentOptimizer

The MCTS engine is automatically used when `method='mcts'` or `method='hybrid'`:

```python
from model_opt.autotuner import IntelligentOptimizer

optimizer = IntelligentOptimizer()

# Use MCTS search
optimized_model, result = optimizer.optimize_auto(
    model,
    method='mcts',
    n_simulations=50,
    timeout_seconds=300.0
)

# Use hybrid (cached + MCTS)
optimized_model, result = optimizer.optimize_auto(
    model,
    method='hybrid'
)
```

## Federated Tree Integration

The MCTS engine can optionally use federated tree operations for NetworkX-based tree management:

```python
from model_opt.tree_search import MCTSEngine, FederatedTreeManager
from model_opt.core.storage import MongoDBBackend
from model_opt.utils.vecdb import LocalVecDB

mongo_backend = MongoDBBackend(connection_string="mongodb://localhost:27017/")
vector_db = LocalVecDB(db_dir="rag_store")
tree_manager = FederatedTreeManager(storage_backend=mongo_backend, vector_db=vector_db)

# Initialize MCTS with federated tree manager
mcts_engine = MCTSEngine(
    storage_backend=mongo_backend,
    federated_tree_manager=tree_manager,
    vector_db=vector_db  # Optional: for paper expansion
)
```

## See Also

- [Federated Tree Operations](federated/README.md) - Detailed federated tree documentation
- [Autotuner Documentation](../autotuner/README.md) - High-level usage

