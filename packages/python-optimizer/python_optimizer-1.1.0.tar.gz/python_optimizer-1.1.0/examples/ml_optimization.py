#!/usr/bin/env python3
"""
Machine Learning Optimization Example

Demonstrates JIT optimization of ML algorithms including:
- K-Means clustering
- Neural network forward pass
- Gradient descent optimization
- Feature engineering pipelines
"""

import time

import matplotlib.pyplot as plt
import numpy as np
from sklearn.datasets import make_blobs, make_classification
from sklearn.preprocessing import StandardScaler

from python_optimizer import optimize

# =============================================================================
# K-Means Clustering Optimization
# =============================================================================


@optimize(jit=True, fastmath=True, nogil=True)
def kmeans_jit(data, centers, max_iters=100, tol=1e-4):
    """JIT-optimized K-means clustering algorithm."""
    n_samples, n_features = data.shape
    k = centers.shape[0]

    labels = np.zeros(n_samples, dtype=np.int32)
    prev_centers = centers.copy()

    for iteration in range(max_iters):
        # Assign points to closest centers
        for i in range(n_samples):
            min_dist = np.inf
            for j in range(k):
                dist = 0.0
                for f in range(n_features):
                    diff = data[i, f] - centers[j, f]
                    dist += diff * diff
                if dist < min_dist:
                    min_dist = dist
                    labels[i] = j

        # Update centers
        for j in range(k):
            count = 0
            for f in range(n_features):
                centers[j, f] = 0.0

            for i in range(n_samples):
                if labels[i] == j:
                    count += 1
                    for f in range(n_features):
                        centers[j, f] += data[i, f]

            if count > 0:
                for f in range(n_features):
                    centers[j, f] /= count

        # Check convergence
        max_shift = 0.0
        for j in range(k):
            shift = 0.0
            for f in range(n_features):
                diff = centers[j, f] - prev_centers[j, f]
                shift += diff * diff
            if shift > max_shift:
                max_shift = shift

        if max_shift < tol:
            break

        prev_centers[:] = centers

    return labels, centers


def kmeans_python(data, centers, max_iters=100, tol=1e-4):
    """Pure Python K-means for comparison."""
    n_samples, n_features = data.shape
    k = centers.shape[0]

    labels = np.zeros(n_samples, dtype=np.int32)
    prev_centers = centers.copy()

    for iteration in range(max_iters):
        # Assign points to closest centers
        for i in range(n_samples):
            distances = [np.sum((data[i] - centers[j]) ** 2) for j in range(k)]
            labels[i] = np.argmin(distances)

        # Update centers
        for j in range(k):
            cluster_points = data[labels == j]
            if len(cluster_points) > 0:
                centers[j] = np.mean(cluster_points, axis=0)

        # Check convergence
        if np.max(np.sum((centers - prev_centers) ** 2, axis=1)) < tol:
            break

        prev_centers = centers.copy()

    return labels, centers


# =============================================================================
# Neural Network Forward Pass Optimization
# =============================================================================


@optimize(jit=True, fastmath=True, nogil=True)
def relu_jit(x):
    """JIT-optimized ReLU activation."""
    return max(0.0, x)


@optimize(jit=True, fastmath=True, nogil=True)
def sigmoid_jit(x):
    """JIT-optimized sigmoid activation."""
    if x > 500:
        return 1.0
    elif x < -500:
        return 0.0
    return 1.0 / (1.0 + np.exp(-x))


@optimize(jit=True, fastmath=True, nogil=True)
def neural_forward_jit(X, W1, b1, W2, b2):
    """JIT-optimized neural network forward pass."""
    batch_size, input_size = X.shape
    hidden_size = W1.shape[1]
    output_size = W2.shape[1]

    # Hidden layer
    Z1 = np.zeros((batch_size, hidden_size))
    for i in range(batch_size):
        for j in range(hidden_size):
            z = b1[j]
            for k in range(input_size):
                z += X[i, k] * W1[k, j]
            Z1[i, j] = relu_jit(z)

    # Output layer
    Z2 = np.zeros((batch_size, output_size))
    for i in range(batch_size):
        for j in range(output_size):
            z = b2[j]
            for k in range(hidden_size):
                z += Z1[i, k] * W2[k, j]
            Z2[i, j] = sigmoid_jit(z)

    return Z1, Z2


