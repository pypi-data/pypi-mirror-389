# Specialization Cache System

The Python Optimizer's specialization cache system provides efficient management of multiple specialized versions of functions with intelligent memory management, adaptive eviction policies, and comprehensive performance monitoring.

## Overview

The specialization cache system is designed to:
- Store specialized versions of functions based on argument types and patterns
- Automatically manage memory usage with configurable limits
- Provide adaptive eviction policies that learn from usage patterns
- Support thread-safe concurrent access
- Offer detailed performance metrics and monitoring

## Architecture

### Core Components

#### 1. SpecializationCache
The main cache class that manages specialized function versions.

```python
from python_optimizer.specialization_cache import SpecializationCache, CacheConfiguration

# Create cache with custom configuration
config = CacheConfiguration(
    max_size=500,           # Maximum number of cached entries
    max_memory_mb=50,       # Maximum memory usage in MB
    eviction_policy=EvictionPolicy.ADAPTIVE,  # Adaptive eviction strategy
    ttl_seconds=3600,       # Time-to-live for entries (1 hour)
    enable_weak_references=True,  # Use weak references to prevent memory leaks
    stats_collection_enabled=True  # Collect performance statistics
)

cache = SpecializationCache(config)
```

#### 2. TypeHasher
Efficient type-based hashing system for generating cache keys.

```python
from python_optimizer.specialization_cache import TypeHasher

# Hash different types of values
hash_int = TypeHasher.hash_value(42)
hash_float = TypeHasher.hash_value(42.0)
hash_list = TypeHasher.hash_value([1, 2, 3])
hash_dict = TypeHasher.hash_value({"a": 1, "b": 2})

# Hashes are stable and type-aware
assert TypeHasher.hash_value([1, 2, 3]) == TypeHasher.hash_value([1, 2, 3])
assert TypeHasher.hash_value(42) != TypeHasher.hash_value(42.0)
```

#### 3. AdaptiveEvictionStrategy
Intelligent eviction strategy that adapts based on usage patterns.

```python
from python_optimizer.specialization_cache import EvictionPolicy

# Available eviction policies
policies = [
    EvictionPolicy.LRU,         # Least Recently Used
    EvictionPolicy.LFU,         # Least Frequently Used
    EvictionPolicy.TTL,         # Time To Live based
    EvictionPolicy.SIZE_BASED,  # Memory usage based
    EvictionPolicy.ADAPTIVE     # Adaptive (recommended)
]
```

## Configuration Options

### CacheConfiguration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_size` | int | 1000 | Maximum number of cached entries |
| `max_memory_mb` | int | 100 | Maximum memory usage in MB |
| `eviction_policy` | EvictionPolicy | ADAPTIVE | Cache eviction strategy |
| `ttl_seconds` | int | None | Time-to-live for entries (None = no expiration) |
| `min_access_count` | int | 2 | Minimum accesses before entry is considered for eviction |
| `enable_weak_references` | bool | True | Use weak references to prevent memory leaks |
| `enable_compression` | bool | False | Compress cached entries (future feature) |
| `stats_collection_enabled` | bool | True | Collect detailed performance statistics |

### Adaptive Thresholds

Configure the adaptive eviction strategy behavior:

```python
config = CacheConfiguration(
    adaptive_thresholds={
        'hit_rate_threshold': 0.7,    # Minimum hit rate to consider policy effective
        'age_weight': 0.3,            # Weight for entry age in eviction scoring
        'frequency_weight': 0.4,      # Weight for access frequency
        'size_weight': 0.3            # Weight for memory usage
    }
)
```

## Usage Examples

### Basic Usage

```python
from python_optimizer.specialization_cache import get_global_cache

# Get the global cache instance
cache = get_global_cache()

# Store a specialized function
def optimized_add(a, b):
    return a + b

key = cache.get_key("add", (1, 2), {})
entry = cache.put(key, optimized_add, (1, 2), {})

# Retrieve the specialized function
cached_entry = cache.get(key)
if cached_entry:
    specialized_func = cached_entry.get_specialized_func()
    result = specialized_func()
```

### Integration with Function Decorator

