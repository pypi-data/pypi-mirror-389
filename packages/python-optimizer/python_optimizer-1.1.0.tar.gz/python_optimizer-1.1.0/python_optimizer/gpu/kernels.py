"""GPU kernel library with optimized operations.

Provides GPU-accelerated implementations of common operations
using CuPy and Numba CUDA.
"""

import logging
from typing import Callable, Optional

import numpy as np

logger = logging.getLogger(__name__)

try:
    import cupy as cp

    CUPY_AVAILABLE = True
except ImportError:
    CUPY_AVAILABLE = False
    cp = None


class GPUKernelLibrary:
    """Library of GPU-accelerated operations."""

    @staticmethod
    def array_sum(arr: np.ndarray) -> float:
        """GPU-accelerated array sum.

        Args:
            arr: Input array.

        Returns:
            Sum of array elements.
        """
        if CUPY_AVAILABLE:
            gpu_arr = cp.asarray(arr)
            result = cp.sum(gpu_arr)
            return float(cp.asnumpy(result))
        return float(np.sum(arr))

    @staticmethod
    def array_mean(arr: np.ndarray) -> float:
        """GPU-accelerated array mean.

        Args:
            arr: Input array.

        Returns:
            Mean of array elements.
        """
        if CUPY_AVAILABLE:
            gpu_arr = cp.asarray(arr)
            result = cp.mean(gpu_arr)
            return float(cp.asnumpy(result))
        return float(np.mean(arr))

    @staticmethod
    def array_std(arr: np.ndarray) -> float:
        """GPU-accelerated array standard deviation.

        Args:
            arr: Input array.

        Returns:
            Standard deviation of array elements.
        """
        if CUPY_AVAILABLE:
            gpu_arr = cp.asarray(arr)
            result = cp.std(gpu_arr)
            return float(cp.asnumpy(result))
        return float(np.std(arr))

    @staticmethod
    def matrix_multiply(a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """GPU-accelerated matrix multiplication.

        Args:
            a: First matrix.
            b: Second matrix.

        Returns:
            Matrix product a @ b.
        """
        if CUPY_AVAILABLE:
            gpu_a = cp.asarray(a)
            gpu_b = cp.asarray(b)
            result = cp.matmul(gpu_a, gpu_b)
            return cp.asnumpy(result)
        return np.matmul(a, b)

    @staticmethod
    def element_wise_multiply(a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """GPU-accelerated element-wise multiplication.

        Args:
            a: First array.
            b: Second array.

        Returns:
            Element-wise product a * b.
        """
        if CUPY_AVAILABLE:
            gpu_a = cp.asarray(a)
            gpu_b = cp.asarray(b)
            result = gpu_a * gpu_b
            return cp.asnumpy(result)
        return a * b

    @staticmethod
    def element_wise_add(a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """GPU-accelerated element-wise addition.

        Args:
            a: First array.
            b: Second array.

        Returns:
            Element-wise sum a + b.
        """
        if CUPY_AVAILABLE:
            gpu_a = cp.asarray(a)
            gpu_b = cp.asarray(b)
            result = gpu_a + gpu_b
            return cp.asnumpy(result)
        return a + b

    @staticmethod
    def power(arr: np.ndarray, exponent: float) -> np.ndarray:
        """GPU-accelerated array power operation.

        Args:
            arr: Input array.
            exponent: Power to raise elements to.

        Returns:
            Array with each element raised to exponent.
        """
        if CUPY_AVAILABLE:
            gpu_arr = cp.asarray(arr)
            result = cp.power(gpu_arr, exponent)
            return cp.asnumpy(result)
        return np.power(arr, exponent)

    @staticmethod
    def sqrt(arr: np.ndarray) -> np.ndarray:
        """GPU-accelerated square root.

        Args:
            arr: Input array.

        Returns:
            Square root of each element.
        """
        if CUPY_AVAILABLE:
            gpu_arr = cp.asarray(arr)
            result = cp.sqrt(gpu_arr)
            return cp.asnumpy(result)
        return np.sqrt(arr)

    @staticmethod
    def exp(arr: np.ndarray) -> np.ndarray:
        """GPU-accelerated exponential.

        Args:
            arr: Input array.

        Returns:
            Exponential of each element.
        """
        if CUPY_AVAILABLE:
            gpu_arr = cp.asarray(arr)
            result = cp.exp(gpu_arr)
            return cp.asnumpy(result)
        return np.exp(arr)

    @staticmethod
    def log(arr: np.ndarray) -> np.ndarray:
        """GPU-accelerated natural logarithm.

        Args:
            arr: Input array.

        Returns:
            Natural log of each element.
        """
        if CUPY_AVAILABLE:
            gpu_arr = cp.asarray(arr)
            result = cp.log(gpu_arr)
            return cp.asnumpy(result)
        return np.log(arr)

    @staticmethod
    def dot_product(a: np.ndarray, b: np.ndarray) -> float:
        """GPU-accelerated dot product.

        Args:
            a: First vector.
            b: Second vector.

        Returns:
            Dot product of a and b.
        """
        if CUPY_AVAILABLE:
            gpu_a = cp.asarray(a)
            gpu_b = cp.asarray(b)
            result = cp.dot(gpu_a, gpu_b)
            return float(cp.asnumpy(result))
        return float(np.dot(a, b))

    @staticmethod
    def cumsum(arr: np.ndarray) -> np.ndarray:
        """GPU-accelerated cumulative sum.

        Args:
            arr: Input array.

        Returns:
            Cumulative sum of array elements.
        """
        if CUPY_AVAILABLE:
            gpu_arr = cp.asarray(arr)
            result = cp.cumsum(gpu_arr)
            return cp.asnumpy(result)
        return np.cumsum(arr)

    @staticmethod
    def sort(arr: np.ndarray) -> np.ndarray:
        """GPU-accelerated array sort.

        Args:
            arr: Input array.

        Returns:
            Sorted array.
        """
        if CUPY_AVAILABLE:
            gpu_arr = cp.asarray(arr)
            result = cp.sort(gpu_arr)
            return cp.asnumpy(result)
        return np.sort(arr)

    @staticmethod
    def argsort(arr: np.ndarray) -> np.ndarray:
        """GPU-accelerated argsort.

        Args:
            arr: Input array.

        Returns:
            Indices that would sort the array.
        """
        if CUPY_AVAILABLE:
            gpu_arr = cp.asarray(arr)
            result = cp.argsort(gpu_arr)
            return cp.asnumpy(result)
        return np.argsort(arr)

    @staticmethod
    def min(arr: np.ndarray) -> float:
        """GPU-accelerated array minimum.

        Args:
            arr: Input array.

        Returns:
            Minimum value in array.
        """
        if CUPY_AVAILABLE:
            gpu_arr = cp.asarray(arr)
            result = cp.min(gpu_arr)
            return float(cp.asnumpy(result))
        return float(np.min(arr))

    @staticmethod
    def max(arr: np.ndarray) -> float:
        """GPU-accelerated array maximum.

        Args:
            arr: Input array.

        Returns:
            Maximum value in array.
        """
        if CUPY_AVAILABLE:
            gpu_arr = cp.asarray(arr)
            result = cp.max(gpu_arr)
            return float(cp.asnumpy(result))
        return float(np.max(arr))

    @staticmethod
    def concatenate(arrays: list, axis: int = 0) -> np.ndarray:
        """GPU-accelerated array concatenation.

        Args:
            arrays: List of arrays to concatenate.
            axis: Axis along which to concatenate.

        Returns:
            Concatenated array.
        """
        if CUPY_AVAILABLE:
            gpu_arrays = [cp.asarray(arr) for arr in arrays]
            result = cp.concatenate(gpu_arrays, axis=axis)
            return cp.asnumpy(result)
        return np.concatenate(arrays, axis=axis)

    @staticmethod
    def reshape(arr: np.ndarray, shape: tuple) -> np.ndarray:
        """GPU-accelerated array reshape.

        Args:
            arr: Input array.
            shape: Target shape.

        Returns:
            Reshaped array.
        """
        if CUPY_AVAILABLE:
            gpu_arr = cp.asarray(arr)
            result = cp.reshape(gpu_arr, shape)
            return cp.asnumpy(result)
        return np.reshape(arr, shape)

    @staticmethod
    def transpose(arr: np.ndarray) -> np.ndarray:
        """GPU-accelerated array transpose.

        Args:
            arr: Input array.

        Returns:
            Transposed array.
        """
        if CUPY_AVAILABLE:
            gpu_arr = cp.asarray(arr)
            result = cp.transpose(gpu_arr)
            return cp.asnumpy(result)
        return np.transpose(arr)


# Convenience functions for direct kernel access
def gpu_sum(arr: np.ndarray) -> float:
    """GPU-accelerated sum. See GPUKernelLibrary.array_sum."""
    return GPUKernelLibrary.array_sum(arr)


def gpu_mean(arr: np.ndarray) -> float:
    """GPU-accelerated mean. See GPUKernelLibrary.array_mean."""
    return GPUKernelLibrary.array_mean(arr)


def gpu_matmul(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """GPU-accelerated matrix multiplication. See GPUKernelLibrary.matrix_multiply."""
    return GPUKernelLibrary.matrix_multiply(a, b)
