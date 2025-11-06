"""
Specialization Cache and Management

This module manages cached specialized function versions, handles cache
invalidation, and provides persistence for specialized optimizations.
"""

import hashlib
import os
import pickle
import threading
import time
import weakref
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union


@dataclass
class CacheEntry:
    """Represents a cached specialized function version."""

    specialized_func: Callable
    param_name: str
    param_type: type
    usage_pattern: Dict[str, Any]
    performance_gain: float
    creation_time: float
    access_count: int = 0
    last_access_time: float = 0.0
    compilation_time: float = 0.0
    cache_key: str = ""

    def __post_init__(self):
        if not self.cache_key:
            self.cache_key = self._generate_cache_key()
        if not self.last_access_time:
            self.last_access_time = self.creation_time

    def _generate_cache_key(self) -> str:
        """Generate unique cache key for this specialization."""
        key_data = f"{self.param_name}:{self.param_type.__name__}:{hash(str(self.usage_pattern))}"
        return hashlib.md5(key_data.encode()).hexdigest()[:16]

    def record_access(self):
        """Record that this cached entry was accessed."""
        self.access_count += 1
        self.last_access_time = time.time()

    def get_cache_score(self) -> float:
        """Calculate cache score for eviction decisions (higher = keep longer)."""
        age_hours = (time.time() - self.creation_time) / 3600
        recency_hours = (time.time() - self.last_access_time) / 3600

        # Factors: performance gain, access frequency, recency
        score = (
            self.performance_gain * 0.4  # Performance benefit
            + min(self.access_count / 10, 1.0) * 0.3  # Access frequency (capped)
            + max(0, 1.0 - recency_hours / 24) * 0.2  # Recency bonus (24 hour decay)
            + max(0, 1.0 - age_hours / (7 * 24)) * 0.1  # Age penalty (1 week decay)
        )
        return score