```python
from python_optimizer.specialization_cache import get_global_cache
import functools

def cached_specialization(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        cache = get_global_cache()
        key = cache.get_key(func.__name__, args, kwargs)
        
        # Try to get from cache
        entry = cache.get(key)
        if entry:
            specialized_func = entry.get_specialized_func()
            if specialized_func:
                entry.update_metrics(success=True)
                return specialized_func(*args, **kwargs)
        
        # Create new specialization
        result = func(*args, **kwargs)
        
        # Store in cache for future use
        cache.put(key, func, args, kwargs)
        
        return result
    
    return wrapper

# Usage
@cached_specialization
def compute_intensive_function(data, operation):
    # Function implementation
    return process_data(data, operation)
```

### Custom Cache Configuration

```python
from python_optimizer.specialization_cache import (
    configure_cache, CacheConfiguration, EvictionPolicy
)

# Configure global cache
config = CacheConfiguration(
    max_size=2000,
    max_memory_mb=200,
    eviction_policy=EvictionPolicy.ADAPTIVE,
    ttl_seconds=7200,  # 2 hours
    enable_weak_references=True,
    adaptive_thresholds={
        'hit_rate_threshold': 0.8,
        'age_weight': 0.2,
        'frequency_weight': 0.5,
        'size_weight': 0.3
    }
)

configure_cache(config)
```

## Performance Monitoring

### Cache Statistics

```python
from python_optimizer.specialization_cache import get_cache_stats

# Get comprehensive statistics
stats = get_cache_stats()

print(f"Cache hit rate: {stats['hit_rate']:.2%}")
print(f"Total entries: {stats['total_entries']}")
print(f"Memory usage: {stats['memory_usage_estimate']:.2f} MB")
print(f"Evictions: {stats['evictions']}")
print(f"Average entry age: {stats['avg_entry_age_hours']:.1f} hours")
```

### Entry-Level Metrics

```python
# Get detailed metrics for a specific entry
cache = get_global_cache()
entry = cache.get("some_key")

if entry:
    metrics = entry.metrics
    print(f"Access count: {metrics.access_count}")
    print(f"Hit rate: {metrics.success_rate:.2%}")
    print(f"Average execution time: {metrics.average_execution_time:.6f}s")
    print(f"Memory estimate: {metrics.memory_estimate} bytes")
    print(f"Last access: {metrics.last_access_time}")
```

## Advanced Features

### Weak References

Prevent memory leaks by automatically cleaning up entries when specialized functions are garbage collected:

```python
config = CacheConfiguration(enable_weak_references=True)
cache = SpecializationCache(config)

def create_specialized_function():
    def specialized():
        return "result"
    return specialized

# Function will be automatically removed from cache when garbage collected
func = create_specialized_function()
entry = cache.put("key", func, (), {})

del func  # Function is eligible for garbage collection
# Entry will be marked as invalid automatically
```

### Time-To-Live (TTL)

Automatically expire entries after a specified time:

```python
config = CacheConfiguration(ttl_seconds=3600)  # 1 hour TTL
cache = SpecializationCache(config)

# Entry will automatically expire after 1 hour
cache.put("temp_key", some_function, (), {})
```

### Memory Management

The cache automatically manages memory usage with intelligent eviction:

```python
# Cache will automatically evict entries when approaching memory limit
config = CacheConfiguration(
    max_memory_mb=100,
    eviction_policy=EvictionPolicy.SIZE_BASED
)
```

## Thread Safety

The specialization cache is fully thread-safe and supports concurrent access:

```python
import threading
from python_optimizer.specialization_cache import get_global_cache

def worker_thread(thread_id):
    cache = get_global_cache()
    
    for i in range(100):
        key = f"thread_{thread_id}_key_{i}"
        cache.put(key, lambda: i, (i,), {})
        entry = cache.get(key)
        # Safe concurrent access

# Start multiple threads
threads = []
for i in range(4):
    thread = threading.Thread(target=worker_thread, args=(i,))
    threads.append(thread)
    thread.start()

for thread in threads:
    thread.join()
```

## Best Practices

### 1. Choose Appropriate Cache Size

