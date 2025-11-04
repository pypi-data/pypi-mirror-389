"""Test suite for pixtreme_core.transform.affine module (affine_transform, get_inverse_matrix)"""

import cupy as cp
import numpy as np
import pytest
from pixtreme_core.constants import (
    INTER_AREA,
    INTER_AUTO,
    INTER_B_SPLINE,
    INTER_CATMULL_ROM,
    INTER_CUBIC,
    INTER_LANCZOS2,
    INTER_LANCZOS3,
    INTER_LANCZOS4,
    INTER_LINEAR,
    INTER_MITCHELL,
    INTER_NEAREST,
)
from pixtreme_core.transform.affine import affine_transform, get_inverse_matrix


class TestGetInverseMatrix:
    """Test cases for get_inverse_matrix() function"""

    def test_inverse_matrix_identity(self):
        """Test inverse of identity matrix"""
        # Identity matrix (2x3)
        M = cp.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=cp.float32)

        inv_M = get_inverse_matrix(M)

        # Inverse of identity is identity
        assert cp.allclose(inv_M, M, atol=1e-6)

    def test_inverse_matrix_translation(self):
        """Test inverse of translation matrix"""
        # Translation by (10, 20)
        M = cp.array([[1.0, 0.0, 10.0], [0.0, 1.0, 20.0]], dtype=cp.float32)

        inv_M = get_inverse_matrix(M)

        # Inverse should translate by (-10, -20)
        expected = cp.array([[1.0, 0.0, -10.0], [0.0, 1.0, -20.0]], dtype=cp.float32)
        assert cp.allclose(inv_M, expected, atol=1e-5)

    def test_inverse_matrix_scale(self):
        """Test inverse of scale matrix"""
        # Scale by (2, 3)
        M = cp.array([[2.0, 0.0, 0.0], [0.0, 3.0, 0.0]], dtype=cp.float32)

        inv_M = get_inverse_matrix(M)

        # Inverse should scale by (1/2, 1/3)
        expected = cp.array([[0.5, 0.0, 0.0], [0.0, 1 / 3, 0.0]], dtype=cp.float32)
        assert cp.allclose(inv_M, expected, atol=1e-5)

    def test_inverse_matrix_rotation(self):
        """Test inverse of rotation matrix"""
        # Rotation by 90 degrees
        M = cp.array([[0.0, -1.0, 0.0], [1.0, 0.0, 0.0]], dtype=cp.float32)

        inv_M = get_inverse_matrix(M)

        # Inverse should be rotation by -90 degrees
        expected = cp.array([[0.0, 1.0, 0.0], [-1.0, 0.0, 0.0]], dtype=cp.float32)
        assert cp.allclose(inv_M, expected, atol=1e-5)

    def test_inverse_matrix_3x3_input(self):
        """Test that 3x3 matrix is converted to 2x3"""
        # 3x3 matrix
        M = cp.array([[1.0, 0.0, 10.0], [0.0, 1.0, 20.0], [0.0, 0.0, 1.0]], dtype=cp.float32)

        inv_M = get_inverse_matrix(M)

        # Should return 2x3
        assert inv_M.shape == (2, 3)

    def test_inverse_matrix_numpy_input(self):
        """Test with NumPy input"""
        M = np.array([[1.0, 0.0, 5.0], [0.0, 1.0, 10.0]], dtype=np.float32)

        inv_M = get_inverse_matrix(M)

        assert isinstance(inv_M, np.ndarray)
        assert inv_M.shape == (2, 3)

    def test_inverse_matrix_cupy_input(self):
        """Test with CuPy input"""
        M = cp.array([[1.0, 0.0, 5.0], [0.0, 1.0, 10.0]], dtype=cp.float32)

        inv_M = get_inverse_matrix(M)

        assert isinstance(inv_M, cp.ndarray)
        assert inv_M.shape == (2, 3)

    def test_inverse_matrix_roundtrip(self):
        """Test that M @ inv(M) = I"""
        # Create arbitrary transformation
        M = cp.array([[2.0, 0.5, 10.0], [0.3, 1.5, 20.0]], dtype=cp.float32)

        inv_M = get_inverse_matrix(M)

        # Extend to 3x3 for multiplication
        M_3x3 = cp.vstack([M, [0, 0, 1]])
        inv_M_3x3 = cp.vstack([inv_M, [0, 0, 1]])

        # M @ inv(M) should be identity
        result = M_3x3 @ inv_M_3x3
        identity = cp.eye(3, dtype=cp.float32)

        assert cp.allclose(result, identity, atol=1e-5)


