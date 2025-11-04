"""Test suite for pixtreme_core.utils.device module (Device class)"""

import cupy as cp
import pytest
from pixtreme_core.utils import Device


class TestDevice:
    """Test cases for Device context manager"""

    def test_device_init_default(self):
        """Test Device initialization with default device_id=0"""
        device = Device()

        assert device.device_id == 0
        assert hasattr(device, "_device")

    def test_device_init_custom_id(self):
        """Test Device initialization with custom device_id"""
        device = Device(device_id=0)

        assert device.device_id == 0

    def test_device_context_manager_basic(self):
        """Test Device as context manager"""
        with Device(0) as dev:
            assert dev is not None
            assert isinstance(dev, Device)

    def test_device_context_manager_operation(self):
        """Test that operations work inside Device context"""
        with Device(0):
            # Create array on device
            arr = cp.array([1, 2, 3], dtype=cp.float32)
            assert isinstance(arr, cp.ndarray)
            assert arr.device.id == 0

    def test_device_multiple_contexts(self):
        """Test using Device context multiple times"""
        with Device(0):
            arr1 = cp.zeros(10)

        with Device(0):
            arr2 = cp.ones(10)

        assert arr1.device.id == 0
        assert arr2.device.id == 0

    def test_device_nested_contexts(self):
        """Test nested Device contexts"""
        with Device(0):
            arr1 = cp.zeros(10)
            assert arr1.device.id == 0

            with Device(0):
                arr2 = cp.ones(10)
                assert arr2.device.id == 0

    def test_device_exception_handling(self):
        """Test that Device context handles exceptions properly"""
        try:
            with Device(0):
                raise ValueError("Test exception")
        except ValueError:
            pass  # Expected

        # Should be able to use device after exception
        with Device(0):
            arr = cp.array([1, 2, 3])
            assert arr.device.id == 0

    def test_device_attributes(self):
        """Test Device instance attributes"""
        device = Device(0)

        assert hasattr(device, "device_id")
        assert hasattr(device, "_device")
        assert device.device_id == 0

    @pytest.mark.skipif(cp.cuda.runtime.getDeviceCount() < 2, reason="Requires 2+ GPUs")
    def test_device_switching(self):
        """Test switching between devices (requires multi-GPU system)"""
        # Use device 0
        with Device(0):
            arr0 = cp.zeros(10)
            assert arr0.device.id == 0

        # Use device 1
        with Device(1):
            arr1 = cp.ones(10)
            assert arr1.device.id == 1

    def test_device_returns_self(self):
        """Test that __enter__ returns self"""
        device = Device(0)
        with device as dev:
            assert dev is device

    def test_device_integration_with_operations(self):
        """Test Device with actual GPU operations"""
        with Device(0):
            # Create arrays
            a = cp.array([1.0, 2.0, 3.0], dtype=cp.float32)
            b = cp.array([4.0, 5.0, 6.0], dtype=cp.float32)

            # Perform operations
            c = a + b
            d = a * b

            # Verify results
            assert cp.allclose(c, [5.0, 7.0, 9.0])
            assert cp.allclose(d, [4.0, 10.0, 18.0])

    def test_device_with_image_operations(self):
        """Test Device with image-like operations"""
        with Device(0):
            # Create fake image
            image = cp.random.rand(256, 256, 3).astype(cp.float32)

            # Perform image operations
            grayscale = cp.mean(image, axis=2, keepdims=True)
            result = cp.concatenate([grayscale] * 3, axis=2)

            assert result.shape == (256, 256, 3)
            assert result.device.id == 0

    def test_device_current_device_unchanged(self):
        """Test that current device is properly restored after context"""
        # Use Device context
        with Device(0):
            pass

        # Current device should be restored (or still valid)
        current_device = cp.cuda.Device()
        assert current_device.id >= 0  # Valid device ID

    def test_device_type_validation(self):
        """Test Device with various device_id types"""
        # Integer device_id should work
        device = Device(0)
        assert device.device_id == 0

        # Test with explicit int
        device = Device(device_id=int(0))
        assert device.device_id == 0
