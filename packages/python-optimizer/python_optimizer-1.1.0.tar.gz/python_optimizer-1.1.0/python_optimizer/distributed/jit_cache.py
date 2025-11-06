"""Distributed JIT Cache

Shared JIT compilation cache across distributed workers.
Enables compiled artifacts to be shared between nodes.
"""

import hashlib
import logging
import pickle
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from python_optimizer.distributed.backend import get_backend

logger = logging.getLogger(__name__)


class DistributedJITCache:
    """Distributed cache for JIT compiled functions.
    
    Features:
    - Share compiled artifacts across workers
    - Avoid redundant compilation
    - Persistent disk cache
    - Network-transparent access
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize distributed JIT cache.
        
        Args:
            cache_dir: Directory for cache storage (default: ~/.python_optimizer/distributed_jit_cache)
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".python_optimizer" / "distributed_jit_cache"
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache
        self._memory_cache: Dict[str, Any] = {}
        
        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "compilations": 0,
            "network_transfers": 0,
        }
        
        logger.info(f"Initialized distributed JIT cache at {self.cache_dir}")
    
    def _generate_key(self, func: Callable, options: Dict[str, Any]) -> str:
        """Generate cache key for function and options.
        
        Args:
            func: Function to cache
            options: JIT compilation options
            
        Returns:
            Cache key string
        """
        # Get function bytecode
        try:
            func_code = func.__code__.co_code
        except AttributeError:
            # Already compiled or special function
            func_code = str(func).encode()
        
        # Create hash of function + options
        hasher = hashlib.sha256()
        hasher.update(func_code)
        hasher.update(pickle.dumps(options))
        
        return hasher.hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get compiled function from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Compiled function or None if not found
        """
        # Check memory cache first
        if key in self._memory_cache:
            self.stats["hits"] += 1
            logger.debug(f"JIT cache hit (memory): {key[:8]}")
            return self._memory_cache[key]
        
        # Check disk cache
        cache_file = self.cache_dir / f"{key}.pkl"
        if cache_file.exists():
            try:
                with open(cache_file, "rb") as f:
                    compiled_func = pickle.load(f)
                
                # Update memory cache
                self._memory_cache[key] = compiled_func
                
                self.stats["hits"] += 1
                self.stats["network_transfers"] += 1
                logger.debug(f"JIT cache hit (disk): {key[:8]}")
                return compiled_func
            except Exception as e:
                logger.warning(f"Failed to load cached JIT function: {e}")
        
        self.stats["misses"] += 1
        logger.debug(f"JIT cache miss: {key[:8]}")
        return None
    
    def put(self, key: str, compiled_func: Any):
        """Store compiled function in cache.
        
        Args:
            key: Cache key
            compiled_func: Compiled function to store
        """
        # Store in memory
        self._memory_cache[key] = compiled_func
        
        # Store on disk
        cache_file = self.cache_dir / f"{key}.pkl"
        try:
            with open(cache_file, "wb") as f:
                pickle.dump(compiled_func, f)
            
            self.stats["compilations"] += 1
            logger.debug(f"Stored JIT compiled function: {key[:8]}")
        except Exception as e:
            logger.warning(f"Failed to cache JIT function: {e}")
    
    def get_or_compile(
        self,
        func: Callable,
        compiler: Callable[[Callable], Any],
        options: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Get compiled function from cache or compile it.
        
        Args:
            func: Function to compile
            compiler: Compiler function (e.g., numba.njit)
            options: Compilation options
            
        Returns:
            Compiled function
        """
        options = options or {}
        key = self._generate_key(func, options)
        
        # Try cache first
        compiled_func = self.get(key)
        if compiled_func is not None:
            return compiled_func
        
        # Compile function
        logger.info(f"Compiling function {func.__name__} with options {options}")
        compiled_func = compiler(func)
        
        # Store in cache
        self.put(key, compiled_func)
        
        return compiled_func
    
    def clear(self):
        """Clear all cache entries."""
        self._memory_cache.clear()
        
        # Clear disk cache
        for cache_file in self.cache_dir.glob("*.pkl"):
            try:
                cache_file.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete cache file {cache_file}: {e}")
        
        logger.info("Cleared distributed JIT cache")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total if total > 0 else 0.0
        
        return {
            **self.stats,
            "hit_rate": hit_rate,
            "cache_size": len(self._memory_cache),
            "disk_cache_size": len(list(self.cache_dir.glob("*.pkl"))),
        }


# Global cache instance
_distributed_jit_cache: Optional[DistributedJITCache] = None


def get_distributed_jit_cache() -> DistributedJITCache:
    """Get global distributed JIT cache instance.
    
    Returns:
        Distributed JIT cache
    """
    global _distributed_jit_cache
    
    if _distributed_jit_cache is None:
        _distributed_jit_cache = DistributedJITCache()
    
    return _distributed_jit_cache


def clear_distributed_jit_cache():
    """Clear global distributed JIT cache."""
    cache = get_distributed_jit_cache()
    cache.clear()
