# Optimization Techniques

This module provides various optimization techniques for neural network models: quantization, pruning, layer fusion, and decomposition.

## Quantization

### TorchAO Quantization (Weight-only or Dynamic)

```bash
model-opt optimize model.pth \
  --test-dataset data/ \
  --test-script eval.py \
  --quantize --quant-method int8_weight_only
```

```python
from model_opt.techniques import Quantizer

quantizer = Quantizer()
model, info = quantizer.quantize(
    model,
    method='int8_weight_only',
    example_input=input_tensor
)
```

### Autoquantization

Automatic method selection:

```python
from model_opt.techniques import Quantizer

quantizer = Quantizer()
model, info = quantizer.quantize(
    model,
    method='autoquant',
    example_input=input_tensor
)
```

### Backends

- **TorchAO**: `int8_weight_only`, `int8_dynamic`, `autoquant`
- **NNCF**: Quantization with calibration
- **Intel Neural Compressor**: Cross-platform quantization

## Pruning

### Unstructured Pruning

Local per-layer pruning:

```bash
model-opt optimize model.pth \
  --test-dataset data/ \
  --test-script eval.py \
  --prune --prune-backend basic --prune-amount 0.5 --prune-criterion l1
```

```python
from model_opt.techniques import Pruner

pruner = Pruner()
pruned_model = pruner.prune_model(
    model,
    amount=0.5,
    criterion='l1',
    prune_type='unstructured'
)
```

### Structured Pruning (torch-pruning)

```bash
model-opt optimize model.pth \
  --test-dataset data/ \
  --test-script eval.py \
  --prune --prune-backend torch-pruning --prune-amount 0.3 --prune-criterion magnitude
```

```python
from model_opt.techniques import Pruner

pruner = Pruner()
pruned_model = pruner.prune_model(
    model,
    amount=0.3,
    criterion='magnitude',
    prune_type='structured',
    example_input=input_tensor  # Required for structured pruning
)
```

### Stable Diffusion Token Merging

```python
from model_opt.techniques.pruning.pruning_sd import StableDiffusionPruner

pruner = StableDiffusionPruner()
model = pruner.apply_patch(model, ratio=0.5)
```

### Vision Transformer Token Merging

```python
from model_opt.techniques.pruning.pruning_vit_tome import ViTToMePruner
import timm

pruner = ViTToMePruner()
model = timm.create_model("vit_base_patch16_224", pretrained=True)
model = pruner.apply_patch(model, r=16)
```

### Backends

- **torch-pruning**: Structured pruning with DepGraph
- **NNCF**: Pruning with fine-tuning
- **Basic**: Unstructured magnitude-based pruning

## Layer Fusion

### Conv-BN-ReLU Fusion

```python
from model_opt.techniques import LayerFuser

fuser = LayerFuser()
fused_model = fuser.fuse_conv_bn_relu(model)
```

### Linear-GELU Fusion

```python
fused_model = fuser.fuse_linear_gelu(model)
```

### Multiple Fusion Types

```python
fused_model = fuser.fuse_model(
    model,
    fusion_types=['conv_bn_relu', 'linear_gelu']
)
```

## Decomposition

### SVD Decomposition

```python
from model_opt.techniques import Decomposer

decomposer = Decomposer()
decomposed_model = decomposer.decompose_model(
    model,
    method='svd',
    rank_ratio=0.5
)
```

## Combined Techniques

Apply multiple techniques in sequence:

```bash
model-opt optimize model.pth \
  --test-dataset data/ \
  --test-script eval.py \
  --prune --prune-amount 0.3 \
  --quantize --quant-method int8_dynamic
```

```python
from model_opt.techniques import Quantizer, Pruner, LayerFuser

# Apply pruning
pruner = Pruner()
model = pruner.prune_model(model, amount=0.3, criterion='magnitude')

# Apply quantization
quantizer = Quantizer()
model, info = quantizer.quantize(model, method='int8_dynamic', example_input=input_tensor)

# Apply layer fusion
fuser = LayerFuser()
model = fuser.fuse_conv_bn_relu(model)
```

## Architecture-Specific Recommendations

### CNN (ResNet, etc.)

- **Quantization**: INT8 weight-only or dynamic
- **Pruning**: Structured pruning (0.3-0.5 ratio)
- **Fusion**: Conv-BN-ReLU fusion
- **Decomposition**: SVD (rank_ratio=0.5)

### Vision Transformers (ViT)

- **Quantization**: INT8 weight-only
- **Pruning**: Token merging (ToMe, r=16)
- **Decomposition**: SVD for attention layers

### Hybrid Models

- **Quantization**: INT8 dynamic
- **Pruning**: Structured for CNN parts, token merging for attention
- **Fusion**: Conv-BN-ReLU where applicable

### Diffusion Models (Stable Diffusion)

- **Quantization**: INT8 weight-only
- **Pruning**: Token merging (ToMeSD)

## Components

### Quantizer

Main quantization interface:

```python
from model_opt.techniques import Quantizer

quantizer = Quantizer()
model, info = quantizer.quantize(model, method='int8_weight_only', example_input=input_tensor)
```

### Pruner

Main pruning interface:

```python
from model_opt.techniques import Pruner

pruner = Pruner()
pruned_model = pruner.prune_model(
    model,
    amount=0.5,
    criterion='magnitude',
    prune_type='structured',
    example_input=input_tensor
)
```

### LayerFuser

Layer fusion interface:

```python
from model_opt.techniques import LayerFuser

fuser = LayerFuser()
fused_model = fuser.fuse_model(model, fusion_types=['conv_bn_relu', 'linear_gelu'])
```

### Decomposer

Decomposition interface:

```python
from model_opt.techniques import Decomposer

decomposer = Decomposer()
decomposed_model = decomposer.decompose_model(model, method='svd', rank_ratio=0.5)
```

## Backend Details

### Quantization Backends

- **TorchAO**: `quantize_torch.py` - Weight-only and dynamic quantization
- **NNCF**: `nncf/nncf_quantizer.py` - Calibration-based quantization
- **Intel Neural Compressor**: `neural_compressor/inc_optimizer.py` - Cross-platform quantization

### Pruning Backends

- **torch-pruning**: `pruning/pruning_torch.py` - Structured pruning with DepGraph
- **Basic**: `pruning/pruning_unstructured_torch.py` - Unstructured magnitude pruning
- **ToMeSD**: `pruning/pruning_sd.py` - Stable Diffusion token merging
- **ToMe**: `pruning/pruning_vit_tome.py` - Vision Transformer token merging
- **NNCF**: `nncf/nncf_pruner.py` - Pruning with fine-tuning

### Fusion Backends

- **Conv-BN-ReLU**: `fusion/fusion_conv_bn_relu.py` - Convolution-BatchNorm-ReLU fusion
- **Linear-GELU**: `fusion/fusion_linear_gelu.py` - Linear-GELU fusion

### Decomposition Backends

- **SVD**: `decomposition/decomposition_svd.py` - Singular Value Decomposition

## See Also

- [Autotuner Documentation](../autotuner/README.md) - Automatic technique selection
- [CLI Usage](../../cli.py) - Command-line interface

