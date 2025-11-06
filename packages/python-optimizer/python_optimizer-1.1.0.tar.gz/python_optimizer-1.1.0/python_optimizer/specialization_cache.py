"""
Advanced caching system for function specializations with intelligent memory management,
adaptive eviction policies, and performance monitoring.
"""

import functools
import gc
import hashlib
import logging
import pickle
import sys
import threading
import time
import weakref
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

logger = logging.getLogger(__name__)


class EvictionPolicy(Enum):
    """Cache eviction policies."""

    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL = "ttl"  # Time To Live
    ADAPTIVE = "adaptive"  # Adaptive policy based on usage patterns
    SIZE_BASED = "size_based"  # Based on memory usage estimation


class SpecializationType(Enum):
    """Types of specializations."""

    TYPE_BASED = "type_based"
    VALUE_BASED = "value_based"
    PATTERN_BASED = "pattern_based"
    HYBRID = "hybrid"


@dataclass
class SpecializationMetrics:
    """Metrics for a single specialization."""

    creation_time: float = field(default_factory=time.time)
    last_access_time: float = field(default_factory=time.time)
    access_count: int = 0
    hit_count: int = 0
    miss_count: int = 0
    total_execution_time: float = 0.0
    average_execution_time: float = 0.0
    memory_estimate: int = 0
    specialization_type: SpecializationType = SpecializationType.TYPE_BASED
    success_rate: float = 1.0

    def update_access(self, execution_time: float = 0.0, success: bool = True) -> None:
        """Update metrics on access."""
        self.last_access_time = time.time()
        self.access_count += 1

        if success:
            self.hit_count += 1
        else:
            self.miss_count += 1

        if execution_time > 0:
            self.total_execution_time += execution_time
            self.average_execution_time = self.total_execution_time / max(
                1, self.hit_count
            )

        # Update success rate
        total_attempts = self.hit_count + self.miss_count
        self.success_rate = self.hit_count / max(1, total_attempts)


@dataclass
class CacheConfiguration:
    """Configuration for the specialization cache."""

    max_size: int = 1000
    max_memory_mb: int = 100
    eviction_policy: EvictionPolicy = EvictionPolicy.ADAPTIVE
    ttl_seconds: Optional[int] = None
    min_access_count: int = 2
    enable_weak_references: bool = True
    enable_compression: bool = False
    stats_collection_enabled: bool = True
    adaptive_thresholds: Dict[str, float] = field(
        default_factory=lambda: {
            "hit_rate_threshold": 0.7,
            "age_weight": 0.3,
            "frequency_weight": 0.4,
            "size_weight": 0.3,
        }
    )


class TypeHasher:
    """Efficient type-based hashing for specialization keys."""

    _type_cache: Dict[type, str] = {}
    _lock = threading.Lock()

    @classmethod
    def hash_value(cls, value: Any) -> str:
        """Generate a hash for a value considering its type and content."""
        try:
            # Handle basic types efficiently
            value_type = type(value)

            with cls._lock:
                if value_type not in cls._type_cache:
                    cls._type_cache[value_type] = cls._generate_type_signature(
                        value_type
                    )

                type_sig = cls._type_cache[value_type]

            # Generate content hash based on type
            if value_type in (int, float, str, bool, type(None)):
                content_hash = str(hash(value))
            elif hasattr(value, "__hash__") and value.__hash__ is not None:
                try:
                    content_hash = str(hash(value))
                except TypeError:
                    content_hash = cls._hash_unhashable(value)
            else:
                content_hash = cls._hash_unhashable(value)

            return f"{type_sig}:{content_hash}"

        except Exception as e:
            logger.warning(f"Failed to hash value {type(value)}: {e}")
            return f"unhashable:{id(value)}"

    @classmethod
    def _generate_type_signature(cls, value_type: type) -> str:
        """Generate a signature for a type."""
        module = getattr(value_type, "__module__", "unknown")
        name = getattr(value_type, "__name__", str(value_type))
        return f"{module}.{name}"

    @classmethod
    def _hash_unhashable(cls, value: Any) -> str:
        """Hash unhashable objects by their structure."""
        try:
            if isinstance(value, (list, tuple)):
                return f"seq:{len(value)}:{hash(tuple(type(x) for x in value))}"
            elif isinstance(value, dict):
                return f"dict:{len(value)}:{hash(tuple(sorted(value.keys())))}"
            elif isinstance(value, set):
                return f"set:{len(value)}"
            elif hasattr(value, "__dict__"):
                return f"obj:{value.__class__.__name__}:{id(value)}"
            else:
                return f"unknown:{id(value)}"
        except Exception:
            return f"error:{id(value)}"


