"""Test suite for pixtreme_core.color.lut module (read_lut, apply_lut)"""

import os
import tempfile

import cupy as cp
import pytest
from pixtreme_core.color.lut import apply_lut, read_lut


class TestReadLut:
    """Test cases for read_lut() function"""

    @pytest.fixture
    def sample_cube_file(self):
        """Create a temporary .cube LUT file for testing"""
        # Create a simple 2x2x2 identity LUT
        cube_content = """TITLE "Test LUT"
LUT_3D_SIZE 2

0.0 0.0 0.0
1.0 0.0 0.0
0.0 1.0 0.0
1.0 1.0 0.0
0.0 0.0 1.0
1.0 0.0 1.0
0.0 1.0 1.0
1.0 1.0 1.0
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".cube", delete=False) as f:
            f.write(cube_content)
            temp_path = f.name

        yield temp_path

        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)

    @pytest.fixture
    def sample_cube_file_32(self):
        """Create a 32x32x32 LUT file (more realistic size)"""
        cube_content = 'TITLE "Test LUT 32"\nLUT_3D_SIZE 32\n\n'

        # Generate gradient LUT data
        for z in range(32):
            for y in range(32):
                for x in range(32):
                    r = x / 31.0
                    g = y / 31.0
                    b = z / 31.0
                    cube_content += f"{r:.6f} {g:.6f} {b:.6f}\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".cube", delete=False) as f:
            f.write(cube_content)
            temp_path = f.name

        yield temp_path

        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)

    def test_read_lut_basic(self, sample_cube_file):
        """Test basic LUT reading"""
        lut = read_lut(sample_cube_file, use_cache=False)

        assert isinstance(lut, cp.ndarray)
        assert lut.shape == (2, 2, 2, 3)
        assert lut.dtype == cp.float32

    def test_read_lut_identity_values(self, sample_cube_file):
        """Test that identity LUT values are correct"""
        lut = read_lut(sample_cube_file, use_cache=False)

        # Check corners of identity LUT
        assert cp.allclose(lut[0, 0, 0], [0.0, 0.0, 0.0], atol=1e-6)
        assert cp.allclose(lut[1, 0, 0], [1.0, 0.0, 0.0], atol=1e-6)
        assert cp.allclose(lut[0, 1, 0], [0.0, 1.0, 0.0], atol=1e-6)
        assert cp.allclose(lut[1, 1, 0], [1.0, 1.0, 0.0], atol=1e-6)
        assert cp.allclose(lut[0, 0, 1], [0.0, 0.0, 1.0], atol=1e-6)
        assert cp.allclose(lut[1, 0, 1], [1.0, 0.0, 1.0], atol=1e-6)
        assert cp.allclose(lut[0, 1, 1], [0.0, 1.0, 1.0], atol=1e-6)
        assert cp.allclose(lut[1, 1, 1], [1.0, 1.0, 1.0], atol=1e-6)

    def test_read_lut_32x32x32(self, sample_cube_file_32):
        """Test reading a 32x32x32 LUT (realistic size)"""
        lut = read_lut(sample_cube_file_32, use_cache=False)

        assert lut.shape == (32, 32, 32, 3)
        assert lut.dtype == cp.float32

        # Check gradient values
        assert cp.allclose(lut[0, 0, 0], [0.0, 0.0, 0.0], atol=1e-6)
        assert cp.allclose(lut[31, 31, 31], [1.0, 1.0, 1.0], atol=1e-6)
        assert cp.allclose(lut[16, 16, 16], [16 / 31, 16 / 31, 16 / 31], atol=1e-5)

    def test_read_lut_with_cache(self, sample_cube_file):
        """Test LUT caching functionality"""
        # First read (cache miss)
        lut1 = read_lut(sample_cube_file, use_cache=True)

        # Second read (cache hit)
        lut2 = read_lut(sample_cube_file, use_cache=True)

        # Results should be identical
        assert cp.allclose(lut1, lut2, atol=1e-6)

    def test_read_lut_no_cache(self, sample_cube_file):
        """Test reading without cache"""
        lut1 = read_lut(sample_cube_file, use_cache=False)
        lut2 = read_lut(sample_cube_file, use_cache=False)

        # Results should still be identical (just not cached)
        assert cp.allclose(lut1, lut2, atol=1e-6)

    def test_read_lut_file_not_found(self):
        """Test error handling for non-existent file"""
        with pytest.raises(FileNotFoundError):
            read_lut("nonexistent_file.cube")

    def test_read_lut_invalid_format(self):
        """Test error handling for invalid .cube format"""
        # Create file without LUT_3D_SIZE
        with tempfile.NamedTemporaryFile(mode="w", suffix=".cube", delete=False) as f:
            f.write("TITLE Test\n0.0 0.0 0.0\n")
            temp_path = f.name

        try:
            with pytest.raises(Exception):
                read_lut(temp_path, use_cache=False)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_read_lut_values_in_range(self, sample_cube_file_32):
        """Test that all LUT values are in valid range [0, 1]"""
        lut = read_lut(sample_cube_file_32, use_cache=False)

        assert cp.all(lut >= 0.0), "All LUT values should be >= 0.0"
        assert cp.all(lut <= 1.0), "All LUT values should be <= 1.0"


class TestApplyLut:
    """Test cases for apply_lut() function"""

    @pytest.fixture
    def identity_lut(self):
        """Create an identity LUT (8x8x8)"""
        size = 8
        lut = cp.zeros((size, size, size, 3), dtype=cp.float32)

        for z in range(size):
            for y in range(size):
                for x in range(size):
                    lut[x, y, z] = cp.array(
                        [x / (size - 1), y / (size - 1), z / (size - 1)],
                        dtype=cp.float32,
                    )

        return lut

    @pytest.fixture
    def sample_image(self):
        """Create a sample test image"""
        image = cp.zeros((256, 256, 3), dtype=cp.float32)
        # Create gradient
        for i in range(256):
            image[i, :, 0] = i / 255.0  # Red gradient
            image[:, i, 1] = i / 255.0  # Green gradient
        image[:, :, 2] = 0.5  # Constant blue
        return image

    def test_apply_lut_trilinear_basic(self, sample_image, identity_lut):
        """Test basic LUT application with trilinear interpolation"""
        result = apply_lut(sample_image, identity_lut, interpolation=0)

        assert isinstance(result, cp.ndarray)
        assert result.shape == sample_image.shape
        assert result.dtype == cp.float32

    def test_apply_lut_tetrahedral_basic(self, sample_image, identity_lut):
        """Test basic LUT application with tetrahedral interpolation"""
        result = apply_lut(sample_image, identity_lut, interpolation=1)

        assert isinstance(result, cp.ndarray)
        assert result.shape == sample_image.shape
        assert result.dtype == cp.float32

    def test_apply_lut_identity_preserves_image(self, sample_image, identity_lut):
        """Test that identity LUT preserves the original image"""
        result = apply_lut(sample_image, identity_lut, interpolation=0)

        # Identity LUT should not change the image (within interpolation tolerance)
        assert cp.allclose(result, sample_image, atol=0.05), "Identity LUT should preserve image"

    def test_apply_lut_trilinear_vs_tetrahedral(self, sample_image, identity_lut):
        """Test that both interpolation methods produce similar results for identity LUT"""
        result_trilinear = apply_lut(sample_image, identity_lut, interpolation=0)
        result_tetrahedral = apply_lut(sample_image, identity_lut, interpolation=1)

        # Both methods should be close for identity LUT
        assert cp.allclose(result_trilinear, result_tetrahedral, atol=0.05)

    def test_apply_lut_solid_color(self, identity_lut):
        """Test LUT on solid color image"""
        # Create red image
        image = cp.ones((128, 128, 3), dtype=cp.float32)
        image[:, :, 0] = 1.0
        image[:, :, 1] = 0.0
        image[:, :, 2] = 0.0

        result = apply_lut(image, identity_lut, interpolation=0)

        # Red should stay red with identity LUT
        assert cp.allclose(result[:, :, 0], 1.0, atol=0.05)
        assert cp.allclose(result[:, :, 1], 0.0, atol=0.05)
        assert cp.allclose(result[:, :, 2], 0.0, atol=0.05)

    def test_apply_lut_black_white(self, identity_lut):
        """Test LUT on black and white images"""
        # Black image
        black = cp.zeros((128, 128, 3), dtype=cp.float32)
        result_black = apply_lut(black, identity_lut, interpolation=0)
        assert cp.allclose(result_black, 0.0, atol=0.01)

        # White image
        white = cp.ones((128, 128, 3), dtype=cp.float32)
        result_white = apply_lut(white, identity_lut, interpolation=0)
        assert cp.allclose(result_white, 1.0, atol=0.01)

    def test_apply_lut_invert_lut(self, sample_image):
        """Test LUT that inverts colors"""
        size = 8
        invert_lut = cp.zeros((size, size, size, 3), dtype=cp.float32)

        # Create inverted LUT
        for z in range(size):
            for y in range(size):
                for x in range(size):
                    invert_lut[x, y, z] = cp.array(
                        [
                            1.0 - x / (size - 1),
                            1.0 - y / (size - 1),
                            1.0 - z / (size - 1),
                        ],
                        dtype=cp.float32,
                    )

        result = apply_lut(sample_image, invert_lut, interpolation=0)

        # Colors should be approximately inverted
        expected = 1.0 - sample_image
        assert cp.allclose(result, expected, atol=0.1)

    def test_apply_lut_grayscale_lut(self, sample_image):
        """Test LUT that converts to grayscale"""
        size = 8
        gray_lut = cp.zeros((size, size, size, 3), dtype=cp.float32)

        # Create grayscale LUT (average of RGB)
        for z in range(size):
            for y in range(size):
                for x in range(size):
                    avg = (x + y + z) / (3 * (size - 1))
                    gray_lut[x, y, z] = cp.array([avg, avg, avg], dtype=cp.float32)

        result = apply_lut(sample_image, gray_lut, interpolation=0)

        # All channels should be approximately equal
        assert cp.allclose(result[:, :, 0], result[:, :, 1], atol=0.1)
        assert cp.allclose(result[:, :, 1], result[:, :, 2], atol=0.1)

    def test_apply_lut_different_sizes(self, identity_lut):
        """Test LUT on different image sizes"""
        sizes = [(64, 64), (128, 256), (512, 512), (1920, 1080)]

        for h, w in sizes:
            image = cp.random.rand(h, w, 3).astype(cp.float32)
            result = apply_lut(image, identity_lut, interpolation=0)

            assert result.shape == (h, w, 3)

    def test_apply_lut_different_lut_sizes(self, sample_image):
        """Test different LUT sizes"""
        lut_sizes = [4, 8, 16, 32]

        for size in lut_sizes:
            # Create identity LUT of given size
            lut = cp.zeros((size, size, size, 3), dtype=cp.float32)
            for z in range(size):
                for y in range(size):
                    for x in range(size):
                        lut[x, y, z] = cp.array(
                            [x / (size - 1), y / (size - 1), z / (size - 1)],
                            dtype=cp.float32,
                        )

            result = apply_lut(sample_image, lut, interpolation=0)

            assert result.shape == sample_image.shape

    def test_apply_lut_output_range(self, sample_image, identity_lut):
        """Test that output values are in valid range"""
        result = apply_lut(sample_image, identity_lut, interpolation=0)

        # Values should stay in [0, 1] range (may slightly exceed due to interpolation)
        assert cp.all(result >= -0.01), "Output should be >= 0 (with small tolerance)"
        assert cp.all(result <= 1.01), "Output should be <= 1 (with small tolerance)"

    def test_apply_lut_uint8_input(self, identity_lut):
        """Test LUT with uint8 input (should be converted to float32)"""
        image_uint8 = (cp.random.rand(128, 128, 3) * 255).astype(cp.uint8)

        result = apply_lut(image_uint8, identity_lut, interpolation=0)

        assert result.dtype == cp.float32
        assert result.shape == (128, 128, 3)

    def test_apply_lut_large_image(self, identity_lut):
        """Test LUT on large image (4K)"""
        large_image = cp.random.rand(2160, 3840, 3).astype(cp.float32)

        result = apply_lut(large_image, identity_lut, interpolation=0)

        assert result.shape == (2160, 3840, 3)

    def test_apply_lut_extreme_values(self, identity_lut):
        """Test LUT with extreme input values"""
        # Image with values outside [0, 1]
        extreme_image = cp.array([[[2.0, -0.5, 1.5]]], dtype=cp.float32)
        extreme_image = cp.tile(extreme_image, (128, 128, 1))

        # Should not crash (values will be clamped or interpolated)
        result = apply_lut(extreme_image, identity_lut, interpolation=0)

        assert result.shape == extreme_image.shape


class TestLutIntegration:
    """Integration tests for LUT workflow"""

    def test_read_and_apply_workflow(self, tmp_path):
        """Test complete workflow: read LUT -> apply to image"""
        # Create temporary LUT file
        lut_path = tmp_path / "test.cube"
        cube_content = 'TITLE "Test"\nLUT_3D_SIZE 8\n\n'

        for z in range(8):
            for y in range(8):
                for x in range(8):
                    r = x / 7.0
                    g = y / 7.0
                    b = z / 7.0
                    cube_content += f"{r:.6f} {g:.6f} {b:.6f}\n"

        lut_path.write_text(cube_content)

        # Read LUT
        lut = read_lut(str(lut_path), use_cache=False)

        # Create test image
        image = cp.random.rand(256, 256, 3).astype(cp.float32)

        # Apply LUT
        result = apply_lut(image, lut, interpolation=0)

        assert result.shape == image.shape
        assert result.dtype == cp.float32

    def test_multiple_lut_applications(self):
        """Test applying multiple LUTs sequentially"""
        # Create identity LUT
        size = 8
        identity_lut = cp.zeros((size, size, size, 3), dtype=cp.float32)
        for z in range(size):
            for y in range(size):
                for x in range(size):
                    identity_lut[x, y, z] = cp.array(
                        [x / (size - 1), y / (size - 1), z / (size - 1)],
                        dtype=cp.float32,
                    )

        # Create test image
        image = cp.random.rand(256, 256, 3).astype(cp.float32)

        # Apply LUT twice
        result1 = apply_lut(image, identity_lut, interpolation=0)
        result2 = apply_lut(result1, identity_lut, interpolation=0)

        # Should be similar (identity LUT preserves image)
        assert cp.allclose(result1, result2, atol=0.1)

    def test_lut_cache_performance(self, tmp_path):
        """Test that LUT caching improves performance"""
        import time

        # Create LUT file
        lut_path = tmp_path / "cache_test.cube"
        cube_content = 'TITLE "Test"\nLUT_3D_SIZE 32\n\n'

        for z in range(32):
            for y in range(32):
                for x in range(32):
                    r = x / 31.0
                    g = y / 31.0
                    b = z / 31.0
                    cube_content += f"{r:.6f} {g:.6f} {b:.6f}\n"

        lut_path.write_text(cube_content)

        # First read (cache miss)
        start = time.time()
        lut1 = read_lut(str(lut_path), use_cache=True)
        time_no_cache = time.time() - start

        # Second read (cache hit)
        start = time.time()
        lut2 = read_lut(str(lut_path), use_cache=True)
        time_with_cache = time.time() - start

        # Cached read should be faster (or similar if very fast)
        assert time_with_cache <= time_no_cache * 2, "Cached read should not be slower"

        # Results should be identical
        assert cp.allclose(lut1, lut2, atol=1e-6)
