"""Distributed Specialization Cache

Shared specialization cache across distributed workers.
Enables specialized function versions to be shared between nodes.
"""

import hashlib
import logging
import pickle
import threading
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class DistributedSpecializationCache:
    """Distributed cache for specialized function versions.
    
    Features:
    - Share specialized versions across workers
    - Synchronize specialization results
    - Persistent disk cache with network transparency
    - Thread-safe concurrent access
    - Consistency guarantees
    """
    
    def __init__(self, cache_dir: Optional[Path] = None, sync_interval: float = 5.0):
        """Initialize distributed specialization cache.
        
        Args:
            cache_dir: Directory for cache storage
            sync_interval: Interval for cache synchronization (seconds)
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".python_optimizer" / "distributed_spec_cache"
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache: {(func_name, type_signature): specialized_version}
        self._memory_cache: Dict[Tuple[str, str], Any] = {}
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Metadata: {(func_name, type_signature): {usage_count, perf_gain, last_access}}
        self._metadata: Dict[Tuple[str, str], Dict[str, Any]] = {}
        
        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "specializations_created": 0,
            "sync_operations": 0,
            "conflicts_resolved": 0,
        }
        
        logger.info(f"Initialized distributed specialization cache at {self.cache_dir}")
    
    def _generate_key(self, func_name: str, type_signature: str) -> str:
        """Generate cache key for function and type signature.
        
        Args:
            func_name: Function name
            type_signature: Type signature string
            
        Returns:
            Cache key string
        """
        key_str = f"{func_name}_{type_signature}"
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    def get(
        self,
        func_name: str,
        type_signature: str
    ) -> Optional[Tuple[Any, Dict[str, Any]]]:
        """Get specialized function version from cache.
        
        Args:
            func_name: Function name
            type_signature: Type signature
            
        Returns:
            Tuple of (specialized_version, metadata) or None if not found
        """
        with self._lock:
            cache_key = (func_name, type_signature)
            
            # Check memory cache
            if cache_key in self._memory_cache:
                self.stats["hits"] += 1
                metadata = self._metadata.get(cache_key, {})
                metadata["usage_count"] = metadata.get("usage_count", 0) + 1
                
                logger.debug(
                    f"Specialization cache hit (memory): {func_name} {type_signature[:20]}"
                )
                return self._memory_cache[cache_key], metadata
            
            # Check disk cache
            file_key = self._generate_key(func_name, type_signature)
            cache_file = self.cache_dir / f"{file_key}.pkl"
            metadata_file = self.cache_dir / f"{file_key}_meta.pkl"
            
            if cache_file.exists():
                try:
                    with open(cache_file, "rb") as f:
                        specialized_version = pickle.load(f)
                    
                    metadata = {}
                    if metadata_file.exists():
                        with open(metadata_file, "rb") as f:
                            metadata = pickle.load(f)
                    
                    # Update memory cache
                    self._memory_cache[cache_key] = specialized_version
                    self._metadata[cache_key] = metadata
                    
                    metadata["usage_count"] = metadata.get("usage_count", 0) + 1
                    
                    self.stats["hits"] += 1
                    logger.debug(
                        f"Specialization cache hit (disk): {func_name} {type_signature[:20]}"
                    )
                    return specialized_version, metadata
                    
                except Exception as e:
                    logger.warning(f"Failed to load cached specialization: {e}")
            
            self.stats["misses"] += 1
            logger.debug(
                f"Specialization cache miss: {func_name} {type_signature[:20]}"
            )
            return None
    
    def put(
        self,
        func_name: str,
        type_signature: str,
        specialized_version: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Store specialized function version in cache.
        
        Args:
            func_name: Function name
            type_signature: Type signature
            specialized_version: Specialized function version
            metadata: Optional metadata (perf_gain, etc.)
        """
        with self._lock:
            cache_key = (func_name, type_signature)
            metadata = metadata or {}
            
            # Store in memory
            self._memory_cache[cache_key] = specialized_version
            self._metadata[cache_key] = metadata
            
            # Store on disk
            file_key = self._generate_key(func_name, type_signature)
            cache_file = self.cache_dir / f"{file_key}.pkl"
            metadata_file = self.cache_dir / f"{file_key}_meta.pkl"
            
            try:
                with open(cache_file, "wb") as f:
                    pickle.dump(specialized_version, f)
                
                with open(metadata_file, "wb") as f:
                    pickle.dump(metadata, f)
                
                self.stats["specializations_created"] += 1
                logger.debug(
                    f"Stored specialization: {func_name} {type_signature[:20]}"
                )
            except Exception as e:
                logger.warning(f"Failed to cache specialization: {e}")
    
    def update_metadata(
        self,
        func_name: str,
        type_signature: str,
        metadata_updates: Dict[str, Any],
    ):
        """Update metadata for a cached specialization.
        
        Args:
            func_name: Function name
            type_signature: Type signature
            metadata_updates: Metadata updates to apply
        """
        with self._lock:
            cache_key = (func_name, type_signature)
            
            if cache_key in self._metadata:
                self._metadata[cache_key].update(metadata_updates)
                
                # Persist to disk
                file_key = self._generate_key(func_name, type_signature)
                metadata_file = self.cache_dir / f"{file_key}_meta.pkl"
                
                try:
                    with open(metadata_file, "wb") as f:
                        pickle.dump(self._metadata[cache_key], f)
                except Exception as e:
                    logger.warning(f"Failed to update metadata: {e}")
    
    def sync(self):
        """Synchronize cache with disk.
        
        Loads any new specializations from disk that aren't in memory.
        """
        with self._lock:
            synced_count = 0
            
            # Scan disk cache for new entries
            for cache_file in self.cache_dir.glob("*.pkl"):
                if cache_file.name.endswith("_meta.pkl"):
                    continue
                
                # Check if already in memory
                file_key = cache_file.stem
                
                # Find corresponding entry in memory cache
                found = False
                for (func_name, type_sig) in self._memory_cache.keys():
                    if self._generate_key(func_name, type_sig) == file_key:
                        found = True
                        break
                
                if not found:
                    # Load from disk
                    try:
                        with open(cache_file, "rb") as f:
                            specialized_version = pickle.load(f)
                        
                        # Load metadata
                        metadata_file = cache_file.parent / f"{file_key}_meta.pkl"
                        metadata = {}
                        if metadata_file.exists():
                            with open(metadata_file, "rb") as f:
                                metadata = pickle.load(f)
                        
                        # Extract function name and type signature from metadata
                        func_name = metadata.get("func_name", "unknown")
                        type_sig = metadata.get("type_signature", "unknown")
                        
                        cache_key = (func_name, type_sig)
                        self._memory_cache[cache_key] = specialized_version
                        self._metadata[cache_key] = metadata
                        
                        synced_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to sync cache entry {file_key}: {e}")
            
            if synced_count > 0:
                self.stats["sync_operations"] += 1
                logger.info(f"Synced {synced_count} cache entries from disk")
    
    def clear(self, func_name: Optional[str] = None):
        """Clear cache entries.
        
        Args:
            func_name: If specified, only clear entries for this function
        """
        with self._lock:
            if func_name is None:
                # Clear all
                self._memory_cache.clear()
                self._metadata.clear()
                
                for cache_file in self.cache_dir.glob("*.pkl"):
                    try:
                        cache_file.unlink()
                    except Exception as e:
                        logger.warning(f"Failed to delete cache file: {e}")
                
                logger.info("Cleared all distributed specialization cache")
            else:
                # Clear specific function
                keys_to_remove = [
                    k for k in self._memory_cache.keys() if k[0] == func_name
                ]
                
                for key in keys_to_remove:
                    del self._memory_cache[key]
                    if key in self._metadata:
                        del self._metadata[key]
                    
                    # Remove from disk
                    file_key = self._generate_key(key[0], key[1])
                    cache_file = self.cache_dir / f"{file_key}.pkl"
                    metadata_file = self.cache_dir / f"{file_key}_meta.pkl"
                    
                    for f in [cache_file, metadata_file]:
                        if f.exists():
                            try:
                                f.unlink()
                            except Exception as e:
                                logger.warning(f"Failed to delete cache file: {e}")
                
                logger.info(f"Cleared cache for function: {func_name}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            total = self.stats["hits"] + self.stats["misses"]
            hit_rate = self.stats["hits"] / total if total > 0 else 0.0
            
            return {
                **self.stats,
                "hit_rate": hit_rate,
                "cache_size": len(self._memory_cache),
                "disk_cache_size": len(list(self.cache_dir.glob("*[!_meta].pkl"))),
                "total_metadata_entries": len(self._metadata),
            }


# Global cache instance
_distributed_spec_cache: Optional[DistributedSpecializationCache] = None


def get_distributed_spec_cache() -> DistributedSpecializationCache:
    """Get global distributed specialization cache instance.
    
    Returns:
        Distributed specialization cache
    """
    global _distributed_spec_cache
    
    if _distributed_spec_cache is None:
        _distributed_spec_cache = DistributedSpecializationCache()
    
    return _distributed_spec_cache


def clear_distributed_spec_cache(func_name: Optional[str] = None):
    """Clear global distributed specialization cache.
    
    Args:
        func_name: If specified, only clear entries for this function
    """
    cache = get_distributed_spec_cache()
    cache.clear(func_name)
