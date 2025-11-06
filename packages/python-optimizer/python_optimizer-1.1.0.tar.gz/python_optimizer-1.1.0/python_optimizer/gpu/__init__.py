"""GPU acceleration module for Python Optimizer.

This module provides CUDA/GPU acceleration capabilities using CuPy and Numba.
Automatically detects GPU availability and falls back to CPU when necessary.

Key Features:
- Automatic GPU detection and device management
- GPU-accelerated JIT compilation
- Smart CPU/GPU dispatch based on data size
- GPU memory management and caching
- Seamless fallback to CPU when GPU unavailable

Usage:
    from python_optimizer import optimize

    @optimize(gpu=True)
    def my_function(data):
        # Automatically runs on GPU if available
        return data ** 2
"""

from python_optimizer.gpu.device import (
    GPUDevice,
    get_gpu_device,
    get_gpu_info,
    is_gpu_available,
    set_gpu_device,
)
from python_optimizer.gpu.dispatcher import GPUDispatcher
from python_optimizer.gpu.kernels import GPUKernelLibrary
from python_optimizer.gpu.memory import (
    GPUMemoryManager,
    clear_gpu_cache,
    get_gpu_memory_info,
)

# Try to import GPU genetic optimizer
try:
    from python_optimizer.gpu.genetic import (
        GPUGeneticOptimizer,
        optimize_genetic_gpu,
    )

    GPU_GENETIC_AVAILABLE = True
except ImportError:
    GPU_GENETIC_AVAILABLE = False
    GPUGeneticOptimizer = None
    optimize_genetic_gpu = None

__all__ = [
    # Device management
    "is_gpu_available",
    "get_gpu_device",
    "get_gpu_info",
    "set_gpu_device",
    "GPUDevice",
    # Memory management
    "GPUMemoryManager",
    "get_gpu_memory_info",
    "clear_gpu_cache",
    # Dispatching
    "GPUDispatcher",
    # Kernels
    "GPUKernelLibrary",
    # GPU Optimizers
    "GPUGeneticOptimizer",
    "optimize_genetic_gpu",
    "GPU_GENETIC_AVAILABLE",
]
