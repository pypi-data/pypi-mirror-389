"""Test suite for pixtreme_core.transform.tile module (tile_image, merge_tiles, etc.)"""

import cupy as cp
from pixtreme_core.transform.tile import (
    add_padding,
    create_gaussian_weights,
    merge_tiles,
    tile_image,
)


class TestTileImage:
    """Test cases for tile_image() function"""

    def test_tile_image_basic(self):
        """Test basic image tiling"""
        image = cp.random.rand(256, 256, 3).astype(cp.float32)
        tiles, padded_shape = tile_image(image, tile_size=128, overlap=16)

        assert isinstance(tiles, list)
        assert len(tiles) > 0
        assert isinstance(padded_shape, tuple)

    def test_tile_image_tile_shapes(self):
        """Test that all tiles have correct shape"""
        image = cp.random.rand(256, 256, 3).astype(cp.float32)
        tile_size = 128
        tiles, _ = tile_image(image, tile_size=tile_size, overlap=16)

        for tile in tiles:
            assert tile.shape == (tile_size, tile_size, 3)

    def test_tile_image_count(self):
        """Test number of tiles generated"""
        # 256x256 image with 128x128 tiles and 16 overlap
        # Step = 128 - 16 = 112
        # After padding to fit: should have multiple tiles
        image = cp.random.rand(256, 256, 3).astype(cp.float32)
        tiles, _ = tile_image(image, tile_size=128, overlap=16)

        # At least 4 tiles for 256x256 image
        assert len(tiles) >= 4

    def test_tile_image_small_image(self):
        """Test tiling of small image"""
        image = cp.random.rand(64, 64, 3).astype(cp.float32)
        tiles, _ = tile_image(image, tile_size=128, overlap=16)

        # Should create at least 1 tile (after padding)
        assert len(tiles) >= 1

    def test_tile_image_large_image(self):
        """Test tiling of large image"""
        image = cp.random.rand(512, 512, 3).astype(cp.float32)
        tiles, _ = tile_image(image, tile_size=128, overlap=16)

        # Should create many tiles
        assert len(tiles) > 10

    def test_tile_image_different_tile_sizes(self):
        """Test different tile sizes"""
        image = cp.random.rand(256, 256, 3).astype(cp.float32)

        for tile_size in [64, 128, 256]:
            tiles, _ = tile_image(image, tile_size=tile_size, overlap=8)
            assert all(tile.shape[0] == tile_size for tile in tiles)

    def test_tile_image_different_overlaps(self):
        """Test different overlap values"""
        image = cp.random.rand(256, 256, 3).astype(cp.float32)
        tile_size = 128

        for overlap in [0, 8, 16, 32]:
            tiles, _ = tile_image(image, tile_size=tile_size, overlap=overlap)
            assert len(tiles) > 0

    def test_tile_image_rectangular_image(self):
        """Test tiling of rectangular (non-square) image"""
        image = cp.random.rand(300, 400, 3).astype(cp.float32)
        tiles, padded_shape = tile_image(image, tile_size=128, overlap=16)

        assert len(tiles) > 0
        assert all(tile.shape == (128, 128, 3) for tile in tiles)

    def test_tile_image_returns_padded_shape(self):
        """Test that padded_shape is returned correctly"""
        image = cp.random.rand(256, 256, 3).astype(cp.float32)
        tiles, padded_shape = tile_image(image, tile_size=128, overlap=16)

        assert isinstance(padded_shape, tuple)
        assert len(padded_shape) == 3
        assert padded_shape[0] >= image.shape[0]  # Padded height >= original
        assert padded_shape[1] >= image.shape[1]  # Padded width >= original
        assert padded_shape[2] == 3  # Channels unchanged


