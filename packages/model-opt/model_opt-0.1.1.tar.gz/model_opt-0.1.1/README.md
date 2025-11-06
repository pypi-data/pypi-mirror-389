# Model Optimization Toolkit

[![PyPI version](https://badge.fury.io/py/model-opt.svg)](https://badge.fury.io/py/model-opt)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

A comprehensive toolkit for optimizing neural network models with support for multiple frameworks and research-driven optimization techniques.

## Features

- **Multi-Framework Support**: PyTorch, TensorFlow, Keras, and JAX
- **Model Analysis**: Automatic architecture detection and bottleneck identification
- **Intelligent Optimization**: Hybrid optimization with federated tree knowledge, rule-based caching, and MCTS exploration
- **Research Integration**: Web search for optimization techniques based on model architecture
- **Performance Benchmarking**: Built-in benchmarking and validation tools

## Installation

### Install from PyPI (Recommended)

```bash
# Install the package
pip install model-opt

# Or install with optional dependencies
pip install "model-opt[pytorch]"   # PyTorch support
pip install "model-opt[all]"       # All features
pip install "model-opt[research]"  # Research tools
pip install "model-opt[llm]"       # LLM support
pip install "model-opt[federated]" # Federated tree operations
```

### Install from Source

```bash
# Clone the repository
git clone https://github.com/Ramshankar07/model-opt.git
cd model-opt

# Install in development mode
pip install -e .

# Or install with optional dependencies
pip install -e ".[dev]"       # Development build (includes torch, torchao, torch-pruning)
pip install -e ".[all]"       # All features
pip install -e ".[pytorch]"   # PyTorch support (includes torchao and torch-pruning)
pip install -e ".[research]" # Research tools
pip install -e ".[llm]"       # LLM support (includes VLLM for local serving)
pip install -e ".[federated]" # Federated tree operations
```

**Note:** For development and testing, install the development dependencies:
```bash
pip install -e ".[dev]"  # Includes torch, torchao, torch-pruning, networkx (essential for tests)
```

For full optimization functionality, install PyTorch dependencies:
```bash
pip install -e ".[pytorch]"  # Includes torchao (quantization) and torch-pruning (structured pruning)
```

### Environment Setup

Create a `.env` file in project root for LLM providers (optional):

```
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
TOGETHER_API_KEY=...
```

## Quick Start

### Basic Usage

```python
from model_opt.autotuner import IntelligentOptimizer
import torchvision.models as models

# Load model
model = models.resnet50(pretrained=True)

# Create optimizer
optimizer = IntelligentOptimizer()

# Optimize automatically
optimized_model, result = optimizer.optimize_auto(model)

print(f"Compression: {result.compression_ratio:.2f}x")
print(f"Speedup: {result.speedup:.2f}x")
print(f"Techniques: {[t.value for t in result.techniques]}")
```

### CLI Usage

```bash
# Analyze model
model-opt analyze model.pth

# Optimize with automatic strategy selection
model-opt optimize model.pth \
    --test-dataset data/val/ \
    --test-script evaluate.py

# Research-driven optimization
model-opt research model.pth \
    --test-dataset data/val/ \
    --test-script evaluate.py \
    --max-papers 50
```

## Documentation

### Core Modules

- **[Autotuner](src/model_opt/autotuner/README.md)**: Intelligent optimization with tree search
- **[Tree Search](src/model_opt/tree_search/README.md)**: MCTS implementation and components
- **[Federated Trees](src/model_opt/tree_search/federated/README.md)**: Distributed knowledge sharing
- **[Research Agent](src/model_opt/agent/README.md)**: Research paper search and analysis
- **[Optimization Techniques](src/model_opt/techniques/README.md)**: Quantization, pruning, fusion, decomposition

### Additional Docs

- [Building and Installation Guide](docs/BUILD.md) - Detailed build instructions
- [Package Structure](docs/PACKAGE.md) - Package organization and usage

## Optimization Methods

The toolkit supports three optimization methods:

1. **Hybrid** (default): Intelligent multi-source lookup with federated tree knowledge, local cache, and MCTS exploration
2. **Rule-based**: Fast, uses learned rules and cached results
3. **MCTS**: Monte Carlo Tree Search for exploration and optimization

The default **hybrid** method uses a three-tier lookup strategy:
1. **Federated Tree**: Looks up validated compression strategies from shared knowledge base
2. **Local Cache**: Falls back to previously cached results for similar models
3. **MCTS Exploration**: Uses Monte Carlo Tree Search if no cached results are found

```python
# Use default hybrid method (recommended)
optimized_model, result = optimizer.optimize_auto(model)

# Use hybrid with federated tree from file
optimizer = IntelligentOptimizer(storage_backend="path/to/federated_tree.json")
optimized_model, result = optimizer.optimize_auto(model)

# Use MCTS search only
optimized_model, result = optimizer.optimize_auto(
    model,
    method='mcts',
    n_simulations=50,
    timeout_seconds=300.0
)

# Use rule-based only
optimized_model, result = optimizer.optimize_auto(
    model,
    method='rule'
)
```

**📖 [Detailed Explanation of Optimization Methods](docs/OPTIMIZATION_METHODS.md)** - Complete guide on how each method works, when to use them, and performance characteristics.

## Project Structure

```
model-opt/
├── src/model_opt/
│   ├── core/              # Core optimization engine
│   ├── autotuner/         # Intelligent optimization
│   ├── tree_search/       # MCTS tree search
│   ├── agent/             # Research agents
│   ├── techniques/        # Optimization techniques
│   └── utils/             # Utilities
├── tests/                 # Test scripts
└── docs/                  # Documentation
```

## Test Script Format

Your test script should output metrics in this format:

```python
print(f"accuracy = {accuracy:.1f}")
print(f"inference = {inference_time:.2f}")
```

The script receives these environment variables:
- `MODEL_OPT_MODEL`: Path to your model
- `MODEL_OPT_DATASET`: Path to your test dataset

## Development

```bash
# Run full pipeline test
python tests/test_full_pipeline.py --model resnet50

# Run with LLM support
python tests/test_full_pipeline.py --model resnet50 \
    --llm-provider openai --llm-model gpt-4o-mini
```

## Optional Dependencies

- **`[pytorch]`**: PyTorch, TorchAO, torch-pruning, tomesd, timm
- **`[tensorflow]`**: TensorFlow/Keras support
- **`[research]`**: Web scraping, embeddings, vector DB
- **`[llm]`**: LLM provider clients (OpenAI, Google, Together)
- **`[federated]`**: Federated tree operations (MongoDB, Redis, Neo4j)
- **`[all]`**: All optional dependencies

## License

MIT