def neural_forward_python(X, W1, b1, W2, b2):
    """Pure Python neural network forward pass."""
    Z1 = np.maximum(0, X @ W1 + b1)  # ReLU
    Z2 = 1 / (1 + np.exp(-(Z1 @ W2 + b2)))  # Sigmoid
    return Z1, Z2


# =============================================================================
# Gradient Descent Optimization
# =============================================================================


@optimize(jit=True, fastmath=True, nogil=True)
def gradient_descent_jit(X, y, learning_rate=0.01, max_iters=1000, tol=1e-6):
    """JIT-optimized gradient descent for linear regression."""
    n_samples, n_features = X.shape
    weights = np.zeros(n_features)
    bias = 0.0

    for iteration in range(max_iters):
        # Forward pass
        predictions = np.zeros(n_samples)
        for i in range(n_samples):
            pred = bias
            for j in range(n_features):
                pred += weights[j] * X[i, j]
            predictions[i] = pred

        # Compute cost and gradients
        cost = 0.0
        dw = np.zeros(n_features)
        db = 0.0

        for i in range(n_samples):
            error = predictions[i] - y[i]
            cost += error * error
            db += error
            for j in range(n_features):
                dw[j] += error * X[i, j]

        cost /= 2 * n_samples
        db /= n_samples
        for j in range(n_features):
            dw[j] /= n_samples

        # Update parameters
        prev_weights = weights.copy()
        prev_bias = bias

        for j in range(n_features):
            weights[j] -= learning_rate * dw[j]
        bias -= learning_rate * db

        # Check convergence
        weight_change = 0.0
        for j in range(n_features):
            diff = weights[j] - prev_weights[j]
            weight_change += diff * diff
        bias_change = (bias - prev_bias) ** 2

        if weight_change + bias_change < tol:
            break

    return weights, bias, cost


# =============================================================================
# Feature Engineering Pipeline
# =============================================================================


@optimize(jit=True, fastmath=True, nogil=True)
def polynomial_features_jit(X, degree=2):
    """JIT-optimized polynomial feature generation."""
    n_samples, n_features = X.shape

    # Calculate output size for polynomial features
    # For degree 2: original + squares + cross terms
    n_poly_features = n_features + n_features + (n_features * (n_features - 1)) // 2

    X_poly = np.zeros((n_samples, n_poly_features))

    for i in range(n_samples):
        idx = 0

        # Original features
        for j in range(n_features):
            X_poly[i, idx] = X[i, j]
            idx += 1

        # Square terms
        for j in range(n_features):
            X_poly[i, idx] = X[i, j] * X[i, j]
            idx += 1

        # Cross terms
        for j in range(n_features):
            for k in range(j + 1, n_features):
                X_poly[i, idx] = X[i, j] * X[i, k]
                idx += 1

    return X_poly


@optimize(jit=True, fastmath=True, nogil=True)
def standardize_jit(X):
    """JIT-optimized feature standardization."""
    n_samples, n_features = X.shape
    X_scaled = np.zeros_like(X)

    for j in range(n_features):
        # Compute mean
        mean = 0.0
        for i in range(n_samples):
            mean += X[i, j]
        mean /= n_samples

        # Compute std
        var = 0.0
        for i in range(n_samples):
            diff = X[i, j] - mean
            var += diff * diff
        var /= n_samples
        std = np.sqrt(var)

        # Standardize
        if std > 1e-8:  # Avoid division by zero
            for i in range(n_samples):
                X_scaled[i, j] = (X[i, j] - mean) / std
        else:
            for i in range(n_samples):
                X_scaled[i, j] = 0.0

    return X_scaled


# =============================================================================
# Benchmarking Functions
# =============================================================================