```python
# For development/testing
config = CacheConfiguration(max_size=100, max_memory_mb=10)

# For production applications
config = CacheConfiguration(max_size=5000, max_memory_mb=500)

# For memory-constrained environments
config = CacheConfiguration(max_size=50, max_memory_mb=5)
```

### 2. Monitor Cache Performance

```python
import time
from python_optimizer.specialization_cache import get_cache_stats

def monitor_cache_performance():
    stats = get_cache_stats()
    
    if stats['hit_rate'] < 0.7:
        print("Warning: Cache hit rate is low. Consider tuning configuration.")
    
    if stats['memory_usage_estimate'] > stats.get('max_memory_mb', 100) * 0.9:
        print("Warning: Cache memory usage is high.")
    
    if stats['evictions'] > stats['total_entries'] * 2:
        print("Warning: High eviction rate. Consider increasing cache size.")

# Run monitoring periodically
monitor_cache_performance()
```

### 3. Handle Cache Misses Gracefully

```python
def get_specialized_function(key, fallback_func, *args, **kwargs):
    cache = get_global_cache()
    entry = cache.get(key)
    
    if entry:
        specialized_func = entry.get_specialized_func()
        if specialized_func:
            return specialized_func
    
    # Cache miss - create new specialization
    return fallback_func
```

### 4. Use Appropriate Eviction Policies

```python
# For general use - adapts automatically
config = CacheConfiguration(eviction_policy=EvictionPolicy.ADAPTIVE)

# For temporal data - removes old entries first
config = CacheConfiguration(eviction_policy=EvictionPolicy.LRU)

# For memory-sensitive applications
config = CacheConfiguration(eviction_policy=EvictionPolicy.SIZE_BASED)

# For frequently accessed data
config = CacheConfiguration(eviction_policy=EvictionPolicy.LFU)
```

## API Reference

### Global Functions

```python
# Get global cache instance
cache = get_global_cache()

# Configure global cache
configure_cache(config)

# Clear all cached entries
clear_cache()

# Get cache statistics
stats = get_cache_stats()
```

### SpecializationCache Methods

```python
# Generate cache key
key = cache.get_key(func_name, args, kwargs)

# Store entry
entry = cache.put(key, specialized_func, args, kwargs)

# Retrieve entry
entry = cache.get(key)

# Remove entry
removed = cache.remove(key)

# Clear all entries
cache.clear()

# Get statistics
stats = cache.get_stats()

# Perform maintenance
cache.maintenance()
```

### Entry Methods

```python
# Check if entry is valid
is_valid = entry.is_valid()

# Get specialized function
func = entry.get_specialized_func()

# Update metrics
entry.update_metrics(execution_time=0.001, success=True)
```

## Troubleshooting

### Common Issues

1. **High Memory Usage**
   ```python
   # Reduce cache size or memory limit
   config = CacheConfiguration(max_size=100, max_memory_mb=10)
   configure_cache(config)
   ```

2. **Low Hit Rate**
   ```python
   # Check cache statistics to identify patterns
   stats = get_cache_stats()
   if stats['hit_rate'] < 0.5:
       # Consider increasing cache size or adjusting eviction policy
       pass
   ```

3. **Frequent Evictions**
   ```python
   # Increase cache limits or use more selective eviction
   config = CacheConfiguration(
       max_size=2000,
       eviction_policy=EvictionPolicy.LFU
   )
   ```

### Debug Information

Enable detailed logging:

```python
import logging
logging.getLogger('python_optimizer.specialization_cache').setLevel(logging.DEBUG)
```

Get detailed cache state:

```python
cache = get_global_cache()
stats = cache.get_stats()

print("Cache State:")
for key, value in stats.items():
    print(f"  {key}: {value}")
```

## Performance Considerations

- **Cache Key Generation**: O(n) where n is the number of arguments
- **Cache Lookup**: O(1) average case with hash table
- **Eviction**: O(n) where n is the number of cached entries
- **Memory Overhead**: ~200-500 bytes per cached entry
- **Thread Safety**: Minimal overhead with RLock

The specialization cache is designed for high-performance scenarios where function call overhead reduction is critical.
