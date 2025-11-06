"""Advanced Performance Profiling

Comprehensive profiling system with:
- Chrome tracing format export
- Flamegraph data collection
- Timeline visualization data
- Hierarchical call tracking
- Event-based profiling
"""

import json
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import logging

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Profiling event types for Chrome tracing."""
    DURATION = "X"          # Complete event (duration)
    INSTANT = "i"           # Instant event
    COUNTER = "C"           # Counter event
    ASYNC_START = "b"       # Async event start
    ASYNC_END = "e"         # Async event end
    METADATA = "M"          # Metadata event


@dataclass
class ProfilingEvent:
    """Single profiling event."""
    name: str
    category: str
    event_type: EventType
    timestamp: float
    duration: Optional[float] = None
    tid: int = 0  # Thread ID
    pid: int = 0  # Process ID
    args: Dict[str, Any] = field(default_factory=dict)
    
    def to_chrome_trace(self) -> Dict[str, Any]:
        """Convert to Chrome tracing format."""
        event = {
            "name": self.name,
            "cat": self.category,
            "ph": self.event_type.value,
            "ts": int(self.timestamp * 1_000_000),  # Convert to microseconds
            "tid": self.tid,
            "pid": self.pid,
        }
        
        if self.duration is not None:
            event["dur"] = int(self.duration * 1_000_000)
        
        if self.args:
            event["args"] = self.args
        
        return event


class AdvancedProfiler:
    """Advanced profiling system with multiple export formats.
    
    Features:
    - Chrome tracing format export (chrome://tracing)
    - Flamegraph data collection
    - Timeline visualization
    - Hierarchical call stacks
    - Thread-aware profiling
    - Minimal overhead
    """
    
    def __init__(self, enabled: bool = True):
        """Initialize advanced profiler.
        
        Args:
            enabled: Whether profiling is enabled
        """
        self.enabled = enabled
        self.events: List[ProfilingEvent] = []
        self.call_stack: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        self.lock = threading.RLock()
        self.start_time = time.perf_counter()
        
        # Statistics
        self.stats = {
            "total_events": 0,
            "categories": set(),
            "threads": set(),
        }
    
    def record_event(
        self,
        name: str,
        category: str,
        event_type: EventType = EventType.INSTANT,
        duration: Optional[float] = None,
        **kwargs
    ):
        """Record a profiling event.
        
        Args:
            name: Event name
            category: Event category (e.g., "optimization", "jit", "specialization")
            event_type: Type of event
            duration: Duration in seconds (for DURATION events)
            **kwargs: Additional arguments to store
        """
        if not self.enabled:
            return
        
        with self.lock:
            timestamp = time.perf_counter() - self.start_time
            tid = threading.get_ident()
            
            event = ProfilingEvent(
                name=name,
                category=category,
                event_type=event_type,
                timestamp=timestamp,
                duration=duration,
                tid=tid,
                pid=0,
                args=kwargs,
            )
            
            self.events.append(event)
            self.stats["total_events"] += 1
            self.stats["categories"].add(category)
            self.stats["threads"].add(tid)
    
    def start_span(self, name: str, category: str, **kwargs):
        """Start a timed span.
        
        Args:
            name: Span name
            category: Span category
            **kwargs: Additional metadata
        
        Returns:
            SpanContext for use with context manager
        """
        return SpanContext(self, name, category, kwargs)
    
    def record_function_call(
        self,
        func_name: str,
        duration: float,
        category: str = "function",
        **kwargs
    ):
        """Record a function call with duration.
        
        Args:
            func_name: Function name
            duration: Execution duration in seconds
            category: Category for grouping
            **kwargs: Additional metadata
        """
        self.record_event(
            name=func_name,
            category=category,
            event_type=EventType.DURATION,
            duration=duration,
            **kwargs
        )
    
    def record_instant(self, name: str, category: str = "instant", **kwargs):
        """Record an instant event (no duration).
        
        Args:
            name: Event name
            category: Event category
            **kwargs: Additional metadata
        """
        self.record_event(
            name=name,
            category=category,
            event_type=EventType.INSTANT,
            **kwargs
        )
    
    def record_counter(self, name: str, value: float, category: str = "counter"):
        """Record a counter value.
        
        Args:
            name: Counter name
            value: Counter value
            category: Category
        """
        self.record_event(
            name=name,
            category=category,
            event_type=EventType.COUNTER,
            value=value
        )
    
    def export_chrome_trace(self, output_path: Path):
        """Export profiling data to Chrome tracing format.
        
        Args:
            output_path: Path to output JSON file
        
        The generated file can be viewed in:
        - chrome://tracing
        - edge://tracing
        - https://ui.perfetto.dev
        """
        with self.lock:
            trace_events = [event.to_chrome_trace() for event in self.events]
            
            # Add metadata
            trace_events.insert(0, {
                "name": "process_name",
                "ph": "M",
                "pid": 0,
                "args": {"name": "Python Optimizer"}
            })
            
            trace_data = {
                "traceEvents": trace_events,
                "displayTimeUnit": "ms",
                "otherData": {
                    "total_events": self.stats["total_events"],
                    "categories": list(self.stats["categories"]),
                    "threads": len(self.stats["threads"]),
                }
            }
            
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, "w") as f:
                json.dump(trace_data, f, indent=2)
            
            logger.info(f"Exported Chrome trace to {output_path}")
            logger.info(f"Open in chrome://tracing or https://ui.perfetto.dev")
    
    def export_flamegraph_data(self, output_path: Path):
        """Export data suitable for flamegraph generation.
        
        Args:
            output_path: Path to output file
        
        Format: Brendan Gregg's flamegraph format
        Each line: stack1;stack2;stack3 count
        """
        with self.lock:
            # Build call stacks from duration events
            stacks = defaultdict(int)
            
            # Sort events by timestamp and thread
            duration_events = [
                e for e in self.events
                if e.event_type == EventType.DURATION and e.duration
            ]
            duration_events.sort(key=lambda e: (e.tid, e.timestamp))
            
            # Build stacks per thread
            thread_stacks: Dict[int, List[str]] = defaultdict(list)
            thread_times: Dict[int, float] = {}
            
            for event in duration_events:
                tid = event.tid
                start_time = event.timestamp
                end_time = start_time + event.duration
                
                # Clean up expired stack frames
                if tid in thread_times:
                    while (thread_stacks[tid] and 
                           thread_times[tid] < start_time):
                        thread_stacks[tid].pop()
                        if thread_stacks[tid]:
                            # Update to parent's end time (approximation)
                            thread_times[tid] = start_time
                
                # Add current frame
                thread_stacks[tid].append(event.name)
                thread_times[tid] = end_time
                
                # Record stack
                stack_key = ";".join(thread_stacks[tid])
                stacks[stack_key] += int(event.duration * 1000)  # milliseconds
            
            # Write flamegraph data
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, "w") as f:
                for stack, count in sorted(stacks.items()):
                    f.write(f"{stack} {count}\n")
            
            logger.info(f"Exported flamegraph data to {output_path}")
            logger.info(f"Generate SVG: flamegraph.pl {output_path} > flamegraph.svg")
    
    def export_timeline_data(self, output_path: Path):
        """Export timeline visualization data.
        
        Args:
            output_path: Path to output JSON file
        
        Format: Custom JSON format for timeline visualization
        """
        with self.lock:
            timeline_data = {
                "start_time": self.start_time,
                "duration": (time.perf_counter() - self.start_time),
                "threads": {},
            }
            
            # Group events by thread
            for event in self.events:
                tid = str(event.tid)
                if tid not in timeline_data["threads"]:
                    timeline_data["threads"][tid] = {
                        "events": [],
                        "name": f"Thread-{tid}",
                    }
                
                timeline_data["threads"][tid]["events"].append({
                    "name": event.name,
                    "category": event.category,
                    "type": event.event_type.name,
                    "timestamp": event.timestamp,
                    "duration": event.duration,
                    "args": event.args,
                })
            
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, "w") as f:
                json.dump(timeline_data, f, indent=2)
            
            logger.info(f"Exported timeline data to {output_path}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get profiling statistics.
        
        Returns:
            Dictionary with statistics
        """
        with self.lock:
            # Calculate category breakdown
            category_counts = defaultdict(int)
            category_times = defaultdict(float)
            
            for event in self.events:
                category_counts[event.category] += 1
                if event.duration:
                    category_times[event.category] += event.duration
            
            return {
                "total_events": self.stats["total_events"],
                "categories": list(self.stats["categories"]),
                "threads": len(self.stats["threads"]),
                "category_counts": dict(category_counts),
                "category_times": dict(category_times),
                "total_duration": time.perf_counter() - self.start_time,
            }
    
    def clear(self):
        """Clear all profiling data."""
        with self.lock:
            self.events.clear()
            self.call_stack.clear()
            self.stats = {
                "total_events": 0,
                "categories": set(),
                "threads": set(),
            }
            self.start_time = time.perf_counter()
    
    def print_summary(self):
        """Print a summary of profiling data."""
        stats = self.get_stats()
        
        print("\n" + "=" * 60)
        print("Advanced Profiler Summary")
        print("=" * 60)
        print(f"Total Events: {stats['total_events']}")
        print(f"Threads: {stats['threads']}")
        print(f"Duration: {stats['total_duration']:.3f}s")
        print(f"\nCategories: {', '.join(stats['categories'])}")
        print("\nCategory Breakdown:")
        
        for category in stats['categories']:
            count = stats['category_counts'].get(category, 0)
            time_spent = stats['category_times'].get(category, 0)
            print(f"  {category:20s}: {count:6d} events, {time_spent:.3f}s")
        print("=" * 60 + "\n")


class SpanContext:
    """Context manager for profiling spans."""
    
    def __init__(
        self,
        profiler: AdvancedProfiler,
        name: str,
        category: str,
        args: Dict[str, Any]
    ):
        self.profiler = profiler
        self.name = name
        self.category = category
        self.args = args
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.perf_counter() - self.start_time
        self.profiler.record_function_call(
            self.name,
            duration,
            self.category,
            **self.args
        )
        return False


# Global profiler instance
_global_profiler: Optional[AdvancedProfiler] = None


def get_profiler() -> AdvancedProfiler:
    """Get global profiler instance.
    
    Returns:
        Global AdvancedProfiler instance
    """
    global _global_profiler
    
    if _global_profiler is None:
        _global_profiler = AdvancedProfiler()
    
    return _global_profiler


def profile_function(category: str = "function"):
    """Decorator to profile a function.
    
    Args:
        category: Category for grouping
    
    Example:
        @profile_function(category="optimization")
        def my_function():
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            profiler = get_profiler()
            with profiler.start_span(func.__name__, category):
                return func(*args, **kwargs)
        return wrapper
    return decorator
