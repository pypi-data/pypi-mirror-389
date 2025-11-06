# Autotuner / Intelligent Optimization

The autotuner uses Monte Carlo Tree Search (MCTS) to automatically select optimal compression strategies based on model architecture and constraints.

## Basic Usage

```python
from model_opt.autotuner import IntelligentOptimizer
import torch
import torchvision.models as models

# Load your model
model = models.resnet50(pretrained=True)

# Create optimizer
optimizer = IntelligentOptimizer()

# Optimize with automatic strategy selection (rule-based, default)
optimized_model, result = optimizer.optimize_auto(model)

print(f"Compression ratio: {result.compression_ratio:.2f}x")
print(f"Speedup: {result.speedup:.2f}x")
print(f"Accuracy drop: {result.accuracy_drop:.2%}")
print(f"Techniques applied: {[t.value for t in result.techniques]}")
```

## Optimization Methods

The autotuner supports three optimization methods:

1. **Rule-based** (default): Fast, uses learned rules and cached results
2. **MCTS**: Monte Carlo Tree Search for exploration and optimization
3. **Hybrid**: Combines rule-based caching with MCTS exploration

```python
# Use MCTS search for exploration
optimized_model, result = optimizer.optimize_auto(
    model,
    method='mcts',
    n_simulations=50,      # Number of MCTS simulations
    timeout_seconds=300.0   # Maximum search time
)

# Use hybrid method (cached results + MCTS exploration)
optimized_model, result = optimizer.optimize_auto(
    model,
    method='hybrid',
    n_simulations=50
)
```

## Custom Constraints

```python
# Set maximum accuracy drop constraint
constraints = {
    'max_accuracy_drop': 0.02  # Maximum 2% accuracy drop
}

optimized_model, result = optimizer.optimize_auto(
    model,
    constraints=constraints
)
```

## With Example Input

```python
# Provide example input for better benchmarking
example_input = torch.randn(1, 3, 224, 224)

optimized_model, result = optimizer.optimize_auto(
    model,
    example_input=example_input
)
```

## Architecture Detection

The autotuner automatically detects model architecture families:
- **CNN**: Convolutional Neural Networks (ResNet, etc.)
- **ViT**: Vision Transformers
- **HYBRID**: Models with both attention and convolution
- **DIFFUSION**: Diffusion models (Stable Diffusion, etc.)

Each architecture family gets optimized strategies:
- **CNN**: INT8 quantization + structured pruning + layer fusion
- **ViT**: Token merging + INT8 quantization + SVD decomposition
- **HYBRID**: Combination of CNN and ViT techniques
- **DIFFUSION**: Token merging + quantization

## Knowledge Base and Storage

The autotuner maintains a knowledge base that caches optimization results for similar model architectures. This enables fast lookups and learning from previous optimizations.

### Local Storage (JSON)

```python
# Use custom knowledge base path
optimizer = IntelligentOptimizer(knowledge_base_path="my_kb.json")

# The knowledge base is automatically updated after each optimization
# Results are stored with model signatures for fast retrieval
```

### Federated Storage (MongoDB, Redis, Neo4j, ChromaDB)

```python
from model_opt.core.storage import MongoDBBackend, RedisBackend

# Use MongoDB for federated learning
mongo_backend = MongoDBBackend(connection_string="mongodb://localhost:27017")
optimizer = IntelligentOptimizer(storage_backend=mongo_backend)

# Use Redis for fast caching
redis_backend = RedisBackend(host="localhost", port=6379)
optimizer = IntelligentOptimizer(storage_backend=redis_backend)
```

The federated storage enables:
- **Confidence-weighted merging**: Results from multiple sources are merged based on confidence scores
- **Sample count tracking**: Statistical significance tracking for better decisions
- **Cross-system learning**: Share optimization knowledge across deployments

## Components

- **`IntelligentOptimizer`**: Main optimizer class with automatic strategy selection
- **`CompressionTreeSearch`**: Rule-based tree search with knowledge base caching
- **`MCTSEngine`**: Advanced MCTS search (see [Tree Search README](../tree_search/README.md))
- **`ModelSignature`**: Model architecture signature for caching and lookup
- **`CompressionResult`**: Results container with metrics and applied techniques

## See Also

- [Tree Search Documentation](../tree_search/README.md) - MCTS implementation details
- [Federated Trees Documentation](../tree_search/federated/README.md) - Distributed knowledge sharing

