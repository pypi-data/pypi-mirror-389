"""Test suite for pixtreme_draw.text module (put_text, add_label)"""

import cupy as cp
import pytest

try:
    import cv2

    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

from pixtreme_draw import add_label, put_text

pytestmark = pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV (cv2) is required for text drawing")


class TestPutText:
    """Test cases for put_text() function"""

    def test_put_text_basic(self):
        """Test basic text drawing"""
        image = cp.zeros((512, 512, 3), dtype=cp.float32)
        result = put_text(image, text="Hello World", org=(50, 100))

        assert result is not None
        assert isinstance(result, cp.ndarray)

        # Text should modify some pixels
        diff = cp.sum(cp.abs(result - image))
        assert diff > 0, "Text should have been drawn"

    def test_put_text_returns_new_array(self):
        """Test that put_text returns a new array (not in-place)"""
        image = cp.zeros((512, 512, 3), dtype=cp.float32)
        result = put_text(image, text="Test", org=(50, 100))

        # Should return a different array object
        assert result is not image, "Should return new array, not modify in-place"

    def test_put_text_dtype_preserved(self):
        """Test that dtype is preserved"""
        image = cp.zeros((512, 512, 3), dtype=cp.float32)
        result = put_text(image, text="Test", org=(50, 100))

        assert result.dtype == cp.float32

    def test_put_text_shape_preserved(self):
        """Test that shape is preserved when density=1.0"""
        image = cp.zeros((512, 512, 3), dtype=cp.float32)
        result = put_text(image, text="Test", org=(50, 100), density=1.0)

        assert result.shape == image.shape

    def test_put_text_custom_color(self):
        """Test text with custom color"""
        image = cp.zeros((512, 512, 3), dtype=cp.float32)
        custom_color = (0.0, 1.0, 0.0)  # Green
        result = put_text(image, text="Green", org=(50, 100), color=custom_color)

        # Check that green channel has more values than others
        green_sum = cp.sum(result[:, :, 1])
        red_sum = cp.sum(result[:, :, 0])
        blue_sum = cp.sum(result[:, :, 2])

        assert green_sum > red_sum, "Green channel should dominate"
        assert green_sum > blue_sum, "Green channel should dominate"

    def test_put_text_large_font_scale(self):
        """Test with large font_scale=5.0"""
        image = cp.zeros((512, 512, 3), dtype=cp.float32)
        result = put_text(image, text="BIG", org=(50, 200), font_scale=5.0)

        # Large text should modify many pixels
        modified_pixels = cp.sum(result > 0)
        assert modified_pixels > 1000, f"Expected >1000 modified pixels, got {modified_pixels}"

    def test_put_text_small_font_scale(self):
        """Test with small font_scale=0.5"""
        image = cp.zeros((512, 512, 3), dtype=cp.float32)
        result = put_text(image, text="small", org=(50, 100), font_scale=0.5)

        # Small text should modify fewer pixels
        modified_pixels = cp.sum(result > 0)
        assert modified_pixels > 0, "Should have drawn some pixels"
        assert modified_pixels < 10000, "Small text should not modify too many pixels"

    def test_put_text_thick_text(self):
        """Test with thick text (thickness=10)"""
        image = cp.zeros((512, 512, 3), dtype=cp.float32)
        result = put_text(image, text="THICK", org=(50, 100), thickness=10)

        # Thick text should modify many pixels
        modified_pixels = cp.sum(result > 0)
        assert modified_pixels > 500, f"Thick text should modify many pixels, got {modified_pixels}"

    def test_put_text_different_fonts(self):
        """Test with different OpenCV fonts"""
        image = cp.zeros((512, 512, 3), dtype=cp.float32)

        # Test FONT_HERSHEY_SIMPLEX (default)
        result1 = put_text(image, text="Font1", org=(50, 100), font_face=cv2.FONT_HERSHEY_SIMPLEX)
        assert cp.any(result1 > 0)

        # Test FONT_HERSHEY_COMPLEX
        result2 = put_text(image, text="Font2", org=(50, 200), font_face=cv2.FONT_HERSHEY_COMPLEX)
        assert cp.any(result2 > 0)

        # Test FONT_HERSHEY_TRIPLEX
        result3 = put_text(image, text="Font3", org=(50, 300), font_face=cv2.FONT_HERSHEY_TRIPLEX)
        assert cp.any(result3 > 0)

    def test_put_text_density_2(self):
        """Test with density=2.0 (high-resolution rendering)"""
        image = cp.zeros((512, 512, 3), dtype=cp.float32)
        result = put_text(image, text="Smooth", org=(50, 100), density=2.0)

        # Should return same shape (upscaled then downscaled)
        assert result.shape == image.shape

        # Should produce smoother text
        assert cp.any(result > 0)

    def test_put_text_density_4(self):
        """Test with density=4.0 (very high-resolution rendering)"""
        image = cp.zeros((512, 512, 3), dtype=cp.float32)
        result = put_text(image, text="Very Smooth", org=(50, 100), density=4.0)

        assert result.shape == image.shape
        assert cp.any(result > 0)

    def test_put_text_empty_string(self):
        """Test with empty string"""
        image = cp.zeros((512, 512, 3), dtype=cp.float32)
        result = put_text(image, text="", org=(50, 100))

        # Should return array without modification (or minimal change)
        # Empty string draws nothing
        assert result.shape == image.shape

    def test_put_text_long_text(self):
        """Test with long text string"""
        image = cp.zeros((512, 512, 3), dtype=cp.float32)
        long_text = "This is a very long text string that might overflow"
        result = put_text(image, text=long_text, org=(10, 100), font_scale=0.8)

        # Should draw text (may extend beyond image)
        assert cp.any(result > 0)