class TestAffineTransform:
    """Test cases for affine_transform() function"""

    @pytest.fixture
    def sample_image(self):
        """Create a sample test image"""
        image = cp.zeros((256, 256, 3), dtype=cp.float32)
        # Create red square in center
        image[100:150, 100:150, 0] = 1.0
        return image

    def test_affine_transform_identity(self, sample_image):
        """Test affine transform with identity matrix"""
        # Identity transformation
        M = cp.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=cp.float32)
        dsize = (256, 256)

        result = affine_transform(sample_image, M, dsize, flags=INTER_LINEAR)

        assert result.shape == (256, 256, 3)
        # Should be similar to original
        assert cp.allclose(result, sample_image, atol=0.1)

    def test_affine_transform_translation(self, sample_image):
        """Test affine transform with translation"""
        # Translate by (50, 30)
        M = cp.array([[1.0, 0.0, 50.0], [0.0, 1.0, 30.0]], dtype=cp.float32)
        dsize = (256, 256)

        result = affine_transform(sample_image, M, dsize, flags=INTER_LINEAR)

        assert result.shape == (256, 256, 3)
        # Red square should be translated
        # Original center: (125, 125), new center: (175, 155)
        assert result[155, 175, 0] > 0.5  # Red channel

    def test_affine_transform_scale_up(self, sample_image):
        """Test affine transform with scaling up"""
        # Scale by 2x
        M = cp.array([[2.0, 0.0, 0.0], [0.0, 2.0, 0.0]], dtype=cp.float32)
        dsize = (512, 512)

        result = affine_transform(sample_image, M, dsize, flags=INTER_LINEAR)

        assert result.shape == (512, 512, 3)

    def test_affine_transform_scale_down(self, sample_image):
        """Test affine transform with scaling down"""
        # Scale by 0.5x
        M = cp.array([[0.5, 0.0, 0.0], [0.0, 0.5, 0.0]], dtype=cp.float32)
        dsize = (128, 128)

        result = affine_transform(sample_image, M, dsize, flags=INTER_LINEAR)

        assert result.shape == (128, 128, 3)

    def test_affine_transform_rotation(self):
        """Test affine transform with rotation"""
        # Create simple image
        image = cp.zeros((256, 256, 3), dtype=cp.float32)
        image[100:150, 100:150, 0] = 1.0  # Red square

        # Rotate 45 degrees around center
        angle = cp.radians(45)
        cos_a = float(cp.cos(angle))
        sin_a = float(cp.sin(angle))
        center = cp.array([128, 128])

        M = cp.array([[cos_a, -sin_a, 0.0], [sin_a, cos_a, 0.0]], dtype=cp.float32)

        # Adjust for rotation around center
        M[0, 2] = -cos_a * center[0] + sin_a * center[1] + center[0]
        M[1, 2] = -sin_a * center[0] - cos_a * center[1] + center[1]

        dsize = (256, 256)
        result = affine_transform(image, M, dsize, flags=INTER_LINEAR)

        assert result.shape == (256, 256, 3)

    def test_affine_transform_different_interpolations(self, sample_image):
        """Test affine transform with different interpolation methods"""
        M = cp.array([[1.0, 0.0, 10.0], [0.0, 1.0, 10.0]], dtype=cp.float32)
        dsize = (256, 256)

        interpolations = [
            INTER_NEAREST,
            INTER_LINEAR,
            INTER_CUBIC,
            INTER_AREA,
            INTER_MITCHELL,
            INTER_CATMULL_ROM,
            INTER_B_SPLINE,
            INTER_LANCZOS2,
            INTER_LANCZOS3,
            INTER_LANCZOS4,
        ]

        for interp in interpolations:
            result = affine_transform(sample_image, M, dsize, flags=interp)
            assert result.shape == (256, 256, 3), f"Failed for interpolation {interp}"

    def test_affine_transform_auto_upscale(self, sample_image):
        """Test INTER_AUTO selects MITCHELL for upscaling"""
        # Scale up by 2x
        M = cp.array([[2.0, 0.0, 0.0], [0.0, 2.0, 0.0]], dtype=cp.float32)
        dsize = (512, 512)

        result = affine_transform(sample_image, M, dsize, flags=INTER_AUTO)

        assert result.shape == (512, 512, 3)

    def test_affine_transform_auto_downscale(self, sample_image):
        """Test INTER_AUTO selects AREA for downscaling"""
        # Scale down by 0.5x
        M = cp.array([[0.5, 0.0, 0.0], [0.0, 0.5, 0.0]], dtype=cp.float32)
        dsize = (128, 128)

        result = affine_transform(sample_image, M, dsize, flags=INTER_AUTO)

        assert result.shape == (128, 128, 3)

    def test_affine_transform_3x3_matrix(self, sample_image):
        """Test that 3x3 matrix is accepted and converted"""
        # 3x3 identity matrix
        M = cp.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]], dtype=cp.float32)
        dsize = (256, 256)

        result = affine_transform(sample_image, M, dsize, flags=INTER_LINEAR)

        assert result.shape == (256, 256, 3)

    def test_affine_transform_dtype_preserved(self, sample_image):
        """Test that dtype is float32"""
        M = cp.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=cp.float32)
        dsize = (256, 256)

        result = affine_transform(sample_image, M, dsize, flags=INTER_LINEAR)

        assert result.dtype == cp.float32

    def test_affine_transform_different_output_sizes(self, sample_image):
        """Test different output sizes"""
        M = cp.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=cp.float32)

        sizes = [(128, 128), (256, 256), (512, 512), (300, 400)]

        for h, w in sizes:
            result = affine_transform(sample_image, M, (h, w), flags=INTER_LINEAR)
            assert result.shape == (h, w, 3)

    def test_affine_transform_values_in_range(self, sample_image):
        """Test that output values are in valid range"""
        M = cp.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=cp.float32)
        dsize = (256, 256)

        result = affine_transform(sample_image, M, dsize, flags=INTER_LINEAR)

        # Values should be in [0, 1] range
        assert cp.all(result >= -0.01), "Values should be >= 0"
        assert cp.all(result <= 1.01), "Values should be <= 1"

    def test_affine_transform_shear(self):
        """Test affine transform with shear"""
        image = cp.zeros((256, 256, 3), dtype=cp.float32)
        image[100:150, 100:150, 0] = 1.0  # Red square

        # Shear transformation
        M = cp.array([[1.0, 0.3, 0.0], [0.0, 1.0, 0.0]], dtype=cp.float32)
        dsize = (256, 256)

        result = affine_transform(image, M, dsize, flags=INTER_LINEAR)

        assert result.shape == (256, 256, 3)

    def test_affine_transform_combined_transforms(self):
        """Test affine transform with combined transformations"""
        image = cp.zeros((256, 256, 3), dtype=cp.float32)
        image[100:150, 100:150, 0] = 1.0

        # Combine scale + rotation + translation
        scale = 1.5
        angle = cp.radians(30)
        cos_a = float(cp.cos(angle) * scale)
        sin_a = float(cp.sin(angle) * scale)

        M = cp.array([[cos_a, -sin_a, 50.0], [sin_a, cos_a, 30.0]], dtype=cp.float32)

        dsize = (400, 400)
        result = affine_transform(image, M, dsize, flags=INTER_LINEAR)

        assert result.shape == (400, 400, 3)

    def test_affine_transform_large_image(self):
        """Test affine transform on large image"""
        large_image = cp.random.rand(2160, 3840, 3).astype(cp.float32)

        M = cp.array([[1.0, 0.0, 100.0], [0.0, 1.0, 100.0]], dtype=cp.float32)
        dsize = (2160, 3840)

        result = affine_transform(large_image, M, dsize, flags=INTER_LINEAR)

        assert result.shape == (2160, 3840, 3)

    def test_affine_transform_black_image(self):
        """Test affine transform on black image"""
        black = cp.zeros((256, 256, 3), dtype=cp.float32)

        M = cp.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=cp.float32)
        dsize = (256, 256)

        result = affine_transform(black, M, dsize, flags=INTER_LINEAR)

        assert cp.allclose(result, 0.0)

    def test_affine_transform_white_image(self):
        """Test affine transform on white image"""
        white = cp.ones((256, 256, 3), dtype=cp.float32)

        M = cp.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=cp.float32)
        dsize = (256, 256)

        result = affine_transform(white, M, dsize, flags=INTER_LINEAR)

        assert cp.allclose(result, 1.0, atol=0.1)


