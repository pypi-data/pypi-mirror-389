"""Tests for TensorFlow/Keras model optimization.

Tests TFModelOptimizer, TFTrainingOptimizer, TFInferenceOptimizer, and
graceful degradation when TensorFlow is not available.
"""

from unittest.mock import Mock, patch

import pytest


# Test TensorFlow availability
class TestTensorFlowAvailability:
    """Tests for TensorFlow framework availability detection."""

    def test_tensorflow_available_flag(self):
        """Test TENSORFLOW_AVAILABLE flag is boolean."""
        from python_optimizer.ml import TENSORFLOW_AVAILABLE

        assert isinstance(TENSORFLOW_AVAILABLE, bool)

    def test_check_framework_availability(self):
        """Test framework availability checker includes TensorFlow."""
        from python_optimizer.ml import check_framework_availability

        info = check_framework_availability()
        assert isinstance(info, dict)
        assert "tensorflow" in info
        assert "available" in info["tensorflow"]
        assert isinstance(info["tensorflow"]["available"], bool)

    def test_tensorflow_version_when_available(self):
        """Test TensorFlow version is set when available."""
        from python_optimizer.ml import TENSORFLOW_AVAILABLE, TENSORFLOW_VERSION

        if TENSORFLOW_AVAILABLE:
            assert TENSORFLOW_VERSION is not None
            assert isinstance(TENSORFLOW_VERSION, str)
        else:
            assert TENSORFLOW_VERSION is None


# Skip TensorFlow tests if not available
pytestmark = pytest.mark.skipif(
    not pytest.importorskip("tensorflow", reason="TensorFlow not available"),
    reason="TensorFlow not available",
)


class TestTFModelOptimizer:
    """Tests for TFModelOptimizer class."""

    @pytest.fixture
    def simple_model(self):
        """Create a simple Keras model for testing."""
        import tensorflow as tf

        model = tf.keras.Sequential(
            [
                tf.keras.layers.Dense(20, activation="relu", input_shape=(10,)),
                tf.keras.layers.Dense(1),
            ]
        )
        return model

    def test_model_optimizer_initialization(self, simple_model):
        """Test TFModelOptimizer initialization."""
        from python_optimizer.ml import TFModelOptimizer

        optimizer = TFModelOptimizer(simple_model, use_xla=False)
        assert optimizer.model is not None
        assert optimizer.device is not None
        assert optimizer.mixed_precision is False
        assert optimizer.use_xla is False

    def test_model_optimizer_with_device_selection(self, simple_model):
        """Test model optimizer with explicit device."""
        from python_optimizer.ml import TFModelOptimizer

        optimizer = TFModelOptimizer(simple_model, device="CPU:0", use_xla=False)
        assert "/CPU:0" in optimizer.device

    def test_model_optimizer_xla_enabled(self, simple_model):
        """Test model optimizer with XLA compilation."""
        from python_optimizer.ml import TFModelOptimizer

        optimizer = TFModelOptimizer(simple_model, use_xla=True)
        assert optimizer.use_xla is True

    def test_model_optimizer_mixed_precision(self, simple_model):
        """Test model optimizer with mixed precision."""
        from python_optimizer.ml import TFModelOptimizer

        optimizer = TFModelOptimizer(
            simple_model, device="CPU:0", mixed_precision=True, use_xla=False
        )
        assert optimizer.mixed_precision is True

    def test_model_optimizer_forward_pass(self, simple_model):
        """Test optimized forward pass."""
        import tensorflow as tf

        from python_optimizer.ml import TFModelOptimizer

        optimizer = TFModelOptimizer(simple_model, device="CPU:0", use_xla=False)

        # Create dummy input
        x = tf.random.normal((5, 10))
        output = optimizer(x)

        assert output is not None
        assert output.shape == (5, 1)
        assert optimizer.stats["forward_passes"] == 1
        assert optimizer.stats["total_forward_time"] > 0

    def test_model_optimizer_statistics(self, simple_model):
        """Test optimizer statistics tracking."""
        import tensorflow as tf

        from python_optimizer.ml import TFModelOptimizer

        optimizer = TFModelOptimizer(simple_model, device="CPU:0", use_xla=False)

        # Run multiple forward passes
        x = tf.random.normal((5, 10))
        for _ in range(3):
            optimizer(x)

        stats = optimizer.get_stats()
        assert stats["forward_passes"] == 3
        assert stats["total_forward_time"] > 0
        assert stats["avg_forward_time"] > 0
        assert "device" in stats
        assert stats["mixed_precision"] is False

    def test_model_optimizer_training_mode(self, simple_model):
        """Test forward pass in training mode."""
        import tensorflow as tf

        from python_optimizer.ml import TFModelOptimizer

        optimizer = TFModelOptimizer(simple_model, device="CPU:0", use_xla=False)

        x = tf.random.normal((5, 10))
        output = optimizer(x, training=True)

        assert output is not None
        assert output.shape == (5, 1)

    def test_model_optimizer_without_tensorflow_raises(self):
        """Test that optimizer raises RuntimeError without TensorFlow."""
        with patch(
            "python_optimizer.ml.tensorflow_optimizer.TENSORFLOW_AVAILABLE", False
        ):
            from python_optimizer.ml.tensorflow_optimizer import TFModelOptimizer

            with pytest.raises(RuntimeError, match="TensorFlow is not installed"):
                TFModelOptimizer(Mock())


