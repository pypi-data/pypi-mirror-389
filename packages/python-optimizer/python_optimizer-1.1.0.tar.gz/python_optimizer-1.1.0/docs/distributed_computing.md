# Distributed Computing

Python Optimizer provides distributed computing capabilities to scale optimization across multiple cores, nodes, and clusters. Distribute expensive computations for massive speedup.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Backends](#backends)
- [Distributed Coordinator](#distributed-coordinator)
- [Distributed Genetic Algorithms](#distributed-genetic-algorithms)
- [API Reference](#api-reference)
- [Best Practices](#best-practices)
- [Examples](#examples)

## Overview

The distributed computing module provides:

- **Multi-Backend Support** - Multiprocessing (local), Ray (multi-node), Dask (alternative)
- **Distributed Coordinator** - Automatic task distribution and aggregation
- **Map/Reduce Operations** - Parallel processing patterns
- **Distributed Genetic Algorithms** - Massive speedup for population evaluation
- **Load Balancing** - Automatic work distribution across workers
- **Performance Monitoring** - Built-in statistics and throughput tracking

### Supported Backends

- **multiprocessing** (built-in) - Local multi-core execution
- **Ray** (optional) - Multi-node distributed computing
- **Dask** (optional) - Alternative distributed framework

## Installation

### Basic Installation

```bash
# Core distributed computing (multiprocessing only)
pip install python-optimizer
```

### With Ray (Recommended for Multi-Node)

```bash
# Install with Ray for multi-node support
pip install python-optimizer ray
```

### With Dask

```bash
# Install with Dask as alternative
pip install python-optimizer dask distributed
```

## Quick Start

### Local Multi-Core Distribution

```python
from python_optimizer.distributed import (
    BackendType,
    DistributedCoordinator,
    set_backend
)

# Set multiprocessing backend with 4 workers
set_backend(BackendType.MULTIPROCESSING, num_workers=4)

# Create coordinator
coordinator = DistributedCoordinator()

# Distribute computation
def expensive_function(x):
    return x ** 2

results = coordinator.map(expensive_function, range(1000))
print(f"Processed {len(results)} items")
```

### Distributed Genetic Algorithm

```python
from python_optimizer.distributed import DistributedGeneticOptimizer
from python_optimizer.genetic import ParameterRange

# Define parameter ranges
param_ranges = [
    ParameterRange('learning_rate', 0.001, 0.1, 'float'),
    ParameterRange('batch_size', 16, 128, 'int'),
]

# Create distributed optimizer
optimizer = DistributedGeneticOptimizer(
    parameter_ranges=param_ranges,
    population_size=200,
    num_workers=8
)

# Run optimization (fitness evaluation distributed across 8 workers)
best = optimizer.optimize(
    fitness_function=train_model,
    generations=50
)
```

## Backends

### Multiprocessing Backend (Default)

Best for: Local multi-core optimization

```python
from python_optimizer.distributed import BackendType, set_backend

# Use all CPU cores
backend = set_backend(BackendType.MULTIPROCESSING)

# Use specific number of workers
backend = set_backend(BackendType.MULTIPROCESSING, num_workers=4)
```

**Pros:**
- No additional dependencies
- Fast for local workloads
- Simple setup

**Cons:**
- Limited to single machine
- Python GIL limitations

### Ray Backend

Best for: Multi-node clusters, large-scale optimization

```python
from python_optimizer.distributed import BackendType, set_backend

# Connect to Ray cluster
backend = set_backend(
    BackendType.RAY,
    address='ray://cluster-head:10001'
)

# Or start local Ray cluster
backend = set_backend(BackendType.RAY, num_cpus=8)
```

**Pros:**
- Multi-node support
- Excellent scalability
- Fault tolerance
- GPU support

**Cons:**
- Requires Ray installation
- Cluster setup needed

### Dask Backend

Best for: Existing Dask infrastructure

```python
from python_optimizer.distributed import BackendType, set_backend

# Connect to Dask scheduler
backend = set_backend(
    BackendType.DASK,
    address='tcp://scheduler:8786'
)

# Or start local Dask cluster
backend = set_backend(BackendType.DASK, n_workers=4)
```

**Pros:**
- Integration with Dask ecosystem
- Good for data-heavy workflows
- Familiar API for Dask users

**Cons:**
- Requires Dask installation
- Slightly higher overhead

## Distributed Coordinator

The `DistributedCoordinator` handles task distribution and result aggregation.

### Basic Usage

```python
from python_optimizer.distributed import DistributedCoordinator, set_backend, BackendType

# Setup
set_backend(BackendType.MULTIPROCESSING, num_workers=4)
coordinator = DistributedCoordinator()

# Map function over items
results = coordinator.map(
    lambda x: x ** 2,
    range(100)
)
```

### Map-Reduce Pattern

```python
# Sum of squares using map-reduce
result = coordinator.reduce(
    func=lambda x: x ** 2,      # Map: square each number
    items=[1, 2, 3, 4, 5],
    reducer=lambda a, b: a + b,  # Reduce: sum results
    initial=0
)
# Result: 55
```

### Batch Submission

```python
# Submit batch of tasks with different arguments
results = coordinator.submit_batch(
    func=train_model,
    args_list=[
        ({'lr': 0.01}, {'epochs': 10}),
        ({'lr': 0.001}, {'epochs': 20}),
        ({'lr': 0.1}, {'epochs': 5})
    ]
)
```

### Statistics

```python
# Get performance statistics
stats = coordinator.get_stats()
print(f"Tasks completed: {stats['tasks_completed']}")
print(f"Throughput: {stats['throughput']:.1f} tasks/s")
print(f"Workers: {stats['num_workers']}")
```

## Distributed Genetic Algorithms

The `DistributedGeneticOptimizer` provides massive speedup for genetic algorithms by distributing fitness evaluation.

### Basic Example

```python
from python_optimizer.distributed import DistributedGeneticOptimizer, set_backend, BackendType
from python_optimizer.genetic import ParameterRange

# Setup backend
set_backend(BackendType.MULTIPROCESSING, num_workers=8)

# Define optimization problem
param_ranges = [
    ParameterRange('x', -10.0, 10.0, 'float'),
    ParameterRange('y', -10.0, 10.0, 'float'),
]

def fitness_function(params):
    # Expensive fitness computation
    x, y = params['x'], params['y']
    return -(x**2 + y**2)  # Maximize

# Create distributed optimizer
optimizer = DistributedGeneticOptimizer(
    parameter_ranges=param_ranges,
    population_size=1000,  # Large population
    num_workers=8
)

# Run optimization (fitness evaluation distributed)
best = optimizer.optimize(
    fitness_function=fitness_function,
    generations=100
)

print(f"Best solution: x={best.parameters['x']:.4f}, y={best.parameters['y']:.4f}")
print(f"Best fitness: {best.fitness:.4f}")
```

### Performance Benefits

**Speedup Example:**
- Sequential: 1000 fitness evaluations = 1000 seconds
- Distributed (8 workers): 1000 evaluations ≈ 125 seconds
- **Speedup: 8x**

### Statistics

```python
# Get distributed optimization statistics
stats = optimizer.get_distributed_stats()
print(f"Total evaluations: {stats['total_evaluations']}")
print(f"Throughput: {stats['throughput']:.1f} evals/s")
print(f"Workers: {stats['num_workers']}")
```

## API Reference

### Backend Management

#### `set_backend(backend_type, initialize=True, **kwargs)`

Set the distributed computing backend.

**Parameters:**
- `backend_type` (BackendType): Backend to use
- `initialize` (bool): Auto-initialize backend
- `**kwargs`: Backend-specific initialization arguments

**Returns:** Backend instance

**Example:**
```python
backend = set_backend(BackendType.MULTIPROCESSING, num_workers=4)
```

#### `get_backend()`

Get current backend instance.

**Returns:** Current backend

### DistributedCoordinator

#### `map(func, items, chunksize=None)`

Map function over items in parallel.

**Parameters:**
- `func` (Callable): Function to apply
- `items` (List): Items to process
- `chunksize` (int, optional): Items per task

**Returns:** List of results

#### `reduce(func, items, reducer, initial=None)`

Map-reduce operation.

**Parameters:**
- `func` (Callable): Map function
- `items` (List): Items to process
- `reducer` (Callable): Reduce function
- `initial` (Any): Initial value

**Returns:** Reduced result

#### `get_stats()`

Get performance statistics.

**Returns:** Dictionary with statistics

### DistributedGeneticOptimizer

#### `__init__(parameter_ranges, population_size, num_workers, backend, ...)`

Initialize distributed genetic optimizer.

**Parameters:**
- `parameter_ranges` (List[ParameterRange]): Parameters to optimize
- `population_size` (int): Population size
- `num_workers` (int, optional): Number of workers
- `backend` (str): Backend to use
- Additional parameters same as `GeneticOptimizer`

#### `optimize(fitness_function, generations, target_fitness, verbose)`

Run distributed optimization.

**Parameters:**
- `fitness_function` (Callable): Function to maximize
- `generations` (int): Number of generations
- `target_fitness` (float, optional): Early stopping threshold
- `verbose` (bool): Print progress

**Returns:** Best individual

## Best Practices

### Choosing a Backend

**Use Multiprocessing When:**
- Running on single machine
- Moderate workload (< 100 cores)
- Simple setup needed

**Use Ray When:**
- Multi-node cluster available
- Large-scale optimization (100+ cores)
- Need fault tolerance
- GPU acceleration required

**Use Dask When:**
- Already using Dask ecosystem
- Integration with Dask DataFrames
- Existing Dask infrastructure

### Performance Optimization

**DO:**
- Use distributed computing for expensive operations (>0.1s per task)
- Choose appropriate worker count (typically CPU count)
- Enable monitoring to track performance
- Use chunking for many small tasks

**DON'T:**
- Distribute very fast operations (overhead dominates)
- Use more workers than CPU cores (unless I/O bound)
- Forget to shutdown backends (use context managers)
- Distribute operations with large data transfer overhead

### Memory Management

```python
# Avoid passing large data to workers
# BAD:
large_array = np.zeros((10000, 10000))
results = coordinator.map(lambda x: process(x, large_array), items)

# GOOD: Load data inside worker
def process_with_data(x):
    large_array = load_data()  # Load in worker
    return process(x, large_array)

results = coordinator.map(process_with_data, items)
```

## Examples

### Example 1: Parallel Data Processing

```python
from python_optimizer.distributed import DistributedCoordinator, set_backend, BackendType

# Setup
set_backend(BackendType.MULTIPROCESSING, num_workers=8)
coordinator = DistributedCoordinator()

# Process files in parallel
def process_file(filename):
    # Expensive file processing
    data = load_and_process(filename)
    return analyze(data)

filenames = ['file1.csv', 'file2.csv', ..., 'file100.csv']
results = coordinator.map(process_file, filenames)

print(f"Processed {len(results)} files")
```

### Example 2: Hyperparameter Optimization

```python
from python_optimizer.distributed import DistributedGeneticOptimizer
from python_optimizer.genetic import ParameterRange

# Define hyperparameter search space
param_ranges = [
    ParameterRange('learning_rate', 1e-4, 1e-1, 'float'),
    ParameterRange('batch_size', 16, 256, 'int'),
    ParameterRange('hidden_dim', 64, 512, 'int'),
    ParameterRange('dropout', 0.0, 0.5, 'float'),
]

def train_and_evaluate(params):
    # Train model with given hyperparameters
    model = create_model(params)
    val_acc = train_model(model, params)
    return val_acc  # Return validation accuracy

# Distributed hyperparameter optimization
optimizer = DistributedGeneticOptimizer(
    parameter_ranges=param_ranges,
    population_size=100,
    num_workers=16
)

best_params = optimizer.optimize(
    fitness_function=train_and_evaluate,
    generations=50,
    verbose=True
)

print(f"Best hyperparameters: {best_params.parameters}")
print(f"Best validation accuracy: {best_params.fitness:.4f}")
```

### Example 3: Ray Cluster

```python
from python_optimizer.distributed import BackendType, DistributedCoordinator, set_backend

# Connect to Ray cluster
backend = set_backend(
    BackendType.RAY,
    address='ray://cluster-head.local:10001'
)

print(f"Connected to Ray with {backend.num_workers()} workers")

# Use cluster for large-scale optimization
coordinator = DistributedCoordinator()

def expensive_simulation(params):
    # Run expensive simulation
    return run_simulation(**params)

# Distribute across entire cluster
param_sets = generate_parameter_sets(10000)
results = coordinator.map(expensive_simulation, param_sets)

print(f"Completed {len(results)} simulations")
```

## Performance Tips

### Optimal Worker Count

```python
import multiprocessing as mp

# CPU-bound tasks: use CPU count
num_workers = mp.cpu_count()

# I/O-bound tasks: use 2-4x CPU count  
num_workers = mp.cpu_count() * 2
```

### Monitoring Performance

```python
coordinator = DistributedCoordinator()

# Run workload
results = coordinator.map(heavy_function, items)

# Check statistics
stats = coordinator.get_stats()
efficiency = stats['tasks_completed'] / (stats['total_time'] * stats['num_workers'])
print(f"Worker efficiency: {efficiency:.2%}")
```

### Chunking for Small Tasks

```python
# Many small tasks - use chunking
coordinator.map(fast_function, range(10000), chunksize=100)
```

## Troubleshooting

### "Backend not initialized" Error

```python
# Always set backend before using coordinator
set_backend(BackendType.MULTIPROCESSING, num_workers=4)
coordinator = DistributedCoordinator()
```

### Slow Performance

**Check:**
1. Task overhead: Are individual tasks expensive enough? (>0.1s recommended)
2. Data transfer: Are you passing large data to workers?
3. Worker count: Too many workers can cause overhead

**Debug:**
```python
stats = coordinator.get_stats()
print(f"Throughput: {stats['throughput']:.1f} tasks/s")
print(f"Avg task time: {stats['avg_task_time']:.4f}s")
```

### Memory Issues

**Solution:** Reduce worker count or batch size
```python
set_backend(BackendType.MULTIPROCESSING, num_workers=2)  # Fewer workers
```

---

For more examples, see:
- `examples/distributed_optimization.py` - Comprehensive examples
- `tests/test_distributed.py` - Test suite with usage patterns