class TestAddLabel:
    """Test cases for add_label() function"""

    def test_add_label_basic(self):
        """Test basic label addition"""
        image = cp.zeros((512, 512, 3), dtype=cp.float32)
        result = add_label(image, text="Label Text")

        assert result is not None
        assert isinstance(result, cp.ndarray)

    def test_add_label_increases_height(self):
        """Test that label increases image height by label_size"""
        image = cp.zeros((512, 512, 3), dtype=cp.float32)
        label_size = 50
        result = add_label(image, text="Label", label_size=label_size)

        # Height should increase by label_size
        expected_height = 512 + label_size
        assert result.shape[0] == expected_height, f"Expected height {expected_height}, got {result.shape[0]}"
        assert result.shape[1] == 512  # Width unchanged

    def test_add_label_dtype_preserved(self):
        """Test that dtype is preserved"""
        image = cp.zeros((512, 512, 3), dtype=cp.float32)
        result = add_label(image, text="Test")

        assert result.dtype == cp.float32

    def test_add_label_custom_label_size(self):
        """Test with custom label_size=50"""
        image = cp.zeros((256, 256, 3), dtype=cp.float32)
        result = add_label(image, text="Big Label", label_size=50)

        assert result.shape == (256 + 50, 256, 3)

    def test_add_label_custom_label_color(self):
        """Test with custom label background color"""
        image = cp.zeros((256, 256, 3), dtype=cp.float32)
        label_color = (1.0, 0.0, 0.0)  # Red background
        result = add_label(image, text="Red BG", label_size=30, label_color=label_color)

        # Check that label area has red background
        label_area = result[256:, :, :]  # Bottom label area
        red_channel = label_area[:, :, 0]

        # Most of red channel in label should be 1.0 (except text)
        red_ratio = cp.sum(red_channel > 0.9) / red_channel.size
        assert red_ratio > 0.5, f"Expected >50% red pixels in label, got {red_ratio * 100:.1f}%"

    def test_add_label_bottom_align(self):
        """Test with bottom alignment (default)"""
        image = cp.zeros((256, 256, 3), dtype=cp.float32)
        result = add_label(image, text="Bottom", label_align="bottom", label_size=30)

        assert result.shape == (256 + 30, 256, 3)

    def test_add_label_top_align(self):
        """Test with top alignment"""
        image = cp.zeros((256, 256, 3), dtype=cp.float32)
        result = add_label(image, text="Top", label_align="top", label_size=30)

        assert result.shape == (256 + 30, 256, 3)

    def test_add_label_custom_text_color(self):
        """Test with custom text color"""
        image = cp.zeros((256, 256, 3), dtype=cp.float32)
        text_color = (0.0, 0.0, 1.0)  # Blue text
        result = add_label(image, text="Blue Text", color=text_color, label_size=30)

        # Check that blue channel has values in label area
        label_area = result[256:, :, :]
        blue_sum = cp.sum(label_area[:, :, 2])

        assert blue_sum > 0, "Blue channel should have text"

    def test_add_label_calls_put_text(self):
        """Test that add_label internally uses put_text"""
        # This is an integration test to verify the workflow
        image = cp.zeros((256, 256, 3), dtype=cp.float32)
        result = add_label(image, text="Integration Test", label_size=40)

        # Should have label area with text
        label_area = result[256:, :, :]

        # Text should be drawn (some pixels modified)
        assert cp.any(label_area > 0), "Text should be drawn in label area"

    def test_add_label_density_2(self):
        """Test with density=2.0"""
        image = cp.zeros((256, 256, 3), dtype=cp.float32)
        result = add_label(image, text="Smooth Label", density=2.0, label_size=30)

        assert result.shape == (256 + 30, 256, 3)
        assert cp.any(result > 0)

    def test_add_label_empty_text(self):
        """Test with empty text"""
        image = cp.zeros((256, 256, 3), dtype=cp.float32)
        result = add_label(image, text="", label_size=30)

        # Should still add label box (even if empty)
        assert result.shape == (256 + 30, 256, 3)

    def test_add_label_large_label_size(self):
        """Test with label_size larger than image height"""
        image = cp.zeros((100, 100, 3), dtype=cp.float32)
        result = add_label(image, text="Huge Label", label_size=200)

        # Should still work (label box dominates)
        assert result.shape == (100 + 200, 100, 3)

    def test_add_label_preserves_original_image(self):
        """Test that original image content is preserved"""
        image = cp.ones((256, 256, 3), dtype=cp.float32) * 0.5  # Gray image
        result = add_label(image, text="Label", label_size=30)

        # Original image area should be unchanged
        original_area = result[:256, :, :]
        assert cp.allclose(original_area, 0.5, atol=1e-6), "Original image should be preserved"

    def test_add_label_font_parameters(self):
        """Test with custom font parameters"""
        image = cp.zeros((256, 256, 3), dtype=cp.float32)
        result = add_label(
            image,
            text="Custom Font",
            font_face=cv2.FONT_HERSHEY_COMPLEX,
            font_scale=1.5,
            thickness=3,
            label_size=50,
        )

        assert result.shape == (256 + 50, 256, 3)
        assert cp.any(result > 0)
