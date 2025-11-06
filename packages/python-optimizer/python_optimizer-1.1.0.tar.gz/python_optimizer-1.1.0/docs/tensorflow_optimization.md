# TensorFlow/Keras Model Optimization

Python Optimizer provides comprehensive optimization capabilities for TensorFlow and Keras models, including XLA compilation, mixed precision training, and inference optimization.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [TensorFlow Optimization](#tensorflow-optimization)
  - [Model Optimization](#model-optimization)
  - [Training Optimization](#training-optimization)
  - [Inference Optimization](#inference-optimization)
- [API Reference](#api-reference)
- [Performance Guide](#performance-guide)
- [Best Practices](#best-practices)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

## Overview

The TensorFlow optimization module provides:

- **XLA Compilation** - Accelerated Linear Algebra for faster execution
- **tf.function Optimization** - Graph-mode execution with JIT compilation
- **Mixed Precision Training** - Automatic FP16/FP32 for faster training with lower memory
- **Training Loop Acceleration** - Gradient accumulation and optimized training steps
- **Inference Optimization** - Dynamic batching and graph optimization
- **GPU Acceleration** - Seamless GPU utilization with memory tracking
- **Device Management** - Automatic device selection (CPU/GPU)
- **Performance Tracking** - Built-in statistics for monitoring optimization

### Supported Versions

- **TensorFlow** 2.x (tested with 2.10+)
- **Keras** (included with TensorFlow 2.x)

## Installation

TensorFlow optimization requires TensorFlow to be installed:

```bash
# Install python-optimizer with TensorFlow
pip install python-optimizer tensorflow

# For GPU support
pip install python-optimizer tensorflow[and-cuda]

# For Apple Silicon (Metal)
pip install python-optimizer tensorflow-macos tensorflow-metal
```

## Quick Start

### Basic Model Optimization

```python
from python_optimizer.ml import optimize_tf_model
import tensorflow as tf

# Create Keras model
model = tf.keras.Sequential([
    tf.keras.layers.Dense(256, activation='relu', input_shape=(784,)),
    tf.keras.layers.Dense(128, activation='relu'),
    tf.keras.layers.Dense(10, activation='softmax')
])

# Optimize model with XLA
optimized_model = optimize_tf_model(model, device='GPU:0', use_xla=True)

# Use optimized model
output = optimized_model(input_data)
```

### Training Optimization

```python
from python_optimizer.ml import TFTrainingOptimizer
import tensorflow as tf

# Setup
model = create_model()
optimizer = tf.keras.optimizers.Adam(learning_rate=0.001)
loss_fn = tf.keras.losses.SparseCategoricalCrossentropy()

# Create training optimizer
training_opt = TFTrainingOptimizer(
    model,
    optimizer,
    mixed_precision=True,  # Enable AMP
    gradient_accumulation_steps=4,  # Accumulate gradients
    use_xla=True  # Enable XLA
)

# Training loop
for epoch in range(num_epochs):
    for step, (inputs, targets) in enumerate(train_dataset):
        result = training_opt.training_step(inputs, targets, loss_fn, step)
        
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
from python_optimizer.ml import optimize_tf_inference

# Optimize model for inference
inf_opt = optimize_tf_inference(model, device='GPU:0', batch_size=32)

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

## TensorFlow Optimization

### Model Optimization

The `TFModelOptimizer` class provides comprehensive model optimization:

```python
from python_optimizer.ml import TFModelOptimizer

optimizer = TFModelOptimizer(
    model,
    device='GPU:0',          # Device: 'CPU:0', 'GPU:0', etc.
    use_xla=True,            # Enable XLA compilation
    mixed_precision=False,   # Enable mixed precision
    jit_compile=True         # Use tf.function with jit_compile
)
```

#### Features

**Automatic Device Selection**
```python
# Automatic device selection (GPU > CPU)
optimizer = TFModelOptimizer(model)  # Auto-selects best device

# Explicit device
optimizer = TFModelOptimizer(model, device='GPU:0')  # Specific GPU
optimizer = TFModelOptimizer(model, device='CPU:0')  # CPU only
```

**XLA Compilation**
```python
# With XLA (Accelerated Linear Algebra)
optimizer = TFModelOptimizer(model, use_xla=True)

# XLA provides 1.2-2x speedup for most models
```

**tf.function Graph Optimization**
```python
# Use tf.function with JIT compilation
optimizer = TFModelOptimizer(model, jit_compile=True)

# Forward pass is automatically graph-optimized
output = optimizer(input_data)
```

**Mixed Precision**
```python
# Enable mixed precision (FP16/FP32)
optimizer = TFModelOptimizer(model, mixed_precision=True)

# Sets global policy to 'mixed_float16'
# Automatic loss scaling included
```

**Optimized Forward Pass**
```python
# Use optimized forward pass
output = optimizer(input_data)

# Training mode
output = optimizer(input_data, training=True)

# Get performance statistics
stats = optimizer.get_stats()
print(f"Forward passes: {stats['forward_passes']}")
print(f"Avg time: {stats['avg_forward_time']:.6f}s")
print(f"Device: {stats['device']}")
```

### Training Optimization

The `TFTrainingOptimizer` class optimizes training loops:

```python
from python_optimizer.ml import TFTrainingOptimizer

training_opt = TFTrainingOptimizer(
    model,
    optimizer,
    device='GPU:0',
    mixed_precision=True,           # Enable AMP with LossScaleOptimizer
    gradient_accumulation_steps=4,  # Accumulate over 4 steps
    use_xla=True                    # Enable XLA
)
```

#### Features

**Automatic Mixed Precision (AMP)**
```python
# Enable AMP with LossScaleOptimizer
training_opt = TFTrainingOptimizer(
    model,
    optimizer,
    mixed_precision=True  # Wraps optimizer with LossScaleOptimizer
)

# Automatic loss scaling and gradient unscaling
# Significant speedup on modern GPUs (V100, A100, RTX 30xx+)
```

**Gradient Accumulation**
```python
# Accumulate gradients over multiple steps
training_opt = TFTrainingOptimizer(
    model,
    optimizer,
    gradient_accumulation_steps=8  # Effective batch size = batch_size * 8
)

# Training loop
for step, (inputs, targets) in enumerate(train_dataset):
    result = training_opt.training_step(inputs, targets, loss_fn, step)
    # Gradients accumulated, optimizer updated every 8 steps
```

**XLA Compilation**
```python
# Enable XLA for training step
training_opt = TFTrainingOptimizer(
    model,
    optimizer,
    use_xla=True  # Compiles training step with XLA
)

# Training step is JIT-compiled for faster execution
```

**Training Step Method**
```python
result = training_opt.training_step(inputs, targets, loss_fn, step)

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

The `TFInferenceOptimizer` class optimizes model inference:

```python
from python_optimizer.ml import TFInferenceOptimizer

inf_opt = TFInferenceOptimizer(
    model,
    device='GPU:0',
    use_xla=True,      # Enable XLA for inference
    batch_size=32      # Dynamic batching size
)
```

#### Features

**Single Prediction**
```python
# Predict single input
output = inf_opt.predict(input_tensor)

# Automatically uses tf.function with XLA
# Optimized inference path
```

**Batch Prediction with Dynamic Batching**
```python
# List of individual inputs
inputs = [img1, img2, img3, ...]  # Can be any number

# Automatically batched for efficiency
outputs = inf_opt.batch_predict(inputs)

# Batch size controlled by TFInferenceOptimizer
inf_opt = TFInferenceOptimizer(model, batch_size=64)  # Process 64 at a time
```

**XLA Optimization**
```python
# Enable XLA for inference
inf_opt = TFInferenceOptimizer(model, use_xla=True)

# XLA provides significant speedup for inference
# Especially beneficial for smaller batch sizes
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

#### `optimize_tf_model(model, device=None, use_xla=True, mixed_precision=False, jit_compile=True)`

Convenience function to create optimized TensorFlow/Keras model.

**Parameters:**
- `model` (keras.Model): Keras model to optimize
- `device` (str, optional): Device to use ('CPU:0', 'GPU:0', etc.)
- `use_xla` (bool): Enable XLA compilation
- `mixed_precision` (bool): Enable mixed precision
- `jit_compile` (bool): Use tf.function with jit_compile

**Returns:** `TFModelOptimizer` instance

**Example:**
```python
optimized = optimize_tf_model(model, device='GPU:0', use_xla=True)
```

#### `optimize_tf_training(mixed_precision=True, gradient_accumulation_steps=1, use_xla=True)`

Decorator to optimize TensorFlow training functions.

**Parameters:**
- `mixed_precision` (bool): Enable automatic mixed precision
- `gradient_accumulation_steps` (int): Gradient accumulation steps
- `use_xla` (bool): Enable XLA compilation

**Returns:** Decorator function

**Example:**
```python
@optimize_tf_training(mixed_precision=True, use_xla=True)
def train_step(model, inputs, targets, loss_fn, optimizer):
    # Training code
    pass
```

#### `optimize_tf_inference(model, device=None, use_xla=True, batch_size=None)`

Convenience function to create optimized inference engine.

**Parameters:**
- `model` (keras.Model): Keras model
- `device` (str, optional): Device to use
- `use_xla` (bool): Enable XLA compilation
- `batch_size` (int, optional): Batch size for dynamic batching

**Returns:** `TFInferenceOptimizer` instance

**Example:**
```python
inf_opt = optimize_tf_inference(model, device='GPU:0', batch_size=32)
```

### Classes

#### `TFModelOptimizer`

Main model optimization class.

**Methods:**
- `__init__(model, device=None, use_xla=True, mixed_precision=False, jit_compile=True)`
- `__call__(inputs, training=False)` - Optimized forward pass
- `get_stats()` - Get performance statistics

#### `TFTrainingOptimizer`

Training loop optimization class.

**Methods:**
- `__init__(model, optimizer, device=None, mixed_precision=True, gradient_accumulation_steps=1, use_xla=True)`
- `training_step(inputs, targets, loss_fn, step)` - Execute optimized training step
- `get_stats()` - Get training statistics

#### `TFInferenceOptimizer`

Inference optimization class.

**Methods:**
- `__init__(model, device=None, use_xla=True, batch_size=None)`
- `predict(inputs)` - Single prediction
- `batch_predict(inputs_list)` - Batch prediction with dynamic batching
- `get_stats()` - Get inference statistics

## Performance Guide

### Expected Speedups

Typical performance improvements with TensorFlow optimization:

- **XLA compilation**: 1.2-2.5x speedup
- **Mixed precision training**: 1.5-3x speedup on modern GPUs
- **tf.function optimization**: 1.3-2x speedup
- **Dynamic batching**: 2-10x throughput improvement

### Optimization Strategies

#### For Training

```python
# Maximum training speed
training_opt = TFTrainingOptimizer(
    model,
    optimizer,
    device='GPU:0',
    mixed_precision=True,  # Enable AMP
    gradient_accumulation_steps=8,  # Larger effective batch
    use_xla=True  # Enable XLA
)
```

#### For Inference

```python
# Maximum inference throughput
inf_opt = TFInferenceOptimizer(
    model,
    device='GPU:0',
    use_xla=True,  # Enable XLA
    batch_size=64  # Larger batches
)
```

#### Memory Optimization

```python
# Lower memory usage during training
training_opt = TFTrainingOptimizer(
    model,
    optimizer,
    mixed_precision=True,  # FP16 uses less memory
    gradient_accumulation_steps=4  # Smaller per-step batch
)
```

### Device Selection

**GPU (NVIDIA/AMD)**
- Best overall performance
- Full mixed precision support
- Recommended for production

**CPU**
- Fallback option
- No mixed precision benefit
- Good for testing/debugging

**Apple Metal (M1/M2/M3)**
- Good performance on Apple Silicon
- Limited mixed precision support
- Use tensorflow-metal

## Best Practices

### Model Optimization

✅ **Do:**
- Use `use_xla=True` for best performance
- Enable `jit_compile=True` for graph optimization
- Use mixed precision on compatible GPUs
- Profile your model with `get_stats()` to track improvements

❌ **Don't:**
- Mix training and inference optimizers on same model instance
- Use mixed precision on CPU (no benefit)
- Forget to move data to same device as model

### Training Optimization

✅ **Do:**
- Enable mixed precision on modern GPUs (V100+, RTX 20xx+)
- Use gradient accumulation for larger effective batch sizes
- Enable XLA for training step compilation
- Monitor training statistics regularly

❌ **Don't:**
- Use very large gradient accumulation (>16) without careful tuning
- Disable XLA without testing (usually provides speedup)
- Mix TensorFlow eager mode with optimized training

### Inference Optimization

✅ **Do:**
- Use batch prediction when possible
- Set appropriate batch_size for your GPU
- Enable XLA for inference
- Use `model.predict()` wrapper for Keras compatibility

❌ **Don't:**
- Use training optimizers for inference
- Process inputs one-by-one when batching is possible
- Forget to set model to inference mode

## Examples

### Complete Training Example

```python
from python_optimizer.ml import TFModelOptimizer, TFTrainingOptimizer
import tensorflow as tf

# Define model
model = tf.keras.Sequential([
    tf.keras.layers.Conv2D(64, 3, activation='relu', input_shape=(32, 32, 3)),
    tf.keras.layers.MaxPooling2D(2),
    tf.keras.layers.Conv2D(128, 3, activation='relu'),
    tf.keras.layers.MaxPooling2D(2),
    tf.keras.layers.Flatten(),
    tf.keras.layers.Dense(512, activation='relu'),
    tf.keras.layers.Dense(10, activation='softmax')
])

# Optimize model
model_opt = TFModelOptimizer(
    model,
    device='GPU:0',
    use_xla=True,
    mixed_precision=False
)

# Setup training
optimizer = tf.keras.optimizers.Adam(learning_rate=0.001)
loss_fn = tf.keras.losses.SparseCategoricalCrossentropy()

training_opt = TFTrainingOptimizer(
    model_opt.model,
    optimizer,
    device='GPU:0',
    mixed_precision=True,
    gradient_accumulation_steps=4,
    use_xla=True
)

# Training loop
train_dataset = tf.data.Dataset.from_tensor_slices((x_train, y_train))
train_dataset = train_dataset.batch(64).prefetch(tf.data.AUTOTUNE)

for epoch in range(10):
    total_loss = 0
    for step, (inputs, targets) in enumerate(train_dataset):
        result = training_opt.training_step(inputs, targets, loss_fn, step)
        
        total_loss += result['loss']
        
        if step % 100 == 0:
            print(f"Epoch {epoch}, Step {step}, "
                  f"Loss: {result['loss']:.4f}, "
                  f"Time: {result['step_time']:.4f}s")
    
    avg_loss = total_loss / len(train_dataset)
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
from python_optimizer.ml import optimize_tf_inference
import tensorflow as tf

# Load trained model
model = tf.keras.models.load_model('trained_model.h5')

# Optimize for inference
inf_opt = optimize_tf_inference(
    model,
    device='GPU:0',
    use_xla=True,
    batch_size=32
)

# Prepare data preprocessing
preprocess = tf.keras.Sequential([
    tf.keras.layers.Resizing(224, 224),
    tf.keras.layers.Rescaling(1./255)
])

# Load and preprocess images
import numpy as np
from PIL import Image

image_paths = ['img1.jpg', 'img2.jpg', 'img3.jpg', ...]
images = []
for path in image_paths:
    img = Image.open(path)
    img_array = np.array(img)
    img_tensor = tf.convert_to_tensor(img_array)
    img_processed = preprocess(img_tensor)
    images.append(img_processed)

# Batch inference
outputs = inf_opt.batch_predict(images)

# Process results
predictions = [tf.argmax(out, axis=-1).numpy() for out in outputs]

# Print statistics
stats = inf_opt.get_stats()
print(f"Processed {stats['predictions']} images")
print(f"Total time: {stats['total_time']:.2f}s")
print(f"Throughput: {len(images)/stats['total_time']:.1f} img/s")
```

## Troubleshooting

### TensorFlow Not Available

**Error:** `RuntimeError: TensorFlow is not installed`

**Solution:**
```bash
pip install tensorflow
```

### XLA Not Working

**Symptom:** No speedup with `use_xla=True`

**Solutions:**
1. Verify XLA is enabled: Check TensorFlow build supports XLA
2. Some operations don't support XLA - check TensorFlow logs
3. Try without XLA: `use_xla=False` to compare

### Mixed Precision Errors

**Error:** Issues with mixed precision training

**Solutions:**
1. Ensure using GPU: `device='GPU:0'`
2. Check GPU supports FP16: Compute Capability >= 7.0 (V100+)
3. Disable if on CPU: `mixed_precision=False`

### Memory Issues

**Error:** Out of memory

**Solutions:**
```python
# Reduce batch size
inf_opt = TFInferenceOptimizer(model, batch_size=16)  # Smaller

# Use gradient accumulation
training_opt = TFTrainingOptimizer(
    model, optimizer,
    gradient_accumulation_steps=8  # Smaller per-step batch
)

# Enable mixed precision (uses less memory)
training_opt = TFTrainingOptimizer(
    model, optimizer,
    mixed_precision=True
)
```

### Performance Not Improving

**Check:**
1. Model is actually using GPU: `stats['device']`
2. XLA compilation succeeded: Check for warnings
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
print(f"TensorFlow: {frameworks['tensorflow']['available']}")
print(f"Version: {frameworks['tensorflow']['version']}")
print(f"PyTorch: {frameworks['pytorch']['available']}")
```

---

For more examples, see:
- `examples/tensorflow_optimization.py` - Comprehensive TensorFlow examples
- `tests/test_tensorflow.py` - Complete test suite with usage examples
- `docs/ml_optimization.md` - PyTorch optimization guide (similar patterns)
