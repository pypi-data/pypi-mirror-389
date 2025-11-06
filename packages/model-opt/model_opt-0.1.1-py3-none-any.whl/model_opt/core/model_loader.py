"""Model loader and analysis utilities supporting multiple frameworks."""
import os
import sys
import subprocess
from pathlib import Path
from collections import Counter
from typing import Dict, List, Any, Tuple


def get_hardware_info():
    """Detect available hardware."""
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
            return f"NVIDIA {gpu_name} ({gpu_memory:.0f}GB VRAM)"
    except ImportError:
        pass
    return "CPU"


def detect_framework(model_path: str) -> str:
    """Detect model framework based on file extension."""
    ext = Path(model_path).suffix.lower()
    
    if ext in ['.pth', '.pt', '.pkl']:
        return 'pytorch'
    elif ext in ['.h5', '.keras']:
        return 'keras'
    elif ext == '.pb':
        return 'tensorflow'
    elif ext in ['.ckpt', '.jax']:
        return 'jax'
    else:
        # Default to PyTorch for common cases
        return 'pytorch'


def load_model(model_path: str) -> Tuple[Any, str]:
    """Load model from any supported framework."""
    framework = detect_framework(model_path)
    
    if framework == 'pytorch':
        return load_pytorch_model(model_path), framework
    elif framework == 'keras':
        return load_keras_model(model_path), framework
    elif framework == 'tensorflow':
        return load_tensorflow_model(model_path), framework
    elif framework == 'jax':
        return load_jax_model(model_path), framework
    else:
        raise ValueError(f"Unsupported framework: {framework}")


def load_pytorch_model(model_path: str):
    """Load PyTorch model."""
    try:
        import torch
        model = torch.load(model_path, map_location='cpu')
        if hasattr(model, 'eval'):
            model.eval()
        return model
    except Exception as e:
        raise ValueError(f"Failed to load PyTorch model: {e}")


def load_keras_model(model_path: str):
    """Load Keras model."""
    try:
        from tensorflow import keras
        model = keras.models.load_model(model_path)
        return model
    except ImportError:
        try:
            import keras
            model = keras.models.load_model(model_path)
            return model
        except Exception as e:
            raise ValueError(f"Failed to load Keras model: {e}")
    except Exception as e:
        raise ValueError(f"Failed to load Keras model: {e}")


def load_tensorflow_model(model_path: str):
    """Load TensorFlow SavedModel or Frozen Graph."""
    try:
        import tensorflow as tf
        model = tf.keras.models.load_model(model_path)
        return model
    except Exception as e:
        raise ValueError(f"Failed to load TensorFlow model: {e}")


def load_jax_model(model_path: str):
    """Load JAX model."""
    try:
        import jax
        import pickle
        with open(model_path, 'rb') as f:
            params = pickle.load(f)
        return params
    except Exception as e:
        raise ValueError(f"Failed to load JAX model: {e}")


def run_test_script(test_script: str, model_path: str, test_dataset: str) -> Dict[str, float]:
    """Run test script and capture metrics."""
    try:
        if not os.path.exists(test_script):
            print(f"Warning: Test script not found: {test_script}")
            return {}
        
        # Run test script
        env = os.environ.copy()
        env['MODEL_OPT_MODEL'] = model_path
        env['MODEL_OPT_DATASET'] = test_dataset
        
        result = subprocess.run(
            [sys.executable, test_script],
            capture_output=True,
            text=True,
            env=env,
            cwd=os.path.dirname(test_script) or '.'
        )
        
        if result.returncode != 0:
            print(f"Warning: Test script failed: {result.stderr}")
            return {}
        
        metrics = {}
        for line in result.stdout.split('\n'):
            if '=' in line:
                parts = line.split('=')
                if len(parts) == 2:
                    key = parts[0].strip().lower()
                    try:
                        value = float(parts[1].strip())
                        metrics[key] = value
                    except ValueError:
                        pass
        
        mapped_metrics = {}
        if 'inference' in metrics:
            mapped_metrics['inference_ms'] = metrics['inference']
        elif 'latency' in metrics:
            mapped_metrics['inference_ms'] = metrics['latency']
        elif 'inference_time' in metrics:
            mapped_metrics['inference_ms'] = metrics['inference_time']
        
        if 'accuracy' in metrics:
            mapped_metrics['accuracy'] = metrics['accuracy']
        
        return mapped_metrics
    except Exception as e:
        print(f"Warning: Could not run test script: {e}")
        return {}