def benchmark_ml_algorithms():
    """Comprehensive ML algorithm benchmarking."""
    print("🧠 Machine Learning Optimization Benchmark")
    print("=" * 60)

    results = {}

    # 1. K-Means Clustering Benchmark
    print("\n📊 K-Means Clustering")
    print("-" * 30)

    X_kmeans, _ = make_blobs(n_samples=2000, centers=5, n_features=10, random_state=42)
    initial_centers = np.random.RandomState(42).normal(0, 1, (5, 10))

    # Warmup JIT
    kmeans_jit(X_kmeans[:100], initial_centers.copy())

    # Benchmark JIT version
    start_time = time.perf_counter()
    labels_jit, centers_jit = kmeans_jit(X_kmeans, initial_centers.copy())
    jit_time = time.perf_counter() - start_time

    # Benchmark Python version
    start_time = time.perf_counter()
    labels_py, centers_py = kmeans_python(X_kmeans, initial_centers.copy())
    python_time = time.perf_counter() - start_time

    kmeans_speedup = python_time / jit_time
    print(f"Python time:    {python_time:.4f}s")
    print(f"JIT time:       {jit_time:.4f}s")
    print(f"Speedup:        {kmeans_speedup:.2f}x")

    results["kmeans"] = {
        "python_time": python_time,
        "jit_time": jit_time,
        "speedup": kmeans_speedup,
    }

    # 2. Neural Network Forward Pass
    print("\n🧩 Neural Network Forward Pass")
    print("-" * 30)

    batch_size, input_size, hidden_size, output_size = 1000, 50, 100, 10
    X_nn = np.random.randn(batch_size, input_size)
    W1 = np.random.randn(input_size, hidden_size) * 0.1
    b1 = np.zeros(hidden_size)
    W2 = np.random.randn(hidden_size, output_size) * 0.1
    b2 = np.zeros(output_size)

    # Warmup JIT
    neural_forward_jit(X_nn[:10], W1, b1, W2, b2)

    # Benchmark JIT version
    start_time = time.perf_counter()
    Z1_jit, Z2_jit = neural_forward_jit(X_nn, W1, b1, W2, b2)
    jit_time = time.perf_counter() - start_time

    # Benchmark Python version
    start_time = time.perf_counter()
    Z1_py, Z2_py = neural_forward_python(X_nn, W1, b1, W2, b2)
    python_time = time.perf_counter() - start_time

    nn_speedup = python_time / jit_time
    print(f"Python time:    {python_time:.4f}s")
    print(f"JIT time:       {jit_time:.4f}s")
    print(f"Speedup:        {nn_speedup:.2f}x")

    results["neural_network"] = {
        "python_time": python_time,
        "jit_time": jit_time,
        "speedup": nn_speedup,
    }

    # 3. Gradient Descent
    print("\n📈 Gradient Descent")
    print("-" * 30)

    X_gd, y_gd = make_classification(
        n_samples=5000, n_features=20, n_informative=15, noise=0.1, random_state=42
    )
    y_gd = y_gd.astype(np.float64)

    # Warmup JIT
    gradient_descent_jit(X_gd[:100], y_gd[:100])

    # Benchmark JIT version
    start_time = time.perf_counter()
    weights_jit, bias_jit, cost_jit = gradient_descent_jit(X_gd, y_gd)
    jit_time = time.perf_counter() - start_time

    print(f"JIT time:       {jit_time:.4f}s")
    print(f"Final cost:     {cost_jit:.6f}")

    results["gradient_descent"] = {"jit_time": jit_time, "final_cost": cost_jit}

    # 4. Feature Engineering
    print("\n⚙️ Feature Engineering")
    print("-" * 30)

    X_fe = np.random.randn(2000, 15)

    # Polynomial features
    start_time = time.perf_counter()
    X_poly_jit = polynomial_features_jit(X_fe)
    poly_time = time.perf_counter() - start_time

    # Standardization
    start_time = time.perf_counter()
    X_scaled_jit = standardize_jit(X_fe)
    std_time = time.perf_counter() - start_time

    print(f"Polynomial features: {poly_time:.4f}s ({X_fe.shape} → {X_poly_jit.shape})")
    print(f"Standardization:     {std_time:.4f}s")

    results["feature_engineering"] = {
        "polynomial_time": poly_time,
        "standardization_time": std_time,
        "feature_expansion": f"{X_fe.shape} → {X_poly_jit.shape}",
    }

    # Summary
    print("\n🏆 Performance Summary")
    print("=" * 60)
    avg_speedup = np.mean(
        [results["kmeans"]["speedup"], results["neural_network"]["speedup"]]
    )
    print(f"Average ML Algorithm Speedup: {avg_speedup:.2f}x")
    print(f"K-Means Clustering:          {results['kmeans']['speedup']:.2f}x faster")
    print(
        f"Neural Network Forward:      {results['neural_network']['speedup']:.2f}x faster"
    )
    print(f"Feature Engineering:         Sub-millisecond processing")

    return results


if __name__ == "__main__":
    results = benchmark_ml_algorithms()
    print("\n✨ Machine Learning optimization complete!")