class TestTFTrainingOptimizer:
    """Tests for TFTrainingOptimizer class."""

    @pytest.fixture
    def training_setup(self):
        """Create model, optimizer, and data for training tests."""
        import tensorflow as tf

        model = tf.keras.Sequential([tf.keras.layers.Dense(1, input_shape=(10,))])
        optimizer = tf.keras.optimizers.SGD(learning_rate=0.01)
        loss_fn = tf.keras.losses.MeanSquaredError()

        # Generate random data
        inputs = tf.random.normal((8, 10))
        targets = tf.random.normal((8, 1))

        return model, optimizer, loss_fn, inputs, targets

    def test_training_optimizer_initialization(self, training_setup):
        """Test TFTrainingOptimizer initialization."""
        from python_optimizer.ml import TFTrainingOptimizer

        model, optimizer, _, _, _ = training_setup

        training_opt = TFTrainingOptimizer(
            model, optimizer, device="CPU:0", mixed_precision=False, use_xla=False
        )

        assert training_opt.model is not None
        assert training_opt.optimizer is not None
        assert "/CPU:0" in training_opt.device
        assert training_opt.gradient_accumulation_steps == 1

    def test_training_optimizer_with_options(self, training_setup):
        """Test TFTrainingOptimizer with custom options."""
        from python_optimizer.ml import TFTrainingOptimizer

        model, optimizer, _, _, _ = training_setup

        training_opt = TFTrainingOptimizer(
            model,
            optimizer,
            device="CPU:0",
            mixed_precision=False,
            gradient_accumulation_steps=4,
            use_xla=False,
        )

        assert training_opt.gradient_accumulation_steps == 4

    def test_training_optimizer_training_step(self, training_setup):
        """Test optimized training step."""
        from python_optimizer.ml import TFTrainingOptimizer

        model, optimizer, loss_fn, inputs, targets = training_setup

        training_opt = TFTrainingOptimizer(
            model, optimizer, device="CPU:0", mixed_precision=False, use_xla=False
        )

        # Run training step
        result = training_opt.training_step(inputs, targets, loss_fn, step=0)

        assert isinstance(result, dict)
        assert "loss" in result
        assert "step_time" in result
        assert "gpu_memory_used" in result
        assert result["loss"] > 0
        assert result["step_time"] > 0

    def test_training_optimizer_gradient_accumulation(self, training_setup):
        """Test gradient accumulation."""
        from python_optimizer.ml import TFTrainingOptimizer

        model, optimizer, loss_fn, inputs, targets = training_setup

        training_opt = TFTrainingOptimizer(
            model,
            optimizer,
            device="CPU:0",
            mixed_precision=False,
            gradient_accumulation_steps=2,
            use_xla=False,
        )

        # Step 0 should accumulate
        result1 = training_opt.training_step(inputs, targets, loss_fn, step=0)
        assert "loss" in result1

        # Step 1 should apply accumulated gradients
        result2 = training_opt.training_step(inputs, targets, loss_fn, step=1)
        assert "loss" in result2

        stats = training_opt.get_stats()
        assert stats["steps"] == 2

    def test_training_optimizer_statistics(self, training_setup):
        """Test training statistics tracking."""
        from python_optimizer.ml import TFTrainingOptimizer

        model, optimizer, loss_fn, inputs, targets = training_setup

        training_opt = TFTrainingOptimizer(
            model, optimizer, device="CPU:0", mixed_precision=False, use_xla=False
        )

        # Run multiple steps
        for step in range(5):
            training_opt.training_step(inputs, targets, loss_fn, step=step)

        stats = training_opt.get_stats()
        assert stats["steps"] == 5
        assert stats["total_time"] > 0
        assert stats["avg_step_time"] > 0
        assert "device" in stats
        assert "mixed_precision" in stats

    def test_training_optimizer_without_tensorflow_raises(self):
        """Test that TFTrainingOptimizer raises RuntimeError without TensorFlow."""
        with patch(
            "python_optimizer.ml.tensorflow_optimizer.TENSORFLOW_AVAILABLE", False
        ):
            from python_optimizer.ml.tensorflow_optimizer import TFTrainingOptimizer

            with pytest.raises(RuntimeError, match="TensorFlow is not installed"):
                TFTrainingOptimizer(Mock(), Mock())


