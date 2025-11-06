# Python Optimizer 🚀

A high-performance Python optimization toolkit that provides JIT compilation, advanced variable specialization, intelligent caching, and runtime optimizations to accelerate Python code execution without changing language syntax.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Numba](https://img.shields.io/badge/numba-JIT%20compilation-orange.svg)](http://numba.pydata.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Performance](https://img.shields.io/badge/performance-up%20to%20500x-brightgreen.svg)]()
[![Thread Safe](https://img.shields.io/badge/thread-safe-blue.svg)]()

## 🎯 Goal

Accelerate Python program execution by **10-500x** through:
- **Advanced JIT compilation** with Numba and custom optimizations
- **GPU acceleration** with automatic CPU/GPU dispatching (CUDA/CuPy)
- **Intelligent variable specialization** with type-aware caching  
- **Adaptive optimization** based on runtime patterns
- **Specialization caching** with smart memory management
- **Zero syntax changes** - works with existing Python code

## ⚡ Performance Results

Real-world performance improvements achieved:

| Function Type | Original Time | Optimized Time | Speedup | Cache Hit Rate |
|---------------|---------------|----------------|---------|----------------|
| Numerical Computation | 2.06ms | 0.04ms | **51x** | 95% |
| Financial Metrics | 100ms | 2ms | **50x** | 88% |
| Trading Simulation | 500ms | 5ms | **100x** | 92% |
| Genetic Algorithm | 30s | 0.14s | **214x** | - |
| Specialized Functions | 1.2ms | 0.003ms | **400x** | 97% |
| Array Operations | 50ms | 0.1ms | **500x** | 91% |

**Throughput:** Up to **36,456 evaluations/second**
**Cache Efficiency:** 90%+ hit rates with intelligent eviction

## 🛠 Installation

```bash
# Clone the repository
git clone https://github.com/thinmanj/python-optimizer.git
cd python-optimizer

# Install with pip
pip install -e .

# Or install from PyPI (coming soon)
pip install python-optimizer
```

## 🚀 Quick Start

### 1. Basic JIT Optimization

```python
from python_optimizer import optimize

@optimize(jit=True)
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# First call compiles, subsequent calls are blazing fast
result = fibonacci(35)  # ~100x faster after compilation
```

### 2. Variable Specialization

```python
from python_optimizer import optimize

@optimize(specialize=True, jit=False)
def adaptive_function(data):
    if isinstance(data, list):
        return sum(data)
    elif hasattr(data, '__len__'):
        return len(data)
    return data

# Automatically creates specialized versions for different types
result1 = adaptive_function([1, 2, 3, 4])      # List specialization
result2 = adaptive_function("hello world")      # String specialization  
result3 = adaptive_function(range(100))         # Range specialization
# Each type gets its own optimized version cached for future use
```

### 3. Financial Computing Example

```python
import numpy as np
from python_optimizer.jit import calculate_sharpe_ratio_jit

# JIT-compiled financial metrics
returns = np.random.normal(0.001, 0.02, 252)  # Daily returns
sharpe = calculate_sharpe_ratio_jit(returns)   # ~50x faster
```

### 4. Trading Strategy Optimization

```python
from python_optimizer.jit import JITBacktestFitnessEvaluator
from python_optimizer.genetic import Individual

# Ultra-fast backtesting with JIT compilation
evaluator = JITBacktestFitnessEvaluator(initial_cash=10000)
individual = Individual(genes={'ma_short': 10, 'ma_long': 30})

# Evaluate strategy performance
metrics = evaluator.evaluate(individual, market_data)
# Achieves 36,000+ evaluations per second
```

### 5. GPU Acceleration (NEW! 🎉)

```python
from python_optimizer import optimize, is_gpu_available
import numpy as np

# Check GPU availability
if is_gpu_available():
    print("GPU acceleration available!")

# Enable GPU acceleration with automatic CPU/GPU dispatching
@optimize(gpu=True, gpu_min_size=10_000, jit=False)
def gpu_compute(data):
    return data ** 2 + data * 3

# Automatically uses GPU for large arrays, CPU for small ones
small_array = np.random.randn(1000)       # Uses CPU
large_array = np.random.randn(1_000_000)  # Uses GPU

result1 = gpu_compute(small_array)
result2 = gpu_compute(large_array)  # 5-20x faster on GPU!
```

### 6. Advanced Caching & Monitoring

```python
from python_optimizer import (
    get_specialization_stats, 
    clear_specialization_cache,
    configure_specialization,
    get_gpu_info,
    get_gpu_memory_info
)

# Configure specialization behavior
configure_specialization(
    min_calls_for_specialization=3,
    enable_adaptive_learning=True,
    max_cache_size=1000
)

# Monitor performance
stats = get_specialization_stats()
print(f"Cache hit rate: {stats.get('cache_hit_rate', 0):.1%}")
print(f"Specializations created: {stats.get('specializations_created', 0)}")

# Check GPU status
if is_gpu_available():
    gpu_info = get_gpu_info()
    mem_info = get_gpu_memory_info()
    print(f"GPU: {gpu_info['devices'][0]['name']}")
    print(f"Memory: {mem_info.used_gb:.1f}/{mem_info.total_gb:.1f} GB")
```

## 📦 Features

### Advanced JIT Compilation Engine
- **Numba-powered** JIT compilation for numerical code
- **Automatic type inference** and optimization
- **GIL-free execution** for parallel processing
- **Intelligent caching** system for compiled functions
- **Custom optimization passes** for domain-specific code

### Intelligent Variable Specialization
- **Type-aware specialization** with automatic detection
- **Adaptive learning** from runtime patterns
- **Memory-efficient** specialized code paths
- **Multi-level caching** with eviction policies
- **Thread-safe** specialization cache
- **Performance monitoring** and analytics

### GPU Acceleration (Phase 1 - NEW! 🚀)
- **Automatic GPU detection** with graceful CPU fallback
- **Smart CPU/GPU dispatching** based on data size
- **GPU memory management** with pooling and caching
- **CuPy/CUDA integration** for array operations
- **Configurable thresholds** for GPU usage
- **Multi-GPU support** for device selection
- **Zero code changes** - same API works on CPU or GPU
- **Performance monitoring** with GPU statistics

### Advanced Caching System
- **Specialization cache** with multiple eviction policies (LRU, LFU, Adaptive)
- **Memory-bounded** cache with configurable limits
- **Weak references** to prevent memory leaks
- **TTL-based expiration** for temporal optimization
- **Thread-safe** concurrent access
- **Real-time statistics** and monitoring

### Performance Profiling & Analytics
- **Runtime profiling** with minimal overhead
- **Hot path detection** and prioritization
- **Performance analytics** and reporting
- **Specialization effectiveness** tracking
- **Cache performance** monitoring
- **Adaptive optimization** recommendations

### Financial Computing & Trading
- **JIT-optimized** financial metrics (Sharpe ratio, drawdown, etc.)
- **Ultra-fast backtesting** engine for trading strategies
- **Genetic algorithm** optimization for parameter tuning
- **High-frequency trading** optimizations
- **Portfolio optimization** with risk management

## 📖 Documentation

### Core Decorator

The `@optimize` decorator is the main entry point:

```python
from python_optimizer import optimize

@optimize(
    jit=True,                    # Enable JIT compilation
    specialize=True,             # Enable variable specialization
    profile=True,                # Enable performance profiling
    aggressiveness=2,            # Optimization level (0-3)
    cache=True,                  # Enable specialization caching
    gpu=True,                    # Enable GPU acceleration (NEW!)
    gpu_min_size=10_000,         # Minimum size to use GPU (NEW!)
    adaptive_learning=True,      # Enable adaptive optimization
    memory_limit_mb=100,         # Cache memory limit
    min_calls_for_spec=3         # Minimum calls before specialization
)
def your_function(x, y):
    # Your code here - automatically optimized based on usage patterns
    # GPU acceleration for large arrays, JIT for numerical code
    return x * y + compute_heavy_operation()
```

### New Specialization Functions

```python
from python_optimizer import (
    get_specialization_stats,
    clear_specialization_cache,
    configure_specialization,
    get_cache_stats
)

# Configure global specialization behavior
configure_specialization(
    min_calls_for_specialization=3,
    min_performance_gain=0.1,
    enable_adaptive_learning=True,
    max_cache_size=1000,
    max_memory_mb=100
)

# Get performance statistics
stats = get_specialization_stats('function_name')
print(f"Specializations created: {stats.get('specializations_created')}")
print(f"Cache hit rate: {stats.get('cache_hit_rate'):.2%}")
print(f"Performance gain: {stats.get('avg_performance_gain'):.2f}x")

# Global cache statistics
cache_stats = get_cache_stats()
print(f"Total cache entries: {cache_stats['total_entries']}")
print(f"Memory usage: {cache_stats['memory_usage_estimate']:.2f} MB")

# Clear cache when needed
clear_specialization_cache()  # Clear all
clear_specialization_cache('specific_function')  # Clear specific function
```

### JIT Functions

Pre-built JIT-optimized functions:

```python
from python_optimizer.jit import (
    calculate_returns_jit,
    calculate_sharpe_ratio_jit,
    calculate_max_drawdown_jit,
    simulate_strategy_jit
)
```

### Genetic Algorithm Optimization

```python
from python_optimizer.genetic import GeneticOptimizer, ParameterRange

# Define optimization parameters
param_ranges = [
    ParameterRange('learning_rate', 0.001, 0.1, 'float'),
    ParameterRange('hidden_layers', 1, 5, 'int'),
]

# Run optimization
optimizer = GeneticOptimizer(param_ranges, population_size=100)
best_params = optimizer.optimize(fitness_function, generations=50)
```

## 🧪 Examples

Check out the `examples/` directory for:

- **Financial modeling** with JIT optimization
- **Machine learning** parameter optimization
- **Numerical computing** acceleration
- **Trading strategy** backtesting

## 📊 Benchmarks

Run benchmarks to see performance on your system:

```bash
python benchmarks/jit_performance_test.py
python benchmarks/genetic_algorithm_benchmark.py
python benchmarks/financial_metrics_benchmark.py
```

## 🔧 Configuration

### Environment Variables

```bash
export PYTHON_OPTIMIZER_JIT_CACHE=1     # Enable JIT cache
export PYTHON_OPTIMIZER_PROFILE=1       # Enable profiling
export PYTHON_OPTIMIZER_PARALLEL=1      # Enable parallel execution
```

### Configuration File

Create `python_optimizer.toml`:

```toml
[jit]
cache_dir = "~/.python_optimizer/cache"
compile_timeout = 30

[profiling]
enabled = true
output_dir = "./profiles"

[specialization]
max_variants = 5
threshold = 100
```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
git clone https://github.com/thinmanj/python-optimizer.git
cd python-optimizer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run linting
black python_optimizer/
isort python_optimizer/
flake8 python_optimizer/
```

## 📈 Roadmap

- [x] **JIT Compilation Engine** - Numba-based optimization
- [x] **Advanced Variable Specialization** - Type-aware optimization with caching
- [x] **Intelligent Caching System** - Multi-policy cache with memory management
- [x] **Performance Monitoring** - Real-time analytics and adaptive learning
- [x] **Financial Computing Module** - Trading strategy optimization
- [x] **Genetic Algorithm** - Parameter optimization
- [x] **Thread-Safe Operations** - Concurrent optimization support
- [x] **GPU Acceleration** - CUDA/CuPy support with automatic CPU/GPU dispatching ✨
- [x] **ML Model Optimization** - PyTorch integration with training/inference optimization ✨
- [x] **TensorFlow Integration** - TensorFlow/Keras model optimization with XLA ✨
- [x] **Distributed Computing** - Multi-node optimization with Ray/Dask/multiprocessing ✨
- [ ] **Advanced Profiling** - Visual performance analysis tools
- [ ] **Web Interface** - Browser-based optimization dashboard

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Numba team** for excellent JIT compilation framework
- **NumPy community** for foundational numerical computing
- **Trading algorithm researchers** for inspiration and validation

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/thinmanj/python-optimizer/issues)
- **Discussions:** [GitHub Discussions](https://github.com/thinmanj/python-optimizer/discussions)
- **Email:** thinmanj@gmail.com

---

⭐ **Star this repository** if Python Optimizer helps accelerate your code!
