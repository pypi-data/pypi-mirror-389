# GPU Acceleration Guide

Python Optimizer provides GPU acceleration through CUDA/CuPy integration, enabling significant speedups for array operations and numerical computations.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Features](#core-features)
- [API Reference](#api-reference)
- [Performance Guidelines](#performance-guidelines)
- [Troubleshooting](#troubleshooting)

## Overview

GPU acceleration in Python Optimizer provides:

- **Automatic GPU Detection**: Detects available CUDA GPUs and falls back to CPU gracefully
- **Smart Dispatching**: Automatically routes computations to GPU or CPU based on data size
- **Memory Management**: Intelligent GPU memory pooling and caching
- **Zero Code Changes**: Same function works on both GPU and CPU
- **Threshold Tuning**: Configurable size thresholds for GPU usage

### When to Use GPU

GPU acceleration is beneficial for:
- ✅ Large array operations (>10K elements)
- ✅ Matrix multiplications
- ✅ Element-wise operations on large datasets
- ✅ Iterative numerical algorithms
- ✅ Financial computations on large timeseries

GPU may not help for:
- ❌ Small datasets (<10K elements)
- ❌ Operations with complex Python objects
- ❌ I/O-bound operations
- ❌ Code with heavy branching logic

## Installation

### Requirements

- **NVIDIA GPU** with CUDA support (Compute Capability ≥ 3.5)
- **CUDA Toolkit** 11.x or 12.x
- **Python** 3.11+

### Install CuPy

```bash
# For CUDA 12.x
pip install cupy-cuda12x

# For CUDA 11.x
pip install cupy-cuda11x

# Check installation
python -c "import cupy; print(cupy.cuda.runtime.getDeviceCount())"
```

### Verify GPU Support

```python
from python_optimizer import is_gpu_available, get_gpu_info

if is_gpu_available():
    print("✓ GPU available!")
    info = get_gpu_info()
    print(info)
else:
    print("GPU not available - will use CPU")
```

## Quick Start

### Basic Usage

```python
from python_optimizer import optimize
import numpy as np

# Enable GPU acceleration with gpu=True
@optimize(gpu=True, jit=False)
def compute(data):
    return data ** 2 + data * 3

# Works automatically on GPU for large arrays
large_array = np.random.randn(1_000_000)
result = compute(large_array)  # Runs on GPU
```

### Threshold Tuning

Control when GPU is used via `gpu_min_size`:

```python
# Use GPU only for arrays with >100K elements
@optimize(gpu=True, gpu_min_size=100_000)
def compute_selective(data):
    return np.sum(data ** 2)

small = np.random.randn(50_000)   # Uses CPU
large = np.random.randn(200_000)  # Uses GPU

result1 = compute_selective(small)  # CPU
result2 = compute_selective(large)  # GPU
```

### Combining with Other Optimizations

```python
# GPU + JIT + Specialization
@optimize(
    gpu=True,
    jit=True,
    specialize=True,
    gpu_min_size=10_000
)
def combined(data, multiplier):
    return data ** 2 * multiplier
```

## Core Features

### 1. Automatic GPU Detection

Python Optimizer automatically detects GPU availability and falls back to CPU:

```python
from python_optimizer import is_gpu_available, get_gpu_info

# Check availability
if is_gpu_available():
    info = get_gpu_info()
    print(f"GPU: {info['devices'][0]['name']}")
    print(f"Memory: {info['devices'][0]['memory_gb']} GB")
```

### 2. Smart CPU/GPU Dispatching

The dispatcher analyzes input data and automatically selects the best device:

```python
from python_optimizer.gpu import GPUDispatcher

# Create custom dispatcher
dispatcher = GPUDispatcher(
    min_size_threshold=10_000,  # Min size for GPU
    force_gpu=False,            # Don't force GPU
    force_cpu=False             # Don't force CPU
)

@dispatcher.wrap()
def my_function(x):
    return x ** 2 + x

# Automatically dispatched
small_data = np.random.randn(1000)    # → CPU
large_data = np.random.randn(100_000) # → GPU
```

### 3. GPU Memory Management

Control GPU memory allocation and caching:

```python
from python_optimizer import (
    get_gpu_memory_info,
    clear_gpu_cache,
    set_gpu_memory_limit
)

# Check memory usage
mem_info = get_gpu_memory_info()
print(f"GPU Memory: {mem_info.used_gb:.2f}/{mem_info.total_gb:.2f} GB")
print(f"Utilization: {mem_info.utilization_percent:.1f}%")

# Clear cache to free memory
clear_gpu_cache()

# Set memory limit (4 GB)
from python_optimizer.gpu import set_gpu_memory_limit
set_gpu_memory_limit(4.0)
```

### 4. GPU Kernel Library

Pre-optimized GPU operations:

```python
from python_optimizer.gpu import GPUKernelLibrary
import numpy as np

# Use GPU-accelerated operations
arr = np.random.randn(1_000_000)

result = GPUKernelLibrary.array_sum(arr)
mean = GPUKernelLibrary.array_mean(arr)
std = GPUKernelLibrary.array_std(arr)

# Matrix operations
a = np.random.randn(1000, 1000)
b = np.random.randn(1000, 1000)
result = GPUKernelLibrary.matrix_multiply(a, b)
```

### 5. Multi-GPU Support

Select specific GPU device:

```python
from python_optimizer import set_gpu_device, get_gpu_device

# Set to GPU 1
set_gpu_device(1)

# Get device info
device = get_gpu_device(1)
print(f"Using {device.name}")
print(f"Memory: {device.memory_gb:.2f} GB")
print(f"Compute: {device.compute_capability}")
```

### 6. GPU Genetic Algorithm Optimizer

Accelerate genetic algorithm optimization with GPU-accelerated fitness
evaluation:

```python
from python_optimizer.gpu import GPUGeneticOptimizer
from python_optimizer.genetic import ParameterRange

# Define parameter search space
param_ranges = [
    ParameterRange('x', -10.0, 10.0, 'float'),
    ParameterRange('y', -10.0, 10.0, 'float'),
]

# Fitness function to maximize
def fitness_function(params):
    x, y = params['x'], params['y']
    # Expensive computation here
    return -(x**2 + y**2)

# Create GPU genetic optimizer
optimizer = GPUGeneticOptimizer(
    parameter_ranges=param_ranges,
    population_size=10000,  # Large population benefits from GPU
    use_gpu=True,
    gpu_batch_size=1000  # Process in batches
)

# Run optimization
best = optimizer.optimize(
    fitness_function=fitness_function,
    generations=100,
    verbose=True
)

print(f"Best parameters: {best.parameters}")
print(f"Best fitness: {best.fitness}")

# Check GPU statistics
stats = optimizer.get_gpu_stats()
print(f"GPU evaluations: {stats['gpu_evaluations']}")
print(f"GPU time: {stats['gpu_time_seconds']:.2f}s")
print(f"Speedup: {stats['gpu_usage_percent']:.1f}% on GPU")
```

**Expected Speedup**: 10-100x for large populations (>1000 individuals)

**Key Features**:
- Batch-based fitness evaluation on GPU
- Automatic CPU fallback
- Memory-efficient processing
- Configurable batch sizes
- Performance tracking and statistics

## API Reference

### Decorator Parameters

```python
@optimize(
    gpu: bool = False,           # Enable GPU acceleration
    gpu_min_size: int = 10000,   # Min elements to use GPU
    jit: bool = True,            # Can combine with JIT
    specialize: bool = False,    # Can combine with specialization
    # ... other parameters
)
```

### GPU Functions

#### Device Management

```python
is_gpu_available() -> bool
    """Check if GPU is available."""

get_gpu_info() -> dict
    """Get comprehensive GPU information."""

set_gpu_device(device_id: int) -> bool
    """Set active GPU device."""

get_gpu_device(device_id: Optional[int] = None) -> GPUDevice
    """Get GPU device information."""
```

#### Memory Management

```python
get_gpu_memory_info(device_id: Optional[int] = None) -> GPUMemoryInfo
    """Get GPU memory usage information."""

clear_gpu_cache(device_id: Optional[int] = None)
    """Clear GPU memory cache."""

set_gpu_memory_limit(limit_gb: float, device_id: Optional[int] = None)
    """Set GPU memory usage limit."""
```

#### Dispatcher

```python
class GPUDispatcher:
    def __init__(
        self,
        min_size_threshold: int = 10000,
        max_size_threshold: Optional[int] = None,
        force_gpu: bool = False,
        force_cpu: bool = False
    )

    def should_use_gpu(*args, **kwargs) -> bool
        """Determine if GPU should be used."""

    def dispatch(cpu_func, gpu_func, *args, **kwargs) -> Any
        """Dispatch to CPU or GPU."""

    def wrap(cpu_func=None, gpu_func=None)
        """Decorator for automatic dispatching."""

    def get_stats() -> dict
        """Get dispatcher statistics."""
```

#### GPU Genetic Optimizer

```python
class GPUGeneticOptimizer(GeneticOptimizer):
    def __init__(
        self,
        parameter_ranges: List[ParameterRange],
        population_size: int = 100,
        mutation_rate: float = 0.1,
        crossover_rate: float = 0.7,
        elitism_count: int = 2,
        tournament_size: int = 3,
        use_gpu: bool = True,
        gpu_batch_size: Optional[int] = None,
        force_cpu: bool = False
    )
    """GPU-accelerated genetic algorithm optimizer.

    Args:
        parameter_ranges: Parameter ranges to optimize
        population_size: Population size (larger = more GPU benefit)
        use_gpu: Enable GPU acceleration
        gpu_batch_size: Batch size for GPU (None = auto)
        force_cpu: Force CPU execution
    """

    def optimize(
        self,
        fitness_function: Callable,
        generations: int = 100,
        target_fitness: Optional[float] = None,
        verbose: bool = True
    ) -> Individual
        """Run GPU-accelerated genetic optimization."""

    def get_gpu_stats() -> dict
        """Get GPU optimization statistics."""

# Convenience function
optimize_genetic_gpu(
    parameter_ranges: List[ParameterRange],
    fitness_function: Callable,
    population_size: int = 100,
    generations: int = 100,
    use_gpu: bool = True,
    **kwargs
) -> Individual
    """Quick GPU genetic optimization."""
```

### Environment Variables

```bash
# Disable GPU even if available
export PYTHON_OPTIMIZER_NO_GPU=1

# Enable verbose GPU logging
export PYTHON_OPTIMIZER_GPU_DEBUG=1
```

## Performance Guidelines

### Optimal Use Cases

**Best Performance** (5-20x speedup typical):
- Matrix operations (>1000x1000)
- Element-wise array operations (>100K elements)
- Reduction operations (sum, mean, std) on large arrays
- Cumulative operations (cumsum)
- Sorting large arrays

**Moderate Performance** (2-5x speedup):
- Array operations (10K-100K elements)
- Smaller matrix operations (100x100 to 1000x1000)

**Limited Benefit** (<2x speedup):
- Small arrays (<10K elements)
- Operations with frequent CPU<->GPU transfers
- Complex branching logic

### Size Thresholds

Recommended `gpu_min_size` values:

| Operation Type | Min Size | Reason |
|----------------|----------|--------|
| Element-wise ops | 10,000 | Transfer overhead |
| Matrix multiply | 1,000 | Computation intensity |
| Reductions | 50,000 | Simple operations |
| Complex ops | 5,000 | Higher GPU benefit |

### Memory Considerations

```python
# Monitor memory usage
from python_optimizer import get_gpu_memory_info

mem = get_gpu_memory_info()

# Rule of thumb: Keep utilization < 90%
if mem.utilization_percent > 90:
    clear_gpu_cache()
```

### Benchmarking

```python
import time
import numpy as np

@optimize(gpu=True)
def gpu_version(data):
    return data ** 2 + data * 3

@optimize(gpu=False)
def cpu_version(data):
    return data ** 2 + data * 3

# Benchmark
data = np.random.randn(1_000_000).astype(np.float32)

# GPU timing
start = time.perf_counter()
result_gpu = gpu_version(data)
gpu_time = time.perf_counter() - start

# CPU timing
start = time.perf_counter()
result_cpu = cpu_version(data)
cpu_time = time.perf_counter() - start

print(f"GPU: {gpu_time*1000:.2f} ms")
print(f"CPU: {cpu_time*1000:.2f} ms")
print(f"Speedup: {cpu_time/gpu_time:.1f}x")
```

## Troubleshooting

### GPU Not Detected

**Problem**: `is_gpu_available()` returns `False`

**Solutions**:
1. Check CUDA installation: `nvidia-smi`
2. Verify CuPy installation: `python -c "import cupy"`
3. Check CUDA version compatibility
4. Ensure GPU drivers are up-to-date

### Out of Memory Errors

**Problem**: `cupy.cuda.memory.OutOfMemoryError`

**Solutions**:
```python
# 1. Clear cache
from python_optimizer import clear_gpu_cache
clear_gpu_cache()

# 2. Set memory limit
from python_optimizer.gpu import set_gpu_memory_limit
set_gpu_memory_limit(4.0)  # Limit to 4 GB

# 3. Process in batches
def process_batches(large_data, batch_size=100_000):
    results = []
    for i in range(0, len(large_data), batch_size):
        batch = large_data[i:i+batch_size]
        results.append(compute_gpu(batch))
        clear_gpu_cache()  # Clear between batches
    return np.concatenate(results)
```

### Slow GPU Performance

**Problem**: GPU slower than CPU

**Solutions**:
1. Increase `gpu_min_size` threshold
2. Reduce CPU<->GPU transfers
3. Use batch processing
4. Profile with `profile=True`

```python
# Increase threshold
@optimize(gpu=True, gpu_min_size=100_000)  # Higher threshold

# Check dispatcher stats
from python_optimizer.gpu import GPUDispatcher
dispatcher = GPUDispatcher()
# ... use dispatcher ...
print(dispatcher.get_stats())
```

### CuPy Import Errors

**Problem**: `ImportError: cannot import name 'cupy'`

**Solutions**:
```bash
# Reinstall CuPy
pip uninstall cupy cupy-cuda12x
pip install cupy-cuda12x

# Check CUDA version
python -c "import cupy; print(cupy.cuda.runtime.runtimeGetVersion())"
```

### Multiple GPU Selection

```python
# List all GPUs
info = get_gpu_info()
for i, device in enumerate(info['devices']):
    print(f"GPU {i}: {device['name']}")

# Select specific GPU
from python_optimizer import set_gpu_device
set_gpu_device(1)  # Use GPU 1
```

## Advanced Examples

### Custom GPU Dispatcher

```python
from python_optimizer.gpu import GPUDispatcher
import numpy as np

# Create custom dispatcher with aggressive settings
dispatcher = GPUDispatcher(
    min_size_threshold=1000,    # Lower threshold
    force_gpu=False,
    force_cpu=False
)

@dispatcher.wrap()
def custom_compute(x, y):
    return x * y + np.sqrt(x)

# Monitor performance
result = custom_compute(large_array, large_array)
stats = dispatcher.get_stats()
print(f"GPU usage: {stats['gpu_usage_percent']:.1f}%")
print(f"GPU calls: {stats['gpu_calls']}")
print(f"Fallbacks: {stats['gpu_fallbacks']}")
```

### Hybrid CPU/GPU Pipeline

```python
@optimize(gpu=False)  # Keep on CPU
def preprocess(data):
    return data[data > 0]  # Filtering

@optimize(gpu=True, gpu_min_size=10_000)  # GPU for computation
def compute(data):
    return data ** 2 + np.log(data)

@optimize(gpu=False)  # Back to CPU for output
def postprocess(data):
    return data.tolist()

# Pipeline
data = np.random.randn(1_000_000)
result = postprocess(compute(preprocess(data)))
```

## See Also

- [Optimization Overview](optimization_overview.md)
- [Performance Guide](performance_guide.md)
- [Examples](../examples/gpu_optimization.py)