class TestTFInferenceOptimizer:
    """Tests for TFInferenceOptimizer class."""

    @pytest.fixture
    def inference_model(self):
        """Create a simple model for inference testing."""
        import tensorflow as tf

        model = tf.keras.Sequential([tf.keras.layers.Dense(1, input_shape=(10,))])
        return model

    def test_inference_optimizer_initialization(self, inference_model):
        """Test TFInferenceOptimizer initialization."""
        from python_optimizer.ml import TFInferenceOptimizer

        inf_opt = TFInferenceOptimizer(inference_model, device="CPU:0", use_xla=False)

        assert inf_opt.model is not None
        assert "/CPU:0" in inf_opt.device
        assert inf_opt.batch_size is None

    def test_inference_optimizer_with_batch_size(self, inference_model):
        """Test TFInferenceOptimizer with explicit batch size."""
        from python_optimizer.ml import TFInferenceOptimizer

        inf_opt = TFInferenceOptimizer(
            inference_model, device="CPU:0", use_xla=False, batch_size=32
        )

        assert inf_opt.batch_size == 32

    def test_inference_optimizer_predict(self, inference_model):
        """Test inference prediction."""
        import tensorflow as tf

        from python_optimizer.ml import TFInferenceOptimizer

        inf_opt = TFInferenceOptimizer(inference_model, device="CPU:0", use_xla=False)

        # Single prediction
        x = tf.random.normal((1, 10))
        output = inf_opt.predict(x)

        assert output is not None
        assert output.shape == (1, 1)
        assert inf_opt.stats["predictions"] == 1

    def test_inference_optimizer_batch_predict(self, inference_model):
        """Test batch prediction."""
        import tensorflow as tf

        from python_optimizer.ml import TFInferenceOptimizer

        inf_opt = TFInferenceOptimizer(
            inference_model, device="CPU:0", use_xla=False, batch_size=4
        )

        # Create list of inputs
        inputs = [tf.random.normal((1, 10)) for _ in range(10)]
        outputs = inf_opt.batch_predict(inputs)

        assert len(outputs) == 10
        assert inf_opt.stats["predictions"] == 3  # 10/4 = 3 batches (ceil)

    def test_inference_optimizer_statistics(self, inference_model):
        """Test inference statistics tracking."""
        import tensorflow as tf

        from python_optimizer.ml import TFInferenceOptimizer

        inf_opt = TFInferenceOptimizer(inference_model, device="CPU:0", use_xla=False)

        # Run multiple predictions
        for _ in range(5):
            x = tf.random.normal((1, 10))
            inf_opt.predict(x)

        stats = inf_opt.get_stats()
        assert stats["predictions"] == 5
        assert stats["total_time"] > 0
        assert stats["avg_prediction_time"] > 0
        assert "device" in stats

    def test_inference_optimizer_without_tensorflow_raises(self):
        """Test that TFInferenceOptimizer raises RuntimeError without TensorFlow."""
        with patch(
            "python_optimizer.ml.tensorflow_optimizer.TENSORFLOW_AVAILABLE", False
        ):
            from python_optimizer.ml.tensorflow_optimizer import TFInferenceOptimizer

            with pytest.raises(RuntimeError, match="TensorFlow is not installed"):
                TFInferenceOptimizer(Mock())