class SpecializationEntry:
    """Entry in the specialization cache."""

    def __init__(
        self,
        key: str,
        specialized_func: Callable,
        original_args: Tuple[Any, ...],
        original_kwargs: Dict[str, Any],
        config: CacheConfiguration,
    ):
        self.key = key
        self.specialized_func = specialized_func
        self.original_args = original_args
        self.original_kwargs = original_kwargs
        self.config = config
        self.metrics = SpecializationMetrics()
        self._compressed_data: Optional[bytes] = None

        # Estimate memory usage
        self._estimate_memory()

        # Create weak reference if enabled
        if config.enable_weak_references:
            self._weak_ref: Optional[weakref.ReferenceType[Callable[..., Any]]] = weakref.ref(specialized_func, self._cleanup)
        else:
            self._weak_ref = None

    def _estimate_memory(self) -> None:
        """Estimate memory usage of this entry."""
        try:
            size = sys.getsizeof(self)
            size += sys.getsizeof(self.key)
            size += sys.getsizeof(self.specialized_func) if self.specialized_func else 0
            size += sys.getsizeof(self.original_args)
            size += sys.getsizeof(self.original_kwargs)

            if self._compressed_data:
                size += sys.getsizeof(self._compressed_data)

            self.metrics.memory_estimate = size
        except Exception:
            self.metrics.memory_estimate = 1024  # Fallback estimate

    def _cleanup(self, ref: Any) -> None:
        """Cleanup callback for weak references."""
        logger.debug(f"Specialized function for key {self.key} was garbage collected")

    def is_valid(self) -> bool:
        """Check if the entry is still valid."""
        # Check TTL
        if (
            self.config.ttl_seconds
            and time.time() - self.metrics.creation_time > self.config.ttl_seconds
        ):
            return False

        # Check weak reference
        if self._weak_ref and self._weak_ref() is None:
            return False

        return True

    def get_specialized_func(self) -> Optional[Callable[..., Any]]:
        """Get the specialized function, handling weak references."""
        if self._weak_ref and self._weak_ref():
            return self._weak_ref()
        return self.specialized_func

    def update_metrics(self, execution_time: float = 0.0, success: bool = True) -> None:
        """Update metrics for this entry."""
        self.metrics.update_access(execution_time, success)