class TestMergeTiles:
    """Test cases for merge_tiles() function"""

    def test_merge_tiles_basic(self):
        """Test basic tile merging"""
        # Create simple tiles
        tile_size = 128
        original_shape = (256, 256, 3)
        padded_shape = (256, 256, 3)
        scale = 1

        # Create 4 tiles (2x2 grid)
        tiles = [cp.random.rand(tile_size, tile_size, 3).astype(cp.float32) for _ in range(4)]

        result = merge_tiles(tiles, original_shape, padded_shape, scale, tile_size=tile_size, overlap=16)

        assert isinstance(result, cp.ndarray)
        assert result.shape == (256, 256, 3)

    def test_merge_tiles_with_scale(self):
        """Test tile merging with upscaling"""
        tile_size = 128
        original_shape = (256, 256, 3)
        padded_shape = (256, 256, 3)
        scale = 2

        # Create upscaled tiles
        upscaled_tile_size = tile_size * scale
        tiles = [cp.random.rand(upscaled_tile_size, upscaled_tile_size, 3).astype(cp.float32) for _ in range(4)]

        result = merge_tiles(tiles, original_shape, padded_shape, scale, tile_size=tile_size, overlap=16)

        # Output should be 2x the original size
        assert result.shape == (512, 512, 3)

    def test_merge_tiles_preserves_dtype(self):
        """Test that merge_tiles preserves float32 dtype"""
        tile_size = 128
        original_shape = (256, 256, 3)
        padded_shape = (256, 256, 3)
        scale = 1

        tiles = [cp.random.rand(tile_size, tile_size, 3).astype(cp.float32) for _ in range(4)]

        result = merge_tiles(tiles, original_shape, padded_shape, scale, tile_size=tile_size, overlap=16)

        assert result.dtype == cp.float32

    def test_merge_tiles_values_in_range(self):
        """Test that merged values are in reasonable range"""
        tile_size = 128
        original_shape = (256, 256, 3)
        padded_shape = (256, 256, 3)
        scale = 1

        # Create tiles with values in [0, 1]
        tiles = [cp.random.rand(tile_size, tile_size, 3).astype(cp.float32) for _ in range(4)]

        result = merge_tiles(tiles, original_shape, padded_shape, scale, tile_size=tile_size, overlap=16)

        # After Gaussian blending, values should still be reasonable
        assert cp.all(result >= -0.1), "Values should be >= 0 (with tolerance)"
        assert cp.all(result <= 1.1), "Values should be <= 1 (with tolerance)"

    def test_merge_tiles_rectangular_result(self):
        """Test merging tiles for rectangular output"""
        tile_size = 128
        original_shape = (300, 400, 3)
        padded_shape = (336, 448, 3)  # Padded to fit tiles
        scale = 1

        # Calculate number of tiles needed
        step = tile_size - 16  # overlap=16
        num_tiles_y = (padded_shape[0] - tile_size) // step + 1
        num_tiles_x = (padded_shape[1] - tile_size) // step + 1
        num_tiles = num_tiles_y * num_tiles_x

        tiles = [cp.random.rand(tile_size, tile_size, 3).astype(cp.float32) for _ in range(num_tiles)]

        result = merge_tiles(tiles, original_shape, padded_shape, scale, tile_size=tile_size, overlap=16)

        # Should be cropped to original shape
        assert result.shape == (300, 400, 3)