class TestHighLevelAPI:
    """Tests for high-level API functions."""

    @pytest.fixture
    def simple_model(self):
        """Create a simple model for API testing."""
        import tensorflow as tf

        model = tf.keras.Sequential([tf.keras.layers.Dense(1, input_shape=(10,))])
        return model

    def test_optimize_tf_model_function(self, simple_model):
        """Test optimize_tf_model convenience function."""
        from python_optimizer.ml import optimize_tf_model

        optimized = optimize_tf_model(simple_model, device="CPU:0", use_xla=False)

        assert optimized is not None
        from python_optimizer.ml import TFModelOptimizer

        assert isinstance(optimized, TFModelOptimizer)

    def test_optimize_tf_training_decorator(self):
        """Test optimize_tf_training decorator."""
        import tensorflow as tf

        from python_optimizer.ml import optimize_tf_training

        @optimize_tf_training(mixed_precision=False, use_xla=False)
        def train_step(model, inputs, targets, loss_fn, optimizer):
            with tf.GradientTape() as tape:
                predictions = model(inputs)
                loss = loss_fn(targets, predictions)
            gradients = tape.gradient(loss, model.trainable_variables)
            optimizer.apply_gradients(zip(gradients, model.trainable_variables))
            return float(loss.numpy())

        # Create simple training setup
        model = tf.keras.Sequential([tf.keras.layers.Dense(1, input_shape=(10,))])
        optimizer = tf.keras.optimizers.SGD(learning_rate=0.01)
        loss_fn = tf.keras.losses.MeanSquaredError()
        inputs = tf.random.normal((4, 10))
        targets = tf.random.normal((4, 1))

        # Run training step
        loss = train_step(model, inputs, targets, loss_fn, optimizer)
        assert isinstance(loss, float)
        assert loss >= 0

    def test_optimize_tf_inference_function(self, simple_model):
        """Test optimize_tf_inference convenience function."""
        from python_optimizer.ml import optimize_tf_inference

        inf_opt = optimize_tf_inference(simple_model, device="CPU:0", use_xla=False)

        assert inf_opt is not None
        from python_optimizer.ml import TFInferenceOptimizer

        assert isinstance(inf_opt, TFInferenceOptimizer)


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_model_with_multiple_outputs(self):
        """Test model that returns multiple outputs."""
        import tensorflow as tf

        from python_optimizer.ml import TFModelOptimizer

        # Model with multiple outputs
        input_layer = tf.keras.Input(shape=(10,))
        output1 = tf.keras.layers.Dense(5)(input_layer)
        output2 = tf.keras.layers.Dense(3)(input_layer)
        model = tf.keras.Model(inputs=input_layer, outputs=[output1, output2])

        optimizer = TFModelOptimizer(model, device="CPU:0", use_xla=False)

        x = tf.random.normal((4, 10))
        out1, out2 = optimizer(x)
        assert out1.shape == (4, 5)
        assert out2.shape == (4, 3)

    def test_inference_with_empty_batch(self):
        """Test inference with empty batch list."""
        import tensorflow as tf

        from python_optimizer.ml import TFInferenceOptimizer

        model = tf.keras.Sequential([tf.keras.layers.Dense(1, input_shape=(10,))])
        inf_opt = TFInferenceOptimizer(model, device="CPU:0", use_xla=False)

        outputs = inf_opt.batch_predict([])
        assert outputs == []

    def test_model_with_custom_layers(self):
        """Test model with custom layers."""
        import tensorflow as tf

        from python_optimizer.ml import TFModelOptimizer

        class CustomLayer(tf.keras.layers.Layer):
            def __init__(self):
                super().__init__()
                self.dense = tf.keras.layers.Dense(5)

            def call(self, inputs):
                return self.dense(inputs)

        model = tf.keras.Sequential([CustomLayer(), tf.keras.layers.Dense(1)])
        optimizer = TFModelOptimizer(model, device="CPU:0", use_xla=False)

        x = tf.random.normal((4, 10))
        output = optimizer(x)
        assert output.shape == (4, 1)