class AdaptiveEvictionStrategy:
    """Adaptive eviction strategy that learns from usage patterns."""

    def __init__(self, config: CacheConfiguration):
        self.config = config
        self.policy_performance: Dict[EvictionPolicy, float] = defaultdict(float)
        self.current_policy = EvictionPolicy.LRU
        self.policy_switch_count = 0
        self.last_policy_evaluation = time.time()

    def should_evict(
        self,
        entries: Dict[str, SpecializationEntry],
        current_memory_mb: float,
        current_size: int,
    ) -> List[str]:
        """Determine which entries should be evicted."""

        # Check if we need to evict
        memory_pressure = current_memory_mb > self.config.max_memory_mb
        size_pressure = current_size > self.config.max_size

        if not (memory_pressure or size_pressure):
            return []

        # Evaluate and potentially switch policy
        self._evaluate_policy_performance(entries)

        # Calculate how much to evict
        if memory_pressure:
            target_memory = self.config.max_memory_mb * 0.8  # Keep 20% buffer
            memory_to_free = current_memory_mb - target_memory
        else:
            memory_to_free = 0

        if size_pressure:
            target_size = int(self.config.max_size * 0.8)
            items_to_evict = current_size - target_size
        else:
            items_to_evict = 0

        # Select candidates based on current policy
        return self._select_eviction_candidates(entries, memory_to_free, items_to_evict)

    def _evaluate_policy_performance(self, entries: Dict[str, SpecializationEntry]) -> None:
        """Evaluate current policy performance and switch if needed."""
        now = time.time()

        # Only evaluate periodically
        if now - self.last_policy_evaluation < 60:  # 1 minute
            return

        self.last_policy_evaluation = now

        # Calculate current performance metrics
        total_hit_rate = self._calculate_hit_rate(entries)
        avg_access_time = self._calculate_avg_access_time(entries)

        # Simple performance score (can be enhanced)
        current_score = total_hit_rate * 0.7 + (1.0 - avg_access_time) * 0.3

        self.policy_performance[self.current_policy] = current_score

        # Consider switching policy if performance is poor
        if current_score < 0.6 and len(self.policy_performance) > 1:
            best_policy = max(self.policy_performance.items(), key=lambda x: x[1])[0]
            if best_policy != self.current_policy:
                logger.info(
                    f"Switching eviction policy from {self.current_policy} to {best_policy}"
                )
                self.current_policy = best_policy
                self.policy_switch_count += 1

    def _calculate_hit_rate(self, entries: Dict[str, SpecializationEntry]) -> float:
        """Calculate overall cache hit rate."""
        total_hits = sum(entry.metrics.hit_count for entry in entries.values())
        total_attempts = sum(
            entry.metrics.hit_count + entry.metrics.miss_count
            for entry in entries.values()
        )
        return total_hits / max(1, total_attempts)

    def _calculate_avg_access_time(
        self, entries: Dict[str, SpecializationEntry]
    ) -> float:
        """Calculate normalized average access recency."""
        if not entries:
            return 0.0

        now = time.time()
        ages = [now - entry.metrics.last_access_time for entry in entries.values()]
        max_age = max(ages) if ages else 1.0

        return sum(ages) / (len(ages) * max(max_age, 1.0))

    def _select_eviction_candidates(
        self,
        entries: Dict[str, SpecializationEntry],
        memory_to_free: float,
        items_to_evict: int,
    ) -> List[str]:
        """Select entries for eviction based on current policy."""

        if self.current_policy == EvictionPolicy.LRU:
            return self._lru_candidates(entries, items_to_evict)
        elif self.current_policy == EvictionPolicy.LFU:
            return self._lfu_candidates(entries, items_to_evict)
        elif self.current_policy == EvictionPolicy.SIZE_BASED:
            return self._size_based_candidates(entries, memory_to_free, items_to_evict)
        else:  # ADAPTIVE
            return self._adaptive_candidates(entries, memory_to_free, items_to_evict)

    def _lru_candidates(
        self, entries: Dict[str, SpecializationEntry], count: int
    ) -> List[str]:
        """Select LRU candidates."""
        sorted_entries = sorted(
            entries.items(), key=lambda x: x[1].metrics.last_access_time
        )
        return [key for key, _ in sorted_entries[:count]]

    def _lfu_candidates(
        self, entries: Dict[str, SpecializationEntry], count: int
    ) -> List[str]:
        """Select LFU candidates."""
        sorted_entries = sorted(
            entries.items(), key=lambda x: x[1].metrics.access_count
        )
        return [key for key, _ in sorted_entries[:count]]

    def _size_based_candidates(
        self,
        entries: Dict[str, SpecializationEntry],
        memory_to_free: float,
        items_to_evict: int,
    ) -> List[str]:
        """Select candidates based on memory usage."""
        # Sort by memory usage (descending) and access patterns
        sorted_entries = sorted(
            entries.items(),
            key=lambda x: (
                -x[1].metrics.memory_estimate,  # Larger first
                x[1].metrics.last_access_time,  # Then by LRU
            ),
        )

        candidates = []
        freed_memory = 0.0

        for key, entry in sorted_entries:
            if len(candidates) >= items_to_evict and freed_memory >= memory_to_free:
                break

            candidates.append(key)
            freed_memory += entry.metrics.memory_estimate / (
                1024 * 1024
            )  # Convert to MB

        return candidates

    def _adaptive_candidates(
        self,
        entries: Dict[str, SpecializationEntry],
        memory_to_free: float,
        items_to_evict: int,
    ) -> List[str]:
        """Select candidates using adaptive scoring."""
        now = time.time()
        thresholds = self.config.adaptive_thresholds

        scored_entries = []
        for key, entry in entries.items():
            # Calculate composite score (lower = better candidate for eviction)
            age_score = (now - entry.metrics.last_access_time) / 3600  # Hours
            freq_score = 1.0 / max(1, entry.metrics.access_count)
            size_score = entry.metrics.memory_estimate / (1024 * 1024)  # MB
            hit_rate_score = 1.0 - entry.metrics.success_rate

            composite_score = (
                age_score * thresholds["age_weight"]
                + freq_score * thresholds["frequency_weight"]
                + size_score * thresholds["size_weight"]
                + hit_rate_score * 0.2
            )

            scored_entries.append((key, composite_score))

        # Sort by score (higher score = better eviction candidate)
        scored_entries.sort(key=lambda x: x[1], reverse=True)

        return [
            key for key, _ in scored_entries[: max(items_to_evict, len(scored_entries))]
        ]


