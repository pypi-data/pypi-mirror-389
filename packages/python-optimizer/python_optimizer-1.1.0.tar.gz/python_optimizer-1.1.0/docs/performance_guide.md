# Performance Optimization Guide

## Understanding Modern Python Optimization

### What is Advanced Optimization?

Python Optimizer combines multiple optimization techniques:
- **JIT Compilation**: Translates Python to optimized machine code at runtime
- **Variable Specialization**: Creates type-specific optimized versions of functions
- **Intelligent Caching**: Stores and reuses optimized code with smart eviction policies
- **Adaptive Learning**: Automatically improves optimization strategies based on usage patterns

### Performance Expectations

| Code Type | JIT Only | JIT + Specialization | Expected Cache Hit Rate |
|-----------|----------|---------------------|------------------------|
| Numerical loops | 10-100x | 50-400x | 95% |
| Mathematical operations | 5-50x | 20-200x | 90% |
| Array operations | 2-20x | 10-500x | 92% |
| Financial calculations | 20-200x | 100-1000x | 88% |
| Recursive algorithms | 50-500x | 200-2000x | 97% |
| Type-polymorphic functions | 2-10x | 50-300x | 85% |

## Optimization Strategies

### 1. Variable Specialization Best Practices

#### ✅ Specialization-Friendly Code

```python
@optimize(specialize=True, jit=False, adaptive_learning=True)
def polymorphic_processor(data):
    """Function that benefits from specialization."""
    if isinstance(data, list):
        return sum(x * x for x in data)
    elif isinstance(data, tuple):
        return sum(x * x for x in data)
    elif hasattr(data, '__len__') and hasattr(data, '__getitem__'):
        total = 0
        for i in range(len(data)):
            total += data[i] * data[i]
        return total
    else:
        return data * data

# Each type gets specialized version cached
result1 = polymorphic_processor([1, 2, 3, 4])        # List specialization
result2 = polymorphic_processor((1, 2, 3, 4))        # Tuple specialization  
result3 = polymorphic_processor(np.array([1, 2, 3, 4]))  # NumPy specialization
```

#### Monitoring Specialization Performance

```python
from python_optimizer import get_specialization_stats

# Monitor performance
stats = get_specialization_stats('polymorphic_processor')
print(f"Specializations created: {stats.get('specializations_created')}")
print(f"Cache hit rate: {stats.get('cache_hit_rate', 0):.1%}")
print(f"Performance gain: {stats.get('avg_performance_gain', 1):.2f}x")
```

### 2. JIT Compilation Best Practices

#### ✅ JIT-Friendly Code

```python
@optimize(jit=True)
def matrix_multiply_jit(A, B):
    """Efficient matrix multiplication."""
    rows_A, cols_A = A.shape
    rows_B, cols_B = B.shape
    
    if cols_A != rows_B:
        raise ValueError("Matrix dimensions don't match")
    
    C = np.zeros((rows_A, cols_B))
    for i in range(rows_A):
        for j in range(cols_B):
            for k in range(cols_A):
                C[i, j] += A[i, k] * B[k, j]
    
    return C
```

#### ❌ JIT-Unfriendly Code

```python
# Avoid - uses object-oriented features
class Calculator:
    def compute(self, data):
        return sum(data)

# Avoid - uses string operations
def process_text(text):
    return text.upper().replace(" ", "_")

# Avoid - uses dynamic typing
def dynamic_function(data):
    if isinstance(data, list):
        return sum(data)
    elif isinstance(data, dict):
        return sum(data.values())
```

### 2. Memory Optimization

#### Pre-allocate Arrays

```python
@optimize(jit=True)
def efficient_computation(n):
    # Pre-allocate output array
    result = np.zeros(n)
    
    for i in range(n):
        result[i] = expensive_calculation(i)
    
    return result
```

#### Use Appropriate Data Types

```python
# Use specific dtypes for better performance
data = np.array([1, 2, 3, 4, 5], dtype=np.float64)

@optimize(jit=True)
def compute_with_dtype(arr):
    # NumPy dtypes are JIT-friendly
    return np.sum(arr * 2.0)
```

### 3. Cache Optimization

#### Optimal Cache Configuration

```python
from python_optimizer import configure_specialization
from python_optimizer.specialization_cache import EvictionPolicy

# Configure for memory-constrained environments
configure_specialization(
    max_cache_size=100,
    max_memory_mb=10,
    eviction_policy='size_based',
    min_calls_for_specialization=5
)

# Configure for high-performance scenarios
configure_specialization(
    max_cache_size=5000,
    max_memory_mb=500,
    eviction_policy='adaptive',
    min_calls_for_specialization=2,
    enable_adaptive_learning=True
)
```

#### Cache Performance Monitoring