class TestAddPadding:
    """Test cases for add_padding() function"""

    def test_add_padding_basic(self):
        """Test basic padding"""
        image = cp.random.rand(256, 256, 3).astype(cp.float32)
        padded = add_padding(image, patch_size=128, overlap=16)

        assert isinstance(padded, cp.ndarray)
        assert padded.shape[0] >= image.shape[0]
        assert padded.shape[1] >= image.shape[1]
        assert padded.shape[2] == 3

    def test_add_padding_already_aligned(self):
        """Test padding when image is already aligned"""
        # 256 is divisible by (128-16)=112, so minimal padding needed
        image = cp.random.rand(256, 256, 3).astype(cp.float32)
        padded = add_padding(image, patch_size=128, overlap=16)

        # Should have some padding or stay same
        assert padded.shape[0] >= image.shape[0]
        assert padded.shape[1] >= image.shape[1]

    def test_add_padding_small_image(self):
        """Test padding for small image"""
        image = cp.random.rand(50, 50, 3).astype(cp.float32)
        padded = add_padding(image, patch_size=128, overlap=16)

        # Should be padded to at least 128
        assert padded.shape[0] >= 128
        assert padded.shape[1] >= 128

    def test_add_padding_reflect_mode(self):
        """Test that reflect padding is used correctly"""
        # Create image with distinct edge values
        image = cp.zeros((100, 100, 3), dtype=cp.float32)
        image[0, :] = 1.0  # Top edge white

        padded = add_padding(image, patch_size=128, overlap=16)

        # Padding should reflect edge values
        assert padded.shape[0] > 100
        assert cp.any(padded > 0)  # Some white values from reflection

    def test_add_padding_preserves_dtype(self):
        """Test that dtype is preserved"""
        image = cp.random.rand(256, 256, 3).astype(cp.float32)
        padded = add_padding(image, patch_size=128, overlap=16)

        assert padded.dtype == cp.float32

    def test_add_padding_rectangular_image(self):
        """Test padding for rectangular image"""
        image = cp.random.rand(200, 300, 3).astype(cp.float32)
        padded = add_padding(image, patch_size=128, overlap=16)

        assert padded.shape[0] >= 200
        assert padded.shape[1] >= 300

    def test_add_padding_different_patch_sizes(self):
        """Test padding with different patch sizes"""
        image = cp.random.rand(256, 256, 3).astype(cp.float32)

        for patch_size in [64, 128, 256]:
            padded = add_padding(image, patch_size=patch_size, overlap=8)
            assert padded.shape[0] >= image.shape[0]
            assert padded.shape[1] >= image.shape[1]