class TestIntegration:
    """Integration tests combining multiple components."""

    def test_full_training_workflow(self):
        """Test complete training workflow with optimizer."""
        import tensorflow as tf

        from python_optimizer.ml import TFModelOptimizer, TFTrainingOptimizer

        # Create model
        model = tf.keras.Sequential([tf.keras.layers.Dense(1, input_shape=(10,))])

        # Optimize model
        model_opt = TFModelOptimizer(
            model, device="CPU:0", use_xla=False, mixed_precision=False
        )

        # Create training optimizer
        optimizer = tf.keras.optimizers.Adam(learning_rate=0.001)
        loss_fn = tf.keras.losses.MeanSquaredError()

        training_opt = TFTrainingOptimizer(
            model_opt.model,
            optimizer,
            device="CPU:0",
            mixed_precision=False,
            use_xla=False,
        )

        # Generate data
        inputs = tf.random.normal((16, 10))
        targets = tf.random.normal((16, 1))

        # Train for a few steps
        for step in range(10):
            training_opt.training_step(inputs, targets, loss_fn, step)

        # Check that training happened
        stats = training_opt.get_stats()
        assert stats["steps"] == 10
        assert stats["total_time"] > 0

    def test_full_inference_workflow(self):
        """Test complete inference workflow with optimizer."""
        import tensorflow as tf

        from python_optimizer.ml import optimize_tf_inference, optimize_tf_model

        # Create model
        model = tf.keras.Sequential([tf.keras.layers.Dense(1, input_shape=(10,))])

        # Optimize for training (could train here)
        model_opt = optimize_tf_model(model, device="CPU:0", use_xla=False)

        # Switch to inference mode
        inf_opt = optimize_tf_inference(model_opt.model, device="CPU:0", use_xla=False)

        # Run inference
        test_inputs = [tf.random.normal((1, 10)) for _ in range(20)]
        outputs = inf_opt.batch_predict(test_inputs)

        assert len(outputs) == 20

        stats = inf_opt.get_stats()
        assert stats["predictions"] == 1  # All processed in one batch


class TestPerformance:
    """Performance and benchmark tests."""

    @pytest.mark.benchmark
    def test_optimization_overhead(self):
        """Test that optimization overhead is minimal."""
        import time

        import tensorflow as tf

        from python_optimizer.ml import TFModelOptimizer

        model = tf.keras.Sequential(
            [
                tf.keras.layers.Dense(50, activation="relu", input_shape=(100,)),
                tf.keras.layers.Dense(10),
            ]
        )

        optimizer = TFModelOptimizer(model, device="CPU:0", use_xla=False)

        # Warm up
        x = tf.random.normal((32, 100))
        for _ in range(10):
            optimizer(x)

        # Benchmark
        num_iterations = 100
        start = time.perf_counter()
        for _ in range(num_iterations):
            optimizer(x)
        elapsed = time.perf_counter() - start

        avg_time = elapsed / num_iterations
        # Overhead should be minimal (< 1ms per forward pass on CPU)
        assert avg_time < 0.001

    @pytest.mark.benchmark
    def test_batch_inference_efficiency(self):
        """Test batch inference is more efficient than individual predictions."""
        import time

        import tensorflow as tf

        from python_optimizer.ml import TFInferenceOptimizer

        model = tf.keras.Sequential([tf.keras.layers.Dense(10, input_shape=(50,))])
        inf_opt = TFInferenceOptimizer(
            model, device="CPU:0", use_xla=False, batch_size=8
        )

        # Create test inputs
        inputs = [tf.random.normal((1, 50)) for _ in range(32)]

        # Batch prediction
        start = time.perf_counter()
        batch_outputs = inf_opt.batch_predict(inputs)
        batch_time = time.perf_counter() - start

        # Individual predictions
        inf_opt2 = TFInferenceOptimizer(model, device="CPU:0", use_xla=False)
        start = time.perf_counter()
        individual_outputs = [inf_opt2.predict(x) for x in inputs]
        individual_time = time.perf_counter() - start

        # Batch should be faster or comparable
        assert len(batch_outputs) == len(individual_outputs)
        # Allow some tolerance
        assert batch_time <= individual_time * 1.5