```python
from python_optimizer import get_cache_stats
import time

def monitor_cache_performance():
    """Monitor cache performance and suggest optimizations."""
    stats = get_cache_stats()
    
    print(f"Cache Statistics:")
    print(f"  Total entries: {stats['total_entries']}")
    print(f"  Memory usage: {stats['memory_usage_estimate']:.2f} MB")
    print(f"  Hit rate: {stats['hit_rate']:.2%}")
    print(f"  Evictions: {stats['evictions']}")
    
    # Performance recommendations
    if stats['hit_rate'] < 0.7:
        print("⚠️  Low hit rate - consider increasing cache size")
    
    if stats['evictions'] > stats['total_entries']:
        print("⚠️  High eviction rate - increase memory limit")
    
    if stats['memory_usage_estimate'] > 100:
        print("⚠️  High memory usage - consider size-based eviction")

# Run monitoring periodically
monitor_cache_performance()
```

### 4. Loop Optimization

#### Vectorization vs JIT Loops

```python
# Option 1: Vectorized (good for simple operations)
def vectorized_operation(data):
    return data * 2 + np.sin(data)

# Option 2: JIT loops (good for complex logic)
@optimize(jit=True)
def jit_loop_operation(data):
    result = np.zeros_like(data)
    for i in range(len(data)):
        if data[i] > 0:
            result[i] = data[i] * 2 + np.sin(data[i])
        else:
            result[i] = data[i] / 2
    return result
```

## Benchmarking and Profiling

### Performance Testing

```python
import time
import numpy as np
from python_optimizer import optimize

def benchmark_function(func, data, runs=5):
    """Benchmark a function with multiple runs."""
    times = []
    
    for _ in range(runs):
        start = time.perf_counter()
        result = func(data)
        end = time.perf_counter()
        times.append(end - start)
    
    return {
        'mean_time': np.mean(times),
        'std_time': np.std(times),
        'min_time': np.min(times),
        'max_time': np.max(times)
    }

# Example usage
data = np.random.random(100000)

# Python version
def python_sum(arr):
    total = 0.0
    for x in arr:
        total += x * x
    return total

# JIT version
@optimize(jit=True)
def jit_sum(arr):
    total = 0.0
    for i in range(len(arr)):
        total += arr[i] * arr[i]
    return total

# Benchmark both
python_stats = benchmark_function(python_sum, data)
jit_stats = benchmark_function(jit_sum, data)

speedup = python_stats['mean_time'] / jit_stats['mean_time']
print(f"Speedup: {speedup:.2f}x")
```

### Profiling with cProfile

```python
import cProfile
import pstats

def profile_optimization():
    """Profile code to identify bottlenecks."""
    
    # Profile your code
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Run your function
    result = your_function(data)
    
    profiler.disable()
    
    # Analyze results
    stats = pstats.Stats(profiler)
    stats.sort_stats('tottime')
    stats.print_stats(10)  # Top 10 functions
    
    return result
```

## Common Performance Patterns

### 1. Financial Computing

```python
@optimize(jit=True, fastmath=True)
def calculate_portfolio_metrics(returns, weights):
    """High-performance portfolio calculations."""
    n_assets, n_periods = returns.shape
    
    # Portfolio returns
    portfolio_returns = np.zeros(n_periods)
    for t in range(n_periods):
        for i in range(n_assets):
            portfolio_returns[t] += weights[i] * returns[i, t]
    
    # Performance metrics
    mean_return = np.mean(portfolio_returns)
    volatility = np.std(portfolio_returns)
    sharpe_ratio = mean_return / volatility if volatility > 0 else 0
    
    # Maximum drawdown
    cumulative = np.cumprod(1 + portfolio_returns)
    running_max = cumulative[0]
    max_dd = 0.0
    
    for i in range(1, len(cumulative)):
        if cumulative[i] > running_max:
            running_max = cumulative[i]
        else:
            drawdown = (running_max - cumulative[i]) / running_max
            if drawdown > max_dd:
                max_dd = drawdown
    
    return {
        'return': mean_return,
        'volatility': volatility,
        'sharpe': sharpe_ratio,
        'max_drawdown': max_dd
    }
```

### 2. Machine Learning

```python
@optimize(jit=True, fastmath=True)
def kmeans_iteration(data, centroids):
    """JIT-optimized K-means iteration."""
    n_samples, n_features = data.shape
    n_clusters = centroids.shape[0]
    
    # Assign points to clusters
    assignments = np.zeros(n_samples, dtype=np.int32)
    
    for i in range(n_samples):
        min_distance = np.inf
        best_cluster = 0
        
        for j in range(n_clusters):
            distance = 0.0
            for k in range(n_features):
                diff = data[i, k] - centroids[j, k]
                distance += diff * diff
            
            if distance < min_distance:
                min_distance = distance
                best_cluster = j
        
        assignments[i] = best_cluster
    
    # Update centroids
    new_centroids = np.zeros_like(centroids)
    counts = np.zeros(n_clusters)
    
    for i in range(n_samples):
        cluster = assignments[i]
        counts[cluster] += 1
        for k in range(n_features):
            new_centroids[cluster, k] += data[i, k]
    
    for j in range(n_clusters):
        if counts[j] > 0:
            for k in range(n_features):
                new_centroids[j, k] /= counts[j]
    
    return assignments, new_centroids
```