class SpecializationCache:
    """Manages caching of specialized function versions."""

    def __init__(self, max_size: int = 1000, enable_persistence: bool = True):
        self.max_size = max_size
        self.enable_persistence = enable_persistence

        # Main cache storage
        self._cache: OrderedDict[str, Dict[str, CacheEntry]] = OrderedDict()
        self._function_keys: Dict[str, Set[str]] = defaultdict(
            set
        )  # func_name -> cache_keys

        # Cache statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.creation_time = time.time()

        # Thread safety
        self._lock = threading.RLock()

        # Persistence settings
        self.cache_dir = os.path.expanduser("~/.python_optimizer/specialization_cache")
        if self.enable_persistence:
            os.makedirs(self.cache_dir, exist_ok=True)
            self._load_persistent_cache()

        # Performance tracking
        self._performance_stats: Dict[str, List[float]] = defaultdict(list)

        # Cleanup thread for cache maintenance
        self._cleanup_thread = threading.Thread(
            target=self._periodic_cleanup, daemon=True
        )
        self._cleanup_thread.start()

    def get(
        self,
        func_name: str,
        param_types: Tuple[type, ...],
        usage_patterns: Dict[str, Any],
    ) -> Optional[CacheEntry]:
        """Get a cached specialized version if available."""
        with self._lock:
            cache_key = self._generate_lookup_key(
                func_name, param_types, usage_patterns
            )

            if func_name in self._cache and cache_key in self._cache[func_name]:
                entry = self._cache[func_name][cache_key]
                entry.record_access()

                # Move to end (LRU)
                self._cache.move_to_end(func_name)

                self.hits += 1
                return entry

            self.misses += 1
            return None

    def put(self, func_name: str, entry: CacheEntry) -> bool:
        """Store a specialized function in the cache."""
        with self._lock:
            # Ensure function entry exists
            if func_name not in self._cache:
                self._cache[func_name] = {}

            cache_key = entry.cache_key

            # Check if already exists
            if cache_key in self._cache[func_name]:
                # Update existing entry
                existing = self._cache[func_name][cache_key]
                existing.access_count += 1
                existing.last_access_time = time.time()
                return True

            # Check cache size and evict if necessary
            total_entries = sum(len(entries) for entries in self._cache.values())
            if total_entries >= self.max_size:
                self._evict_entries()

            # Store new entry
            self._cache[func_name][cache_key] = entry
            self._function_keys[func_name].add(cache_key)

            # Move to end (most recently added)
            self._cache.move_to_end(func_name)

            # Persist if enabled
            if self.enable_persistence:
                self._persist_entry(func_name, entry)

            return True

    def _generate_lookup_key(
        self,
        func_name: str,
        param_types: Union[Tuple[type, ...], Dict[str, type]],
        usage_patterns: Dict[str, Any],
    ) -> str:
        """Generate lookup key for cache retrieval."""
        # Handle both tuple and dict param_types formats
        if param_types:
            if isinstance(param_types, dict):
                # Dict format: {'arg_0': int, 'arg_1': str}
                if param_types:
                    primary_type = next(iter(param_types.values()))
                    key_data = (
                        f"primary:{primary_type.__name__}:{hash(str(usage_patterns))}"
                    )
                    return hashlib.md5(key_data.encode()).hexdigest()[:16]
            else:
                # Tuple format: (int, str)
                primary_type = param_types[0]
                key_data = (
                    f"primary:{primary_type.__name__}:{hash(str(usage_patterns))}"
                )
                return hashlib.md5(key_data.encode()).hexdigest()[:16]
        return ""

    def _evict_entries(self, num_to_evict: Optional[int] = None):
        """Evict entries from cache based on cache scores."""
        if num_to_evict is None:
            num_to_evict = max(1, self.max_size // 10)  # Evict 10%

        # Collect all entries with scores
        all_entries = []
        for func_name, entries in self._cache.items():
            for cache_key, entry in entries.items():
                all_entries.append(
                    (func_name, cache_key, entry, entry.get_cache_score())
                )

        # Sort by score (lowest first = evict first)
        all_entries.sort(key=lambda x: x[3])

        # Evict lowest scoring entries
        evicted = 0
        for func_name, cache_key, entry, score in all_entries:
            if evicted >= num_to_evict:
                break

            # Remove from cache
            if func_name in self._cache and cache_key in self._cache[func_name]:
                del self._cache[func_name][cache_key]
                self._function_keys[func_name].discard(cache_key)

                # Remove function entry if empty
                if not self._cache[func_name]:
                    del self._cache[func_name]
                    del self._function_keys[func_name]

                evicted += 1
                self.evictions += 1

    def invalidate_function(self, func_name: str):
        """Invalidate all cached versions for a function."""
        with self._lock:
            if func_name in self._cache:
                num_removed = len(self._cache[func_name])
                del self._cache[func_name]
                del self._function_keys[func_name]

                # Remove persistent cache files
                if self.enable_persistence:
                    self._remove_persistent_function(func_name)

                return num_removed
            return 0

    def clear(self):
        """Clear all cached entries."""
        with self._lock:
            self._cache.clear()
            self._function_keys.clear()
            self.hits = 0
            self.misses = 0
            self.evictions = 0

            if self.enable_persistence:
                self._clear_persistent_cache()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_entries = sum(len(entries) for entries in self._cache.values())
            hit_rate = (
                self.hits / (self.hits + self.misses)
                if (self.hits + self.misses) > 0
                else 0
            )

            return {
                "total_entries": total_entries,
                "functions_cached": len(self._cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "evictions": self.evictions,
                "hit_rate": hit_rate,
                "cache_age_hours": (time.time() - self.creation_time) / 3600,
                "memory_usage_estimate": total_entries * 1024,  # Rough estimate
            }

    def get_function_stats(self, func_name: str) -> Dict[str, Any]:
        """Get statistics for a specific function."""
        with self._lock:
            if func_name not in self._cache:
                return {}

            entries = self._cache[func_name]
            total_accesses = sum(entry.access_count for entry in entries.values())
            avg_gain = sum(entry.performance_gain for entry in entries.values()) / len(
                entries
            )

            return {
                "specializations": len(entries),
                "total_accesses": total_accesses,
                "avg_performance_gain": avg_gain,
                "cache_keys": list(entries.keys()),
            }

    def prune_old_entries(self, max_age_hours: float = 24 * 7):  # Default: 1 week
        """Remove entries older than specified age."""
        with self._lock:
            current_time = time.time()
            cutoff_time = current_time - (max_age_hours * 3600)

            removed_count = 0
            functions_to_remove = []

            for func_name, entries in self._cache.items():
                keys_to_remove = []

                for cache_key, entry in entries.items():
                    if entry.creation_time < cutoff_time:
                        keys_to_remove.append(cache_key)

                for key in keys_to_remove:
                    del entries[key]
                    self._function_keys[func_name].discard(key)
                    removed_count += 1

                if not entries:
                    functions_to_remove.append(func_name)

            # Remove empty function entries
            for func_name in functions_to_remove:
                del self._cache[func_name]
                if func_name in self._function_keys:
                    del self._function_keys[func_name]

            return removed_count

    def _periodic_cleanup(self):
        """Periodic maintenance task running in background thread."""
        while True:
            time.sleep(3600)  # Run every hour
            try:
                # Prune old entries
                self.prune_old_entries()

                # Compact cache if too large
                total_entries = sum(len(entries) for entries in self._cache.values())
                if total_entries > self.max_size * 0.9:  # 90% full
                    self._evict_entries(self.max_size // 20)  # Evict 5%

            except Exception:
                # Ignore cleanup errors to avoid disrupting main thread
                pass

    # Persistence methods
    def _persist_entry(self, func_name: str, entry: CacheEntry):
        """Persist a cache entry to disk."""
        try:
            func_cache_dir = os.path.join(self.cache_dir, func_name)
            os.makedirs(func_cache_dir, exist_ok=True)

            cache_file = os.path.join(func_cache_dir, f"{entry.cache_key}.pkl")

            # Don't persist the actual function, just metadata
            entry_data = {
                "param_name": entry.param_name,
                "param_type": entry.param_type,
                "usage_pattern": entry.usage_pattern,
                "performance_gain": entry.performance_gain,
                "creation_time": entry.creation_time,
                "cache_key": entry.cache_key,
                # Note: specialized_func is not persisted as it's not serializable
            }

            with open(cache_file, "wb") as f:
                pickle.dump(entry_data, f)

        except Exception:
            # Persistence failures shouldn't break functionality
            pass

    def _load_persistent_cache(self):
        """Load persistent cache from disk."""
        try:
            if not os.path.exists(self.cache_dir):
                return

            for func_name in os.listdir(self.cache_dir):
                func_path = os.path.join(self.cache_dir, func_name)
                if not os.path.isdir(func_path):
                    continue

                for cache_file in os.listdir(func_path):
                    if not cache_file.endswith(".pkl"):
                        continue

                    try:
                        cache_path = os.path.join(func_path, cache_file)
                        with open(cache_path, "rb") as f:
                            entry_data = pickle.load(f)

                        # Recreate cache entry (without the function)
                        # The function will be regenerated when needed

                    except Exception:
                        # Skip corrupted cache files
                        continue

        except Exception:
            # If persistent cache loading fails, continue without it
            pass

    def _remove_persistent_function(self, func_name: str):
        """Remove persistent cache files for a function."""
        try:
            func_cache_dir = os.path.join(self.cache_dir, func_name)
            if os.path.exists(func_cache_dir):
                import shutil

                shutil.rmtree(func_cache_dir)
        except Exception:
            pass

    def _clear_persistent_cache(self):
        """Clear all persistent cache files."""
        try:
            if os.path.exists(self.cache_dir):
                import shutil

                shutil.rmtree(self.cache_dir)
                os.makedirs(self.cache_dir, exist_ok=True)
        except Exception:
            pass


# Global cache instance
_global_cache = None
_cache_lock = threading.Lock()


def get_global_cache() -> SpecializationCache:
    """Get the global specialization cache instance."""
    global _global_cache
    with _cache_lock:
        if _global_cache is None:
            _global_cache = SpecializationCache()
        return _global_cache


def clear_global_cache():
    """Clear the global cache."""
    global _global_cache
    with _cache_lock:
        if _global_cache is not None:
            _global_cache.clear()
            _global_cache = None


def get_cache_stats() -> Dict[str, Any]:
    """Get global cache statistics."""
    cache = get_global_cache()
    return cache.get_stats()