class SpecializationCache:
    """Advanced caching system for function specializations."""

    def __init__(self, config: Optional[CacheConfiguration] = None):
        self.config = config or CacheConfiguration()
        self._entries: Dict[str, SpecializationEntry] = {}
        self._lock = threading.RLock()
        self._eviction_strategy = AdaptiveEvictionStrategy(self.config)

        # Statistics
        self._stats = {
            "total_lookups": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "evictions": 0,
            "total_memory_mb": 0.0,
            "creation_time": time.time(),
        }

        # Background maintenance
        self._last_maintenance = time.time()
        self._maintenance_interval = 300  # 5 minutes

    def get_key(
        self, func_name: str, args: Tuple[Any, ...], kwargs: Dict[str, Any]
    ) -> str:
        """Generate cache key for function call."""
        try:
            # Hash function name
            key_parts = [func_name]

            # Hash positional arguments
            for arg in args:
                key_parts.append(TypeHasher.hash_value(arg))

            # Hash keyword arguments
            if kwargs:
                sorted_kwargs = sorted(kwargs.items())
                for k, v in sorted_kwargs:
                    key_parts.append(f"{k}={TypeHasher.hash_value(v)}")

            return "|".join(key_parts)

        except Exception as e:
            logger.warning(f"Failed to generate cache key: {e}")
            return f"fallback:{func_name}:{id(args)}:{id(kwargs)}"

    def get(self, key: str) -> Optional[SpecializationEntry]:
        """Get entry from cache."""
        with self._lock:
            self._stats["total_lookups"] += 1

            if key not in self._entries:
                self._stats["cache_misses"] += 1
                return None

            entry = self._entries[key]

            # Check if entry is still valid
            if not entry.is_valid():
                del self._entries[key]
                self._stats["cache_misses"] += 1
                return None

            self._stats["cache_hits"] += 1
            return entry

    def put(
        self,
        key: str,
        specialized_func: Callable[..., Any],
        original_args: Tuple[Any, ...],
        original_kwargs: Dict[str, Any],
    ) -> SpecializationEntry:
        """Put entry into cache."""
        with self._lock:
            # Create new entry
            entry = SpecializationEntry(
                key, specialized_func, original_args, original_kwargs, self.config
            )

            # Check if we need eviction
            self._maybe_evict()

            # Store entry
            self._entries[key] = entry
            self._update_memory_stats()

            return entry

    def remove(self, key: str) -> bool:
        """Remove entry from cache."""
        with self._lock:
            if key in self._entries:
                del self._entries[key]
                self._update_memory_stats()
                return True
            return False

    def clear(self) -> None:
        """Clear all entries."""
        with self._lock:
            self._entries.clear()
            self._update_memory_stats()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            current_stats = self._stats.copy()

            # Calculate derived metrics
            total_lookups = current_stats["total_lookups"]
            if total_lookups > 0:
                current_stats["hit_rate"] = current_stats["cache_hits"] / total_lookups
                current_stats["miss_rate"] = (
                    current_stats["cache_misses"] / total_lookups
                )
            else:
                current_stats["hit_rate"] = 0.0
                current_stats["miss_rate"] = 0.0

            current_stats["total_entries"] = len(self._entries)
            current_stats["memory_usage_estimate"] = self._stats["total_memory_mb"]
            current_stats["uptime_hours"] = (
                time.time() - current_stats["creation_time"]
            ) / 3600

            # Entry-level statistics
            if self._entries:
                access_counts = [
                    entry.metrics.access_count for entry in self._entries.values()
                ]
                current_stats["avg_access_count"] = sum(access_counts) / len(
                    access_counts
                )
                current_stats["max_access_count"] = max(access_counts)
                current_stats["min_access_count"] = min(access_counts)

                ages = [
                    time.time() - entry.metrics.creation_time
                    for entry in self._entries.values()
                ]
                current_stats["avg_entry_age_hours"] = (sum(ages) / len(ages)) / 3600
                current_stats["oldest_entry_hours"] = max(ages) / 3600

            return current_stats

    def _maybe_evict(self) -> None:
        """Check if eviction is needed and perform it."""
        current_size = len(self._entries)
        current_memory_mb = sum(
            entry.metrics.memory_estimate for entry in self._entries.values()
        ) / (1024 * 1024)

        candidates = self._eviction_strategy.should_evict(
            self._entries, current_memory_mb, current_size
        )

        if candidates:
            for key in candidates:
                if key in self._entries:
                    del self._entries[key]
                    self._stats["evictions"] += 1

            logger.debug(f"Evicted {len(candidates)} entries from specialization cache")

    def _update_memory_stats(self) -> None:
        """Update memory usage statistics."""
        total_memory = sum(
            entry.metrics.memory_estimate for entry in self._entries.values()
        )
        self._stats["total_memory_mb"] = total_memory / (1024 * 1024)

    def maintenance(self) -> None:
        """Perform periodic maintenance."""
        now = time.time()

        if now - self._last_maintenance < self._maintenance_interval:
            return

        with self._lock:
            self._last_maintenance = now

            # Remove invalid entries
            invalid_keys = []
            for key, entry in self._entries.items():
                if not entry.is_valid():
                    invalid_keys.append(key)

            for key in invalid_keys:
                del self._entries[key]

            if invalid_keys:
                logger.debug(
                    f"Removed {len(invalid_keys)} invalid entries during maintenance"
                )

            # Trigger garbage collection if memory usage is high
            if self._stats["total_memory_mb"] > self.config.max_memory_mb * 0.9:
                gc.collect()

            # Update memory stats
            self._update_memory_stats()


# Global cache instance
_global_cache: Optional[SpecializationCache] = None
_cache_lock = threading.Lock()


def get_global_cache() -> SpecializationCache:
    """Get or create the global specialization cache."""
    global _global_cache

    if _global_cache is None:
        with _cache_lock:
            if _global_cache is None:
                _global_cache = SpecializationCache()

    return _global_cache


def configure_cache(config: CacheConfiguration) -> None:
    """Configure the global cache."""
    global _global_cache

    with _cache_lock:
        _global_cache = SpecializationCache(config)


def clear_cache() -> None:
    """Clear the global cache."""
    cache = get_global_cache()
    cache.clear()


def get_cache_stats() -> Dict[str, Any]:
    """Get global cache statistics."""
    cache = get_global_cache()
    return cache.get_stats()
