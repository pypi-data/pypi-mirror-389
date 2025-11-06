"""GPU device detection and management.

Handles GPU device detection, selection, and information retrieval.
Supports CUDA devices via CuPy with automatic fallback.
"""

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Try to import CuPy (GPU support)
try:
    import cupy as cp

    CUPY_AVAILABLE = True
except ImportError:
    CUPY_AVAILABLE = False
    cp = None
    logger.debug("CuPy not available - GPU support disabled")

# Try to import Numba CUDA
try:
    from numba import cuda

    NUMBA_CUDA_AVAILABLE = cuda.is_available()
except (ImportError, Exception):
    NUMBA_CUDA_AVAILABLE = False
    cuda = None
    logger.debug("Numba CUDA not available")


@dataclass
class GPUDevice:
    """Information about a GPU device."""

    device_id: int
    name: str
    compute_capability: tuple
    total_memory: int  # bytes
    free_memory: int  # bytes
    is_available: bool
    backend: str  # 'cupy' or 'numba'

    @property
    def memory_gb(self) -> float:
        """Total memory in GB."""
        return self.total_memory / (1024**3)

    @property
    def free_memory_gb(self) -> float:
        """Free memory in GB."""
        return self.free_memory / (1024**3)

    @property
    def utilization_percent(self) -> float:
        """Memory utilization percentage."""
        if self.total_memory == 0:
            return 0.0
        return ((self.total_memory - self.free_memory) / self.total_memory) * 100