class TestAffineIntegration:
    """Integration tests for affine transform workflow"""

    def test_affine_inverse_roundtrip(self):
        """Test forward and inverse affine transform"""
        image = cp.zeros((256, 256, 3), dtype=cp.float32)
        image[100:150, 100:150, 0] = 1.0

        # Forward transform: translate by (50, 30)
        M = cp.array([[1.0, 0.0, 50.0], [0.0, 1.0, 30.0]], dtype=cp.float32)
        dsize = (256, 256)

        transformed = affine_transform(image, M, dsize, flags=INTER_LINEAR)

        # Inverse transform: translate by (-50, -30)
        inv_M = get_inverse_matrix(M)
        recovered = affine_transform(transformed, inv_M, dsize, flags=INTER_LINEAR)

        # Should be close to original
        assert cp.allclose(recovered, image, atol=0.2)

    def test_affine_multiple_transforms(self):
        """Test applying multiple affine transforms sequentially"""
        image = cp.zeros((256, 256, 3), dtype=cp.float32)
        image[100:150, 100:150, 0] = 1.0

        # First transform: scale by 1.5
        M1 = cp.array([[1.5, 0.0, 0.0], [0.0, 1.5, 0.0]], dtype=cp.float32)
        result1 = affine_transform(image, M1, (384, 384), flags=INTER_LINEAR)

        # Second transform: translate
        M2 = cp.array([[1.0, 0.0, 50.0], [0.0, 1.0, 50.0]], dtype=cp.float32)
        result2 = affine_transform(result1, M2, (384, 384), flags=INTER_LINEAR)

        assert result2.shape == (384, 384, 3)

    def test_affine_all_interpolations_consistent(self):
        """Test that all interpolations produce reasonable results"""
        image = cp.zeros((256, 256, 3), dtype=cp.float32)
        image[100:150, 100:150, :] = 1.0  # White square

        M = cp.array([[1.0, 0.0, 20.0], [0.0, 1.0, 20.0]], dtype=cp.float32)
        dsize = (256, 256)

        interpolations = [
            INTER_NEAREST,
            INTER_LINEAR,
            INTER_CUBIC,
            INTER_AREA,
            INTER_MITCHELL,
            INTER_CATMULL_ROM,
            INTER_B_SPLINE,
            INTER_LANCZOS2,
            INTER_LANCZOS3,
            INTER_LANCZOS4,
            INTER_AUTO,
        ]

        results = []
        for interp in interpolations:
            result = affine_transform(image, M, dsize, flags=interp)
            results.append(result)

            # All should have some white pixels (translated square)
            assert cp.any(result > 0.5), f"Interpolation {interp} failed"

        # Results should be generally similar (all translate white square)
        # Compare INTER_LINEAR and INTER_CUBIC
        assert cp.allclose(results[1], results[2], atol=0.3)
