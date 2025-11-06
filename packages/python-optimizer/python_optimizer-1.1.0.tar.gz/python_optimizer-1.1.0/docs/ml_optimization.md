# ML Model Optimization

Python Optimizer provides comprehensive optimization capabilities for machine learning models, with primary support for PyTorch. This guide covers PyTorch model optimization, training acceleration, and inference optimization.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [PyTorch Optimization](#pytorch-optimization)
  - [Model Optimization](#model-optimization)
  - [Training Optimization](#training-optimization)
  - [Inference Optimization](#inference-optimization)
- [API Reference](#api-reference)
- [Performance Guide](#performance-guide)
- [Best Practices](#best-practices)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

## Overview

The ML optimization module provides:

- **Automatic model compilation** - Uses `torch.compile` (PyTorch 2.0+) for optimized execution
- **Mixed precision training** - Automatic mixed precision (AMP) for faster training with lower memory
- **Training loop acceleration** - Optimizes common training patterns with gradient accumulation and clipping
- **Inference optimization** - Dynamic batching and optimized inference paths
- **GPU acceleration** - Seamless integration with GPU acceleration features
- **Device management** - Automatic device selection (CPU/CUDA/MPS)
- **Performance tracking** - Built-in statistics for monitoring optimization effectiveness

### Supported Frameworks

- **PyTorch** ✅ Full support (primary focus)
- **TensorFlow** 🚧 Planned for future release

## Installation

PyTorch optimization requires PyTorch to be installed:

```bash
# Install python-optimizer with PyTorch
pip install python-optimizer torch

# For GPU support (CUDA 12.x)
pip install python-optimizer torch torchvision --index-url https://download.pytorch.org/whl/cu121

# For MPS (Apple Silicon)
pip install python-optimizer torch torchvision
```

## Quick Start

### Basic Model Optimization

```python
from python_optimizer.ml import optimize_model
import torch.nn as nn

class MyModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.linear1 = nn.Linear(784, 256)
        self.relu = nn.ReLU()
        self.linear2 = nn.Linear(256, 10)
    
    def forward(self, x):
        x = self.linear1(x)
        x = self.relu(x)
        x = self.linear2(x)
        return x

# Create and optimize model
model = MyModel()
optimized_model = optimize_model(model, device='cuda', compile=True)

# Use optimized model
output = optimized_model.forward(input_data)
```

### Training Optimization

```python
from python_optimizer.ml import TrainingOptimizer
import torch.optim as optim
import torch.nn as nn

# Setup
model = MyModel()
optimizer = optim.Adam(model.parameters(), lr=0.001)
criterion = nn.CrossEntropyLoss()

# Create training optimizer
training_opt = TrainingOptimizer(
    model, 
    optimizer,
    mixed_precision=True,  # Enable AMP
    gradient_accumulation_steps=4,  # Accumulate gradients
    max_grad_norm=1.0  # Gradient clipping
)

# Training loop
for epoch in range(num_epochs):
    for step, (inputs, targets) in enumerate(train_loader):
        result = training_opt.training_step(inputs, targets, criterion, step)
        
        if step % 100 == 0:
            print(f"Step {step}, Loss: {result['loss']:.4f}, "
                  f"Time: {result['step_time']:.4f}s")

# View statistics
stats = training_opt.get_stats()
print(f"Total steps: {stats['steps']}")
print(f"Avg step time: {stats['avg_step_time']:.4f}s")
```

### Inference Optimization

```python
from python_optimizer.ml import optimize_inference

# Optimize model for inference
inf_opt = optimize_inference(model, device='cuda', batch_size=32)

# Single prediction
output = inf_opt.predict(input_tensor)

# Batch prediction with dynamic batching
inputs = [image1, image2, image3, ...]  # List of inputs
outputs = inf_opt.batch_predict(inputs)  # Automatically batched

# View statistics
stats = inf_opt.get_stats()
print(f"Predictions: {stats['predictions']}")
print(f"Avg time: {stats['avg_prediction_time']:.4f}s")
```

## PyTorch Optimization

### Model Optimization

The `PyTorchModelOptimizer` class provides comprehensive model optimization:

```python
from python_optimizer.ml import PyTorchModelOptimizer

optimizer = PyTorchModelOptimizer(
    model,
    device='cuda',           # Device: 'cpu', 'cuda', 'mps', or torch.device
    compile=True,            # Use torch.compile (PyTorch 2.0+)
    mixed_precision=False,   # Enable mixed precision for forward pass
    memory_efficient=True    # Enable memory optimizations
)
```

#### Features

**Automatic Device Selection**
```python
# Automatic device selection (CUDA > MPS > CPU)
optimizer = PyTorchModelOptimizer(model)  # Auto-selects best device

# Explicit device
optimizer = PyTorchModelOptimizer(model, device='cuda:1')  # Specific GPU
optimizer = PyTorchModelOptimizer(model, device='mps')     # Apple Silicon
```

**Model Compilation**
```python
# With torch.compile (PyTorch 2.0+)
optimizer = PyTorchModelOptimizer(model, compile=True)

# Fallback to uncompiled if torch.compile unavailable
optimizer = PyTorchModelOptimizer(model, compile=True)  # Safe fallback
```

**Optimized Forward Pass**
```python
# Use optimized forward pass
output = optimizer.forward(input_data)

# Get performance statistics
stats = optimizer.get_stats()
print(f"Forward passes: {stats['forward_passes']}")
print(f"Avg time: {stats['avg_forward_time']:.6f}s")
print(f"Device: {stats['device']}")
```

### Training Optimization

The `TrainingOptimizer` class optimizes training loops:

```python
from python_optimizer.ml import TrainingOptimizer
import torch.optim as optim

training_opt = TrainingOptimizer(
    model,
    optimizer,
    device='cuda',
    mixed_precision=True,           # Enable AMP
    gradient_accumulation_steps=4,  # Accumulate over 4 steps
    max_grad_norm=1.0              # Gradient clipping threshold
)
```

#### Features

**Automatic Mixed Precision (AMP)**
```python
# Enable AMP for faster training
training_opt = TrainingOptimizer(
    model, 
    optimizer,
    mixed_precision=True  # Automatic FP16/FP32 mixed precision
)

# AMP automatically enabled on CUDA
# Falls back to FP32 on CPU
```

**Gradient Accumulation**
```python
# Accumulate gradients over multiple steps
training_opt = TrainingOptimizer(
    model,
    optimizer,
    gradient_accumulation_steps=8  # Effective batch size = batch_size * 8
)

# Training loop
for step, (inputs, targets) in enumerate(train_loader):
    result = training_opt.training_step(inputs, targets, criterion, step)
    # Optimizer updated every 8 steps
```

**Gradient Clipping**
```python
# Clip gradients by norm
training_opt = TrainingOptimizer(
    model,
    optimizer,
    max_grad_norm=1.0  # Clip to max norm of 1.0
)

# Disable gradient clipping
training_opt = TrainingOptimizer(
    model,
    optimizer,
    max_grad_norm=None  # No clipping
)
```

**Training Step Method**
```python
result = training_opt.training_step(inputs, targets, criterion, step)

# Returns dict with:
# - loss: float - Current loss value
# - step_time: float - Step execution time
# - gpu_memory_used: float - GPU memory used (MB)
print(f"Loss: {result['loss']:.4f}")
print(f"Time: {result['step_time']:.4f}s")
print(f"Memory: {result['gpu_memory_used']:.1f} MB")
```

**Training Statistics**
```python
stats = training_opt.get_stats()

print(f"Steps completed: {stats['steps']}")
print(f"Total time: {stats['total_time']:.2f}s")
print(f"Avg step time: {stats['avg_step_time']:.4f}s")
print(f"Device: {stats['device']}")
print(f"Mixed precision: {stats['mixed_precision']}")
```

### Inference Optimization

The `InferenceOptimizer` class optimizes model inference:

```python
from python_optimizer.ml import InferenceOptimizer

inf_opt = InferenceOptimizer(
    model,
    device='cuda',
    compile=True,      # Compile for inference (mode='reduce-overhead')
    batch_size=32      # Dynamic batching size
)
```

#### Features

**Single Prediction**
```python
# Predict single input
output = inf_opt.predict(input_tensor)

# Automatically uses torch.no_grad()
# Optimized inference path
```

**Batch Prediction with Dynamic Batching**
```python
# List of individual inputs
inputs = [img1, img2, img3, ...]  # Can be any number

# Automatically batched for efficiency
outputs = inf_opt.batch_predict(inputs)

# Batch size controlled by InferenceOptimizer
inf_opt = InferenceOptimizer(model, batch_size=64)  # Process 64 at a time
```

**Inference Statistics**
```python
stats = inf_opt.get_stats()

print(f"Predictions: {stats['predictions']}")
print(f"Total time: {stats['total_time']:.2f}s")
print(f"Avg prediction time: {stats['avg_prediction_time']:.6f}s")
print(f"Throughput: {stats['predictions'] / stats['total_time']:.1f} pred/s")
```

## API Reference

### High-Level Functions

#### `optimize_model(model, device=None, compile=True, mixed_precision=False)`

Convenience function to create optimized PyTorch model.

**Parameters:**
- `model` (nn.Module): PyTorch model to optimize
- `device` (str/torch.device, optional): Device to use ('cpu', 'cuda', 'mps')
- `compile` (bool): Use torch.compile if available
- `mixed_precision` (bool): Enable mixed precision

**Returns:** `PyTorchModelOptimizer` instance

**Example:**
```python
optimized = optimize_model(model, device='cuda', compile=True)
```

#### `optimize_training(mixed_precision=True, gradient_accumulation_steps=1, max_grad_norm=1.0)`

Decorator to optimize training functions.

**Parameters:**
- `mixed_precision` (bool): Enable AMP
- `gradient_accumulation_steps` (int): Gradient accumulation
- `max_grad_norm` (float): Gradient clipping threshold

**Returns:** Decorator function

**Example:**
```python
@optimize_training(mixed_precision=True, gradient_accumulation_steps=4)
def train_step(model, inputs, targets, criterion, optimizer):
    outputs = model(inputs)
    loss = criterion(outputs, targets)
    loss.backward()
    optimizer.step()
    optimizer.zero_grad()
    return loss.item()
```

#### `optimize_inference(model, device=None, compile=True, batch_size=None)`

Convenience function to create optimized inference engine.

**Parameters:**
- `model` (nn.Module): PyTorch model
- `device` (str/torch.device, optional): Device
- `compile` (bool): Use torch.compile
- `batch_size` (int, optional): Batch size for dynamic batching

**Returns:** `InferenceOptimizer` instance

**Example:**
```python
inf_opt = optimize_inference(model, device='cuda', batch_size=32)
```

### Classes

#### `PyTorchModelOptimizer`

Main model optimization class.

**Methods:**
- `__init__(model, device=None, compile=True, mixed_precision=False, memory_efficient=True)`
- `forward(*args, **kwargs)` - Optimized forward pass
- `get_stats()` - Get performance statistics

#### `TrainingOptimizer`

Training loop optimization class.

**Methods:**
- `__init__(model, optimizer, device=None, mixed_precision=True, gradient_accumulation_steps=1, max_grad_norm=1.0)`
- `training_step(inputs, targets, criterion, step)` - Execute optimized training step
- `get_stats()` - Get training statistics

#### `InferenceOptimizer`

Inference optimization class.

**Methods:**
- `__init__(model, device=None, compile=True, batch_size=None)`
- `predict(inputs)` - Single prediction
- `batch_predict(inputs_list)` - Batch prediction with dynamic batching
- `get_stats()` - Get inference statistics

## Performance Guide

### Expected Speedups

Typical performance improvements with PyTorch optimization:

- **Model compilation** (torch.compile): 1.2-2.5x speedup
- **Mixed precision training**: 1.5-3x speedup on modern GPUs
- **Inference optimization**: 1.3-2x speedup
- **Dynamic batching**: 2-10x throughput improvement

### Optimization Strategies

#### For Training

```python
# Maximum training speed
training_opt = TrainingOptimizer(
    model,
    optimizer,
    device='cuda',
    mixed_precision=True,  # Enable AMP
    gradient_accumulation_steps=8,  # Larger effective batch
    max_grad_norm=1.0  # Stabilize training
)
```

#### For Inference

```python
# Maximum inference throughput
model.eval()  # Set to eval mode
inf_opt = InferenceOptimizer(
    model,
    device='cuda',
    compile=True,  # Compile for inference
    batch_size=64  # Larger batches
)
```

#### Memory Optimization

```python
# Lower memory usage during training
training_opt = TrainingOptimizer(
    model,
    optimizer,
    mixed_precision=True,  # FP16 uses less memory
    gradient_accumulation_steps=4  # Smaller per-step batch
)
```

### Device Selection

**CUDA (NVIDIA GPUs)**
- Best overall performance
- Full AMP support
- Recommended for production

**MPS (Apple Silicon)**
- Good performance on M1/M2/M3
- Limited AMP support (CPU fallback)
- Excellent for development

**CPU**
- Fallback option
- No AMP support
- Good for testing/debugging

## Best Practices

### Model Optimization

✅ **Do:**
- Use `compile=True` on PyTorch 2.0+ for best performance
- Set model to `model.eval()` for inference
- Use mixed precision on compatible GPUs
- Profile your model with `get_stats()` to track improvements

❌ **Don't:**
- Mix training and inference optimizers on same model instance
- Use mixed precision on CPU (no benefit, potential issues)
- Forget to move data to same device as model

### Training Optimization

✅ **Do:**
- Enable mixed precision on CUDA GPUs
- Use gradient accumulation for larger effective batch sizes
- Enable gradient clipping for stability
- Monitor training statistics regularly

❌ **Don't:**
- Use very large gradient accumulation (>16) without careful tuning
- Disable gradient clipping with large learning rates
- Forget to scale loss when using gradient accumulation

### Inference Optimization

✅ **Do:**
- Use batch prediction when possible
- Set appropriate batch_size for your GPU
- Compile models with `compile=True`
- Use `model.eval()` mode

❌ **Don't:**
- Use training optimizers for inference
- Process inputs one-by-one when batching is possible
- Use mixed precision for inference (minimal benefit, added complexity)

## Examples

### Complete Training Example

```python
from python_optimizer.ml import PyTorchModelOptimizer, TrainingOptimizer
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader

# Define model
class CNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(3, 64, 3, padding=1)
        self.conv2 = nn.Conv2d(64, 128, 3, padding=1)
        self.pool = nn.MaxPool2d(2, 2)
        self.fc1 = nn.Linear(128 * 8 * 8, 512)
        self.fc2 = nn.Linear(512, 10)
        self.relu = nn.ReLU()
    
    def forward(self, x):
        x = self.pool(self.relu(self.conv1(x)))
        x = self.pool(self.relu(self.conv2(x)))
        x = x.view(x.size(0), -1)
        x = self.relu(self.fc1(x))
        x = self.fc2(x)
        return x

# Create model
model = CNN()

# Optimize model
model_opt = PyTorchModelOptimizer(
    model,
    device='cuda',
    compile=True,
    mixed_precision=False
)

# Setup training
optimizer = optim.Adam(model_opt.model.parameters(), lr=0.001)
criterion = nn.CrossEntropyLoss()

training_opt = TrainingOptimizer(
    model_opt.model,
    optimizer,
    device='cuda',
    mixed_precision=True,
    gradient_accumulation_steps=4,
    max_grad_norm=1.0
)

# Training loop
train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)

for epoch in range(10):
    total_loss = 0
    for step, (inputs, targets) in enumerate(train_loader):
        inputs, targets = inputs.cuda(), targets.cuda()
        
        result = training_opt.training_step(
            inputs, targets, criterion, step
        )
        
        total_loss += result['loss']
        
        if step % 100 == 0:
            print(f"Epoch {epoch}, Step {step}, "
                  f"Loss: {result['loss']:.4f}, "
                  f"Time: {result['step_time']:.4f}s")
    
    avg_loss = total_loss / len(train_loader)
    print(f"Epoch {epoch} complete, Avg Loss: {avg_loss:.4f}")

# Print final statistics
stats = training_opt.get_stats()
print(f"\nTraining Statistics:")
print(f"Total steps: {stats['steps']}")
print(f"Total time: {stats['total_time']:.2f}s")
print(f"Avg step time: {stats['avg_step_time']:.4f}s")
```

### Complete Inference Example

```python
from python_optimizer.ml import optimize_inference
import torch
from PIL import Image
import torchvision.transforms as transforms

# Load trained model
model = torch.load('trained_model.pth')
model.eval()

# Optimize for inference
inf_opt = optimize_inference(
    model,
    device='cuda',
    compile=True,
    batch_size=32
)

# Prepare image preprocessing
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                        std=[0.229, 0.224, 0.225])
])

# Load images
image_paths = ['img1.jpg', 'img2.jpg', 'img3.jpg', ...]
images = [transform(Image.open(p)).cuda() for p in image_paths]

# Batch inference
outputs = inf_opt.batch_predict(images)

# Process results
predictions = [torch.argmax(out).item() for out in outputs]

# Print statistics
stats = inf_opt.get_stats()
print(f"Processed {stats['predictions']} images")
print(f"Total time: {stats['total_time']:.2f}s")
print(f"Throughput: {stats['predictions']/stats['total_time']:.1f} img/s")
```

## Troubleshooting

### PyTorch Not Available

**Error:** `RuntimeError: PyTorch is not installed`

**Solution:**
```bash
pip install torch torchvision
```

### torch.compile Not Available

**Symptom:** Warning about torch.compile fallback

**Solution:** Upgrade to PyTorch 2.0+:
```bash
pip install --upgrade torch>=2.0.0
```

### Mixed Precision Errors

**Error:** Issues with mixed precision training

**Solutions:**
1. Ensure using CUDA GPU: `device='cuda'`
2. Check GPU supports FP16: Compute Capability >= 7.0
3. Disable if on CPU: `mixed_precision=False`

### Memory Issues

**Error:** CUDA out of memory

**Solutions:**
```python
# Reduce batch size
inf_opt = InferenceOptimizer(model, batch_size=16)  # Smaller

# Use gradient accumulation
training_opt = TrainingOptimizer(
    model, optimizer,
    gradient_accumulation_steps=8  # Smaller per-step batch
)

# Enable memory efficient mode
model_opt = PyTorchModelOptimizer(
    model, memory_efficient=True
)
```

### Performance Not Improving

**Check:**
1. Model is actually using GPU: `stats['device']`
2. Compilation succeeded: Check for warnings
3. Using appropriate batch sizes
4. Model is large enough to benefit from optimization

**Debug:**
```python
# Check statistics
stats = optimizer.get_stats()
print(f"Device: {stats['device']}")
print(f"Avg time: {stats['avg_forward_time']:.6f}s")

# Compare with baseline
import time
start = time.perf_counter()
for _ in range(100):
    model(input_data)
baseline_time = (time.perf_counter() - start) / 100
print(f"Baseline: {baseline_time:.6f}s")
```

## Framework Compatibility

Check which ML frameworks are available:

```python
from python_optimizer.ml import check_framework_availability

frameworks = check_framework_availability()
print(f"PyTorch: {frameworks['pytorch']['available']}")
print(f"Version: {frameworks['pytorch']['version']}")
```

---

For more examples, see:
- `examples/pytorch_optimization.py` - Comprehensive PyTorch examples
- `examples/ml_optimization.py` - General ML optimization patterns
- `tests/test_ml.py` - Complete test suite with usage examples