class _GPUDeviceManager:
    """Singleton manager for GPU devices."""

    def __init__(self):
        self._current_device: Optional[int] = None
        self._device_cache: Dict[int, GPUDevice] = {}
        self._gpu_available: Optional[bool] = None

    def is_available(self) -> bool:
        """Check if GPU is available."""
        if self._gpu_available is not None:
            return self._gpu_available

        # Check environment variable override
        if os.environ.get("PYTHON_OPTIMIZER_NO_GPU", "0") == "1":
            self._gpu_available = False
            logger.info("GPU disabled via PYTHON_OPTIMIZER_NO_GPU environment variable")
            return False

        # Check CuPy availability
        if CUPY_AVAILABLE:
            try:
                device_count = cp.cuda.runtime.getDeviceCount()
                self._gpu_available = device_count > 0
                if self._gpu_available:
                    logger.info(
                        f"GPU available: {device_count} CUDA device(s) detected via CuPy"
                    )
                return self._gpu_available
            except Exception as e:
                logger.debug(f"CuPy GPU detection failed: {e}")

        # Check Numba CUDA availability
        if NUMBA_CUDA_AVAILABLE:
            try:
                self._gpu_available = True
                logger.info("GPU available via Numba CUDA")
                return True
            except Exception as e:
                logger.debug(f"Numba CUDA detection failed: {e}")

        self._gpu_available = False
        logger.info("No GPU available - falling back to CPU")
        return False

    def get_device(self, device_id: Optional[int] = None) -> Optional[GPUDevice]:
        """Get GPU device information.

        Args:
            device_id: Device ID to query. If None, uses current device.

        Returns:
            GPUDevice object or None if not available.
        """
        if not self.is_available():
            return None

        if device_id is None:
            device_id = self._current_device or 0

        # Check cache
        if device_id in self._device_cache:
            return self._device_cache[device_id]

        # Query device
        device = self._query_device(device_id)
        if device:
            self._device_cache[device_id] = device
        return device

    def _query_device(self, device_id: int) -> Optional[GPUDevice]:
        """Query device information from GPU."""
        if CUPY_AVAILABLE:
            try:
                with cp.cuda.Device(device_id):
                    props = cp.cuda.runtime.getDeviceProperties(device_id)
                    meminfo = cp.cuda.runtime.memGetInfo()

                    return GPUDevice(
                        device_id=device_id,
                        name=props["name"].decode("utf-8"),
                        compute_capability=(props["major"], props["minor"]),
                        total_memory=props["totalGlobalMem"],
                        free_memory=meminfo[0],
                        is_available=True,
                        backend="cupy",
                    )
            except Exception as e:
                logger.error(f"Failed to query CuPy device {device_id}: {e}")

        if NUMBA_CUDA_AVAILABLE and cuda:
            try:
                device = cuda.gpus[device_id]
                # Numba provides limited info
                return GPUDevice(
                    device_id=device_id,
                    name=(
                        device.name.decode("utf-8")
                        if hasattr(device.name, "decode")
                        else str(device.name)
                    ),
                    compute_capability=device.compute_capability,
                    total_memory=0,  # Not easily available in Numba
                    free_memory=0,
                    is_available=True,
                    backend="numba",
                )
            except Exception as e:
                logger.error(f"Failed to query Numba CUDA device {device_id}: {e}")

        return None

    def set_device(self, device_id: int) -> bool:
        """Set current GPU device.

        Args:
            device_id: Device ID to set as current.

        Returns:
            True if successful, False otherwise.
        """
        if not self.is_available():
            return False

        try:
            if CUPY_AVAILABLE:
                cp.cuda.Device(device_id).use()
            if NUMBA_CUDA_AVAILABLE and cuda:
                cuda.select_device(device_id)

            self._current_device = device_id
            logger.info(f"Set GPU device to {device_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to set GPU device {device_id}: {e}")
            return False

    def get_info(self) -> Dict[str, Any]:
        """Get comprehensive GPU information.

        Returns:
            Dictionary with GPU information.
        """
        info = {
            "available": self.is_available(),
            "cupy_available": CUPY_AVAILABLE,
            "numba_cuda_available": NUMBA_CUDA_AVAILABLE,
            "current_device": self._current_device,
            "devices": [],
        }

        if not self.is_available():
            return info

        # Get all devices
        if CUPY_AVAILABLE:
            try:
                device_count = cp.cuda.runtime.getDeviceCount()
                for i in range(device_count):
                    device = self.get_device(i)
                    if device:
                        info["devices"].append(
                            {
                                "id": device.device_id,
                                "name": device.name,
                                "compute_capability": device.compute_capability,
                                "memory_gb": round(device.memory_gb, 2),
                                "free_memory_gb": round(device.free_memory_gb, 2),
                                "utilization": round(device.utilization_percent, 1),
                                "backend": device.backend,
                            }
                        )
            except Exception as e:
                logger.error(f"Failed to enumerate GPU devices: {e}")

        return info

    def clear_cache(self):
        """Clear device cache."""
        self._device_cache.clear()


# Global singleton instance
_device_manager = _GPUDeviceManager()


# Public API
def is_gpu_available() -> bool:
    """Check if GPU is available.

    Returns:
        True if GPU is available, False otherwise.

    Example:
        if is_gpu_available():
            print("GPU acceleration enabled")
    """
    return _device_manager.is_available()


def get_gpu_device(device_id: Optional[int] = None) -> Optional[GPUDevice]:
    """Get GPU device information.

    Args:
        device_id: Device ID to query. If None, uses current device.

    Returns:
        GPUDevice object or None if not available.

    Example:
        device = get_gpu_device(0)
        if device:
            print(f"Using {device.name} with {device.memory_gb:.1f} GB")
    """
    return _device_manager.get_device(device_id)


def set_gpu_device(device_id: int) -> bool:
    """Set current GPU device.

    Args:
        device_id: Device ID to set as current.

    Returns:
        True if successful, False otherwise.

    Example:
        if set_gpu_device(1):
            print("Switched to GPU 1")
    """
    return _device_manager.set_device(device_id)


def get_gpu_info() -> Dict[str, Any]:
    """Get comprehensive GPU information.

    Returns:
        Dictionary with GPU information including all available devices.

    Example:
        info = get_gpu_info()
        print(f"Available: {info['available']}")
        for device in info['devices']:
            print(f"  {device['name']}: {device['memory_gb']} GB")
    """
    return _device_manager.get_info()