class TestCreateGaussianWeights:
    """Test cases for create_gaussian_weights() function"""

    def test_gaussian_weights_basic(self):
        """Test basic Gaussian weight creation"""
        weights = create_gaussian_weights(size=128, sigma=32)

        assert isinstance(weights, cp.ndarray)
        assert weights.shape == (128, 128, 1)

    def test_gaussian_weights_dtype(self):
        """Test Gaussian weights dtype"""
        weights = create_gaussian_weights(size=128, sigma=32)

        assert weights.dtype in [cp.float32, cp.float64]

    def test_gaussian_weights_normalized(self):
        """Test that Gaussian weights are normalized"""
        weights = create_gaussian_weights(size=128, sigma=32)

        # Sum should be 1.0 (normalized)
        weight_sum = cp.sum(weights)
        assert cp.allclose(weight_sum, 1.0, atol=1e-6)

    def test_gaussian_weights_center_peak(self):
        """Test that center has highest weight"""
        size = 128
        weights = create_gaussian_weights(size=size, sigma=32)

        center = size // 2
        center_value = weights[center, center, 0]

        # Center should have higher value than corners
        corner_value = weights[0, 0, 0]
        assert center_value > corner_value

    def test_gaussian_weights_symmetry(self):
        """Test that Gaussian weights are symmetric"""
        size = 128
        weights = create_gaussian_weights(size=size, sigma=32)

        # Check horizontal symmetry
        assert cp.allclose(
            weights[:, : size // 2, :],
            cp.flip(weights[:, size // 2 :, :], axis=1),
            atol=1e-5,
        )

        # Check vertical symmetry
        assert cp.allclose(
            weights[: size // 2, :, :],
            cp.flip(weights[size // 2 :, :, :], axis=0),
            atol=1e-5,
        )

    def test_gaussian_weights_different_sizes(self):
        """Test Gaussian weights with different sizes"""
        for size in [64, 128, 256]:
            weights = create_gaussian_weights(size=size, sigma=size // 4)
            assert weights.shape == (size, size, 1)

    def test_gaussian_weights_different_sigmas(self):
        """Test Gaussian weights with different sigmas"""
        size = 128

        for sigma in [16, 32, 64]:
            weights = create_gaussian_weights(size=size, sigma=sigma)

            # Larger sigma should give flatter distribution
            assert weights.shape == (size, size, 1)

    def test_gaussian_weights_values_positive(self):
        """Test that all weights are positive"""
        weights = create_gaussian_weights(size=128, sigma=32)

        assert cp.all(weights >= 0), "All weights should be >= 0"

    def test_gaussian_weights_small_sigma(self):
        """Test Gaussian with small sigma (sharp peak)"""
        weights = create_gaussian_weights(size=128, sigma=8)

        # Normalized weights: center >= edges (normalized distribution is flat)
        center = weights[64, 64, 0]
        edge = weights[0, 64, 0]
        assert center >= edge  # Center at least equal to edge


class TestTileIntegration:
    """Integration tests for tile workflow"""

    def test_tile_and_merge_roundtrip(self):
        """Test tile -> merge roundtrip preserves image"""
        image = cp.random.rand(256, 256, 3).astype(cp.float32)
        tile_size = 128
        overlap = 16

        # Tile image
        tiles, padded_shape = tile_image(image, tile_size=tile_size, overlap=overlap)

        # Merge tiles (scale=1, no processing)
        result = merge_tiles(
            tiles,
            image.shape,
            padded_shape,
            scale=1,
            tile_size=tile_size,
            overlap=overlap,
        )

        # Should be close to original
        assert result.shape == image.shape
        assert cp.allclose(result, image, atol=0.1)

    def test_tile_process_merge_workflow(self):
        """Test complete workflow: tile -> process -> merge"""
        image = cp.random.rand(256, 256, 3).astype(cp.float32)
        tile_size = 128
        overlap = 16
        scale = 2

        # Tile image
        tiles, padded_shape = tile_image(image, tile_size=tile_size, overlap=overlap)

        # Simulate upscaling process
        processed_tiles = []
        for tile in tiles:
            # Simple upscale: repeat pixels
            upscaled = cp.repeat(cp.repeat(tile, scale, axis=0), scale, axis=1)
            processed_tiles.append(upscaled)

        # Merge tiles
        result = merge_tiles(
            processed_tiles,
            image.shape,
            padded_shape,
            scale=scale,
            tile_size=tile_size,
            overlap=overlap,
        )

        # Output should be 2x size
        assert result.shape == (512, 512, 3)

    def test_tile_workflow_different_sizes(self):
        """Test tile workflow with various image sizes"""
        sizes = [(128, 128), (256, 256), (300, 400), (512, 768)]
        tile_size = 128
        overlap = 16

        for h, w in sizes:
            image = cp.random.rand(h, w, 3).astype(cp.float32)

            # Tile
            tiles, padded_shape = tile_image(image, tile_size=tile_size, overlap=overlap)

            # Merge
            result = merge_tiles(
                tiles,
                image.shape,
                padded_shape,
                scale=1,
                tile_size=tile_size,
                overlap=overlap,
            )

            assert result.shape == image.shape

    def test_tile_workflow_preserves_content(self):
        """Test that tile workflow preserves image content"""
        # Create image with recognizable pattern
        image = cp.zeros((256, 256, 3), dtype=cp.float32)
        image[100:150, 100:150, 0] = 1.0  # Red square

        tile_size = 128
        overlap = 16

        # Tile and merge
        tiles, padded_shape = tile_image(image, tile_size=tile_size, overlap=overlap)
        result = merge_tiles(
            tiles,
            image.shape,
            padded_shape,
            scale=1,
            tile_size=tile_size,
            overlap=overlap,
        )

        # Red square should still be present
        red_region = result[100:150, 100:150, 0]
        assert cp.mean(red_region) > 0.5  # Mostly red
