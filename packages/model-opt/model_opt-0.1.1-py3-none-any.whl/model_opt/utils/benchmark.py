"""Benchmark utilities."""
import torch
import time


def measure_inference_time(model, sample_input, device='cpu', iterations=100):
    """Measure model inference time."""
    model.eval()
    model.to(device)
    sample_input = sample_input.to(device)
    
    # Warmup
    with torch.no_grad():
        for _ in range(10):
            _ = model(sample_input)
    
    # Benchmark
    torch.cuda.synchronize() if device != 'cpu' else None
    start = time.time()
    
    with torch.no_grad():
        for _ in range(iterations):
            _ = model(sample_input)
    
    torch.cuda.synchronize() if device != 'cpu' else None
    elapsed = (time.time() - start) * 1000 / iterations
    
    return elapsed

