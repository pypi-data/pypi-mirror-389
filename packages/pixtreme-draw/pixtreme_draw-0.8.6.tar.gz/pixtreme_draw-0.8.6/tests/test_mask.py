"""Test suite for pixtreme_draw.mask module (create_rounded_mask)"""

import cupy as cp
from pixtreme_draw import create_rounded_mask


class TestCreateRoundedMask:
    """Test cases for create_rounded_mask() function"""

    def test_rounded_mask_default_params(self):
        """Test with default parameters"""
        result = create_rounded_mask()

        assert result is not None
        assert isinstance(result, cp.ndarray)

    def test_rounded_mask_output_shape(self):
        """Test that output shape matches dsize parameter"""
        dsize = (256, 512)  # (height, width)
        result = create_rounded_mask(dsize=dsize)

        # Output shape should be (H, W, 3)
        assert result.shape == (
            256,
            512,
            3,
        ), f"Expected (256, 512, 3), got {result.shape}"

    def test_rounded_mask_output_dtype(self):
        """Test that output dtype is float32"""
        result = create_rounded_mask()

        assert result.dtype == cp.float32

    def test_rounded_mask_channels(self):
        """Test that output has 3 channels"""
        result = create_rounded_mask()

        assert result.shape[2] == 3, "Should have 3 channels"

    def test_rounded_mask_custom_size(self):
        """Test with custom size (1024, 768)"""
        result = create_rounded_mask(dsize=(1024, 768))

        assert result.shape == (1024, 768, 3)

    def test_rounded_mask_small_size(self):
        """Test with small size (64, 64)"""
        result = create_rounded_mask(dsize=(64, 64))

        assert result.shape == (64, 64, 3)

    def test_rounded_mask_large_offsets(self):
        """Test with large offsets (creates smaller rounded rectangle)"""
        result = create_rounded_mask(dsize=(512, 512), mask_offsets=(0.3, 0.3, 0.3, 0.3))

        # Check that center is white (inside rounded rect)
        assert cp.any(result[256, 256] > 0.5), "Center should be inside mask"

        # Check that corners are black (outside rounded rect)
        assert cp.all(result[10, 10] < 0.5), "Corner should be outside mask"

    def test_rounded_mask_zero_offsets(self):
        """Test with zero offsets (rounded rect covers entire image)"""
        result = create_rounded_mask(dsize=(256, 256), mask_offsets=(0.0, 0.0, 0.0, 0.0))

        # Most of the image should be white
        white_ratio = cp.sum(result[:, :, 0] > 0.5) / (256 * 256)
        assert white_ratio > 0.7, f"Expected >70% white pixels, got {white_ratio * 100:.1f}%"

    def test_rounded_mask_large_radius(self):
        """Test with large radius ratio (very round corners)"""
        result = create_rounded_mask(dsize=(512, 512), radius_ratio=0.5)

        # Should create very round shape
        assert result.shape == (512, 512, 3)

    def test_rounded_mask_zero_radius(self):
        """Test with zero radius (sharp corners)"""
        result = create_rounded_mask(dsize=(512, 512), radius_ratio=0.0)

        # Should create sharp-cornered rectangle
        assert result.shape == (512, 512, 3)

    def test_rounded_mask_density_1(self):
        """Test with density=1 (no anti-aliasing)"""
        result = create_rounded_mask(dsize=(256, 256), density=1)

        assert result.shape == (256, 256, 3)

        # With density=1, edges might be more aliased
        # Just verify it produces output
        assert cp.any(result > 0)

    def test_rounded_mask_density_2(self):
        """Test with density=2 (2x anti-aliasing)"""
        result = create_rounded_mask(dsize=(256, 256), density=2)

        assert result.shape == (256, 256, 3)

        # Higher density should produce smoother edges
        # (visual verification not possible in unit test)
        assert cp.any(result > 0)

    def test_rounded_mask_density_4(self):
        """Test with density=4 (4x anti-aliasing)"""
        result = create_rounded_mask(dsize=(256, 256), density=4)

        assert result.shape == (256, 256, 3)
        assert cp.any(result > 0)

    def test_rounded_mask_blur_size_10(self):
        """Test with blur_size=10 (blur applied)"""
        result = create_rounded_mask(dsize=(256, 256), blur_size=10, sigma=2.0)

        assert result.shape == (256, 256, 3)

        # Blur should create gradual transitions
        # Edges should have intermediate values (not just 0 or 1)
        assert cp.any((result > 0.1) & (result < 0.9)), "Should have blurred edges"

    def test_rounded_mask_no_blur(self):
        """Test with blur_size=0 (no blur)"""
        result = create_rounded_mask(dsize=(256, 256), blur_size=0)

        assert result.shape == (256, 256, 3)

        # Without blur, edges should be sharper
        # (still anti-aliased if density > 1)
        assert cp.any(result > 0)

    def test_rounded_mask_values_in_range(self):
        """Test that all values are in range [0.0, 1.0]"""
        result = create_rounded_mask(dsize=(512, 512))

        assert cp.all(result >= 0.0), "All values should be >= 0.0"
        assert cp.all(result <= 1.0), "All values should be <= 1.0"

    def test_rounded_mask_integration_dependencies(self):
        """Test that rounded mask uses circle and rectangle correctly"""
        # This test verifies the integration behavior
        # The function should call circle() and rectangle() internally

        result = create_rounded_mask(
            dsize=(512, 512),
            mask_offsets=(0.1, 0.1, 0.1, 0.1),
            radius_ratio=0.1,
            density=1,
            blur_size=0,
        )

        # Verify basic properties
        assert result.shape == (512, 512, 3)

        # Check that center area is white (filled by rectangles)
        center_value = result[256, 256, 0]
        assert center_value > 0.9, f"Center should be white, got {center_value}"

        # Check that rounded corners exist (filled by circles)
        # Top-left corner should have rounded edge
        # Calculate expected corner position
        offset_px = int(512 * 0.1)
        radius_px = int(0.1 * 512)

        # Point inside rounded corner (top-left)
        corner_x = offset_px + radius_px
        corner_y = offset_px + radius_px
        corner_value = result[corner_y, corner_x, 0]
        assert corner_value > 0.9, f"Corner center should be white, got {corner_value}"

    def test_rounded_mask_rectangular_size(self):
        """Test with non-square size"""
        result = create_rounded_mask(dsize=(300, 800))  # Wide rectangle

        assert result.shape == (300, 800, 3)
        assert cp.any(result > 0)

    def test_rounded_mask_asymmetric_offsets(self):
        """Test with asymmetric offsets"""
        result = create_rounded_mask(dsize=(512, 512), mask_offsets=(0.05, 0.15, 0.25, 0.35))

        assert result.shape == (512, 512, 3)

        # Mask should be shifted toward top-left
        # More space on bottom-right
        assert cp.any(result > 0)
