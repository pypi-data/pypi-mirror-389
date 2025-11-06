"""
Simple performance profiler for tracking optimization effectiveness.
"""

import threading
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, Optional

# Global profiling data
_profile_data: Dict[str, Dict[str, Any]] = defaultdict(
    lambda: {
        "call_count": 0,
        "total_time": 0.0,
        "avg_time": 0.0,
        "min_time": float("inf"),
        "max_time": 0.0,
    }
)
_profile_lock = threading.Lock()


@dataclass
class ProfilerConfig:
    """Configuration for the performance profiler."""

    enabled: bool = True
    detailed: bool = False
    output_format: str = "json"  # 'json', 'text', 'csv'


class PerformanceProfiler:
    """Simple performance profiler for functions."""

    def __init__(self, config: Optional[ProfilerConfig] = None):
        self.config = config or ProfilerConfig()

    def profile_function(self, func_name: str, execution_time: float) -> None:
        """Record profiling data for a function."""
        if not self.config.enabled:
            return

        with _profile_lock:
            data = _profile_data[func_name]
            data["call_count"] += 1
            data["total_time"] += execution_time
            data["avg_time"] = data["total_time"] / data["call_count"]
            data["min_time"] = min(data["min_time"], execution_time)
            data["max_time"] = max(data["max_time"], execution_time)


def get_performance_stats() -> Dict[str, Any]:
    """Get current performance statistics."""
    with _profile_lock:
        return dict(_profile_data)


def clear_performance_stats() -> None:
    """Clear all performance statistics."""
    with _profile_lock:
        _profile_data.clear()