### 3. Signal Processing

```python
@optimize(jit=True, fastmath=True)
def moving_average_filter(signal, window_size):
    """Fast moving average implementation."""
    n = len(signal)
    filtered = np.zeros(n)
    
    # Initialize first window
    window_sum = 0.0
    for i in range(min(window_size, n)):
        window_sum += signal[i]
        filtered[i] = window_sum / (i + 1)
    
    # Sliding window
    for i in range(window_size, n):
        window_sum = window_sum - signal[i - window_size] + signal[i]
        filtered[i] = window_sum / window_size
    
    return filtered
```

## Performance Troubleshooting

### Common Issues and Solutions

#### 1. Slow First Call (JIT Compilation)

**Problem**: First function call is very slow.

**Solution**: Warm up JIT functions:

```python
@optimize(jit=True)
def compute_intensive(data):
    # Your computation here
    pass

# Warm up with small data
small_data = np.random.random(100)
compute_intensive(small_data)

# Now use with real data
large_data = np.random.random(100000)
result = compute_intensive(large_data)
```

#### 2. Type Inference Issues

**Problem**: JIT compilation fails due to unclear types.

**Solution**: Provide explicit type hints:

```python
import numba as nb

@nb.jit(nb.float64(nb.float64[:]), nopython=True)
def explicit_types(arr):
    return np.sum(arr)
```

#### 3. Memory Allocation Overhead

**Problem**: Frequent array allocations slow down code.

**Solution**: Pre-allocate and reuse arrays:

```python
@optimize(jit=True)
def efficient_batch_processing(data_batches):
    batch_size = len(data_batches[0])
    temp_array = np.zeros(batch_size)  # Pre-allocate
    results = []
    
    for batch in data_batches:
        # Reuse temp_array instead of creating new ones
        for i in range(batch_size):
            temp_array[i] = expensive_operation(batch[i])
        results.append(temp_array.copy())
    
    return results
```

## Advanced Optimization Techniques

### Parallel Processing

```python
@optimize(jit=True, parallel=True)
def parallel_computation(data):
    """Parallel JIT computation."""
    n = len(data)
    result = np.zeros(n)
    
    # This loop will be parallelized
    for i in nb.prange(n):
        result[i] = expensive_calculation(data[i])
    
    return result
```

### Custom JIT Functions

```python
from numba import njit

@njit(cache=True, fastmath=True)
def custom_jit_function(x, y):
    """Custom JIT function with specific optimizations."""
    return np.sqrt(x*x + y*y)

# Use in optimized decorator
@optimize(jit=True)
def main_computation(data):
    result = np.zeros(len(data))
    for i in range(len(data)):
        result[i] = custom_jit_function(data[i], data[i] * 2)
    return result
```

### GPU Acceleration (Advanced)

```python
from numba import cuda

@cuda.jit
def gpu_kernel(data, result):
    """CUDA kernel for GPU acceleration."""
    idx = cuda.grid(1)
    if idx < data.size:
        result[idx] = expensive_gpu_calculation(data[idx])

def gpu_optimized_function(data):
    """CPU function that uses GPU kernel."""
    # Allocate GPU memory
    d_data = cuda.to_device(data)
    d_result = cuda.device_array_like(data)
    
    # Configure grid and block dimensions
    threads_per_block = 256
    blocks_per_grid = (data.size + threads_per_block - 1) // threads_per_block
    
    # Launch kernel
    gpu_kernel[blocks_per_grid, threads_per_block](d_data, d_result)
    
    # Copy result back to CPU
    return d_result.copy_to_host()
```

## Performance Monitoring

### Runtime Performance Tracking

```python
from python_optimizer.profiling import PerformanceProfiler
import matplotlib.pyplot as plt

profiler = PerformanceProfiler()

@profiler.profile
@optimize(jit=True)
def monitored_function(data):
    # Your computation
    return np.sum(data ** 2)

# Run multiple times
for i in range(100):
    data = np.random.random(1000)
    result = monitored_function(data)

# Plot performance over time
stats = profiler.get_stats()
times = [s.execution_time for s in stats.history]

plt.figure(figsize=(10, 6))
plt.plot(times)
plt.title('Execution Time Over Iterations')
plt.xlabel('Iteration')
plt.ylabel('Time (seconds)')
plt.show()
```

This guide provides comprehensive strategies for maximizing performance with Python Optimizer. Focus on JIT-friendly code patterns, proper benchmarking, and systematic optimization approaches.