def analyze_model(model_path: str, test_dataset: str, test_script: str):
    """Analyze model and generate summary.

    Returns a minimal dict usable by research phase (scraper):
    {
        'architecture_type': 'CNN'|'Transformer'|'RNN'|'Unknown',
        'model_family': 'ResNet'|''|...,
        'layer_types': Dict[str, int],
        'params': int
    }
    """
    print("\nPHASE 1: MODEL ANALYSIS")
    print("━" * 62)
    
    try:
        model, framework = load_model(model_path)
        print(f"├─ Framework: {framework.upper()}")
    except Exception as e:
        print(f"Error loading model: {e}")
        return {}
    
    # Analyze based on framework
    if framework == 'pytorch':
        analysis = analyze_pytorch_model(model)
    elif framework in ['keras', 'tensorflow']:
        analysis = analyze_keras_model(model)
    elif framework == 'jax':
        analysis = analyze_jax_model(model)
    else:
        analysis = {}
    
    model_size_mb = os.path.getsize(model_path) / (1024 * 1024)
    
    model_name = Path(model_path).stem
    
    hardware = get_hardware_info()
    
    metrics = run_test_script(test_script, model_path, test_dataset)
    has_metrics = bool(metrics)
    
    print(f"├─ Model: {model_name} ({analysis.get('params', 0)/1e6:.1f}M params, {model_size_mb:.1f}MB)")
    print(f"├─ Architecture: {analysis.get('arch_type', 'Unknown')}")
    
    layer_types = analysis.get('layer_types', {})
    if layer_types:
        layer_str = ', '.join([f"{name} ({count})" for name, count in list(layer_types.items())[:10]])
        print(f"├─ Layer Types: {layer_str}")
    
    bottleneck_count = analysis.get('bottleneck_count', 0)
    if bottleneck_count > 0:
        print(f"├─ Bottleneck Layers: {bottleneck_count} (potential pruning targets)")
    
    print(f"├─ Hardware: {hardware}")
    
    if has_metrics:
        inference_ms = metrics.get('inference_ms')
        accuracy = metrics.get('accuracy')
        
        if inference_ms is not None and accuracy is not None:
            print(f"└─ Baseline Performance: {inference_ms}ms inference, {accuracy:.1f}% accuracy")
        elif inference_ms is not None:
            print(f"└─ Baseline Performance: {inference_ms}ms inference")
        elif accuracy is not None:
            print(f"└─ Baseline Performance: {accuracy:.1f}% accuracy")
        else:
            print("└─ Baseline Performance: No metrics collected")
    else:
        print("└─ Baseline Performance: No metrics collected")
    print()

    # Prepare scraper-ready information
    arch_long = (analysis.get('arch_type') or '').lower()
    if 'transformer' in arch_long:
        arch_short = 'Transformer'
    elif 'rnn' in arch_long:
        arch_short = 'RNN'
    elif 'cnn' in arch_long:
        arch_short = 'CNN'
    else:
        arch_short = 'Unknown'

    # Heuristic model family detection
    model_family = ''
    if 'resnet' in arch_long or 'resnet' in model_name.lower():
        model_family = 'ResNet'

    return {
        'architecture_type': arch_short,
        'model_family': model_family,
        'layer_types': analysis.get('layer_types', {}),
        'params': int(analysis.get('params', 0)),
    }


def analyze_pytorch_model(model) -> Dict[str, Any]:
    """Analyze PyTorch model."""
    import torch
    
    # Get total parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    
    # Detect layer types
    layer_types = []
    bottleneck_count = 0
    
    def count_layers(module):
        nonlocal bottleneck_count
        layer_types.append(module.__class__.__name__)
        if 'bottleneck' in module.__class__.__name__.lower():
            bottleneck_count += 1
    
    model.apply(count_layers)
    layer_counter = Counter(layer_types)
    
    # Detect architecture type
    arch_type = detect_architecture_pytorch(model)
    
    return {
        'params': total_params,
        'trainable_params': trainable_params,
        'layer_types': dict(layer_counter),
        'bottleneck_count': bottleneck_count,
        'arch_type': arch_type
    }


def analyze_keras_model(model) -> Dict[str, Any]:
    """Analyze Keras/TensorFlow model."""
    layer_types = []
    bottleneck_count = 0
    
    for layer in model.layers:
        layer_types.append(layer.__class__.__name__)
        if 'bottleneck' in layer.__class__.__name__.lower():
            bottleneck_count += 1
    
    layer_counter = Counter(layer_types)
    
    # Get total parameters
    total_params = model.count_params()
    
    # Detect architecture type
    arch_type = detect_architecture_keras(model)
    
    return {
        'params': total_params,
        'layer_types': dict(layer_counter),
        'bottleneck_count': bottleneck_count,
        'arch_type': arch_type
    }


def analyze_jax_model(params) -> Dict[str, Any]:
    """Analyze JAX model."""
    try:
        import jax
        # JAX models are just parameter dictionaries
        def count_params(p):
            return p.size if hasattr(p, 'size') else 0
        
        total_params = sum(count_params(p) for p in jax.tree_leaves(params))
    except Exception:
        total_params = 0
    
    return {
        'params': total_params,
        'layer_types': {},
        'bottleneck_count': 0,
        'arch_type': 'Unknown (JAX)'
    }


def detect_architecture_pytorch(model):
    """Detect model architecture type for PyTorch."""
    class_name = model.__class__.__name__
    
    if 'ResNet' in class_name or any('ResNet' in m.__class__.__name__ for m in model.modules()):
        return 'CNN (ResNet)'
    elif 'Transformer' in class_name or any('Transformer' in m.__class__.__name__ for m in model.modules()):
        return 'Transformer'
    elif 'Bert' in class_name:
        return 'Transformer (BERT)'
    elif 'LSTM' in class_name or 'RNN' in class_name:
        return 'RNN (Recurrent Neural Network)'
    elif any('Conv' in m.__class__.__name__ for m in model.modules()):
        return 'CNN (Convolutional Neural Network)'
    else:
        return 'Unknown Architecture'


def detect_architecture_keras(model):
    """Detect model architecture type for Keras/TensorFlow."""
    layer_names = [l.__class__.__name__ for l in model.layers]
    
    if any('ResNet' in n for n in layer_names):
        return 'CNN (ResNet)'
    elif any('Transformer' in n or 'BERT' in n for n in layer_names):
        return 'Transformer'
    elif any('LSTM' in n or 'RNN' in n for n in layer_names):
        return 'RNN (Recurrent Neural Network)'
    elif any('Conv' in n for n in layer_names):
        return 'CNN (Convolutional Neural Network)'
    else:
        return 'Unknown Architecture'
