"""Test suite for pixtreme_draw.shape module (circle, rectangle)"""

import cupy as cp
from pixtreme_draw import circle, rectangle


class TestCircle:
    """Test cases for circle() function"""

    def test_circle_basic(self):
        """Test basic circle drawing"""
        image = cp.zeros((512, 512, 3), dtype=cp.float32)
        result = circle(image, center_x=256, center_y=256, radius=100)

        # Check that result is the same object (in-place operation)
        assert result is image

        # Check that some pixels are white (circle drawn)
        assert cp.any(result > 0), "Circle should have drawn some pixels"

        # Check center pixel is white
        assert cp.allclose(result[256, 256], [1.0, 1.0, 1.0])

    def test_circle_returns_same_array(self):
        """Test that circle modifies array in-place"""
        image = cp.zeros((512, 512, 3), dtype=cp.float32)
        original_id = id(image)
        result = circle(image, 256, 256, 50)

        assert id(result) == original_id, "Should return same array object"

    def test_circle_dtype_preserved(self):
        """Test that dtype is preserved"""
        image = cp.zeros((512, 512, 3), dtype=cp.float32)
        result = circle(image, 256, 256, 50)

        assert result.dtype == cp.float32

    def test_circle_custom_color(self):
        """Test circle with custom color"""
        image = cp.zeros((512, 512, 3), dtype=cp.float32)
        custom_color = (0.5, 0.2, 0.8)
        circle(image, 256, 256, 50, color=custom_color)

        # Check center pixel has custom color
        assert cp.allclose(image[256, 256], custom_color, atol=1e-6)

    def test_circle_small_radius(self):
        """Test circle with radius=1"""
        image = cp.zeros((100, 100, 3), dtype=cp.float32)
        circle(image, 50, 50, radius=1)

        # Should draw at least the center pixel
        assert cp.any(image > 0)
        assert cp.allclose(image[50, 50], [1.0, 1.0, 1.0])

    def test_circle_large_radius(self):
        """Test circle with large radius"""
        image = cp.zeros((1024, 1024, 3), dtype=cp.float32)
        circle(image, 512, 512, radius=500)

        # Check that large area is drawn
        white_pixels = cp.sum(image[:, :, 0] > 0.5)
        # Approximate area: π * r^2 ≈ 785,000 pixels
        assert white_pixels > 700000, f"Expected ~785k white pixels, got {white_pixels}"

    def test_circle_zero_radius(self):
        """Test circle with radius=0"""
        image = cp.zeros((100, 100, 3), dtype=cp.float32)
        circle(image, 50, 50, radius=0)

        # radius=0 should draw nothing or just center pixel
        # Implementation may vary, just check no error
        assert image.shape == (100, 100, 3)

    def test_circle_center_at_origin(self):
        """Test circle with center at (0, 0)"""
        image = cp.zeros((100, 100, 3), dtype=cp.float32)
        circle(image, center_x=0, center_y=0, radius=20)

        # Should draw quarter circle in top-left
        assert cp.any(image > 0)
        assert cp.allclose(image[0, 0], [1.0, 1.0, 1.0])

    def test_circle_center_outside_image(self):
        """Test circle with center outside image bounds"""
        image = cp.zeros((100, 100, 3), dtype=cp.float32)
        circle(image, center_x=-50, center_y=-50, radius=100)

        # Should draw partial circle (bottom-right quarter)
        # Check that some pixels near origin are drawn
        assert cp.any(image[:20, :20] > 0), "Should draw partial circle"

    def test_circle_partial_overlap(self):
        """Test circle partially overlapping image"""
        image = cp.zeros((100, 100, 3), dtype=cp.float32)
        circle(image, center_x=90, center_y=50, radius=20)

        # Should draw partial circle on right edge
        assert cp.any(image[:, 90:] > 0), "Should draw on right edge"

    def test_circle_multiple_circles(self):
        """Test drawing multiple circles"""
        image = cp.zeros((512, 512, 3), dtype=cp.float32)

        # Draw 3 circles
        circle(image, 100, 100, 30, color=(1.0, 0.0, 0.0))
        circle(image, 200, 200, 30, color=(0.0, 1.0, 0.0))
        circle(image, 300, 300, 30, color=(0.0, 0.0, 1.0))

        # Check each circle's center
        assert cp.allclose(image[100, 100], [1.0, 0.0, 0.0], atol=1e-6)
        assert cp.allclose(image[200, 200], [0.0, 1.0, 0.0], atol=1e-6)
        assert cp.allclose(image[300, 300], [0.0, 0.0, 1.0], atol=1e-6)

    def test_circle_overlapping(self):
        """Test overlapping circles (last one wins)"""
        image = cp.zeros((200, 200, 3), dtype=cp.float32)

        # Draw two overlapping circles
        circle(image, 100, 100, 50, color=(1.0, 0.0, 0.0))
        circle(image, 120, 100, 50, color=(0.0, 1.0, 0.0))

        # Overlapping region should have second color
        assert cp.allclose(image[100, 110], [0.0, 1.0, 0.0], atol=1e-6)


class TestRectangle:
    """Test cases for rectangle() function"""

    def test_rectangle_basic(self):
        """Test basic rectangle drawing"""
        image = cp.zeros((512, 512, 3), dtype=cp.float32)
        result = rectangle(
            image,
            top_left_x=100,
            top_left_y=100,
            bottom_right_x=400,
            bottom_right_y=400,
        )

        # Check that result is the same object (in-place operation)
        assert result is image

        # Check that rectangle is drawn
        assert cp.any(result > 0)

        # Check a pixel inside rectangle is white
        assert cp.allclose(result[200, 200], [1.0, 1.0, 1.0])

    def test_rectangle_returns_same_array(self):
        """Test that rectangle modifies array in-place"""
        image = cp.zeros((512, 512, 3), dtype=cp.float32)
        original_id = id(image)
        result = rectangle(image, 100, 100, 400, 400)

        assert id(result) == original_id, "Should return same array object"

    def test_rectangle_dtype_preserved(self):
        """Test that dtype is preserved"""
        image = cp.zeros((512, 512, 3), dtype=cp.float32)
        result = rectangle(image, 100, 100, 400, 400)

        assert result.dtype == cp.float32

    def test_rectangle_custom_color(self):
        """Test rectangle with custom color"""
        image = cp.zeros((512, 512, 3), dtype=cp.float32)
        custom_color = (0.3, 0.6, 0.9)
        rectangle(image, 100, 100, 200, 200, color=custom_color)

        # Check pixel inside rectangle
        assert cp.allclose(image[150, 150], custom_color, atol=1e-6)

    def test_rectangle_small_rect(self):
        """Test 1x1 rectangle"""
        image = cp.zeros((100, 100, 3), dtype=cp.float32)
        rectangle(image, 50, 50, 51, 51)

        # Should draw 1x1 pixel
        assert cp.allclose(image[50, 50], [1.0, 1.0, 1.0])
        # Adjacent pixels should be black
        assert cp.allclose(image[49, 50], [0.0, 0.0, 0.0])
        assert cp.allclose(image[51, 50], [0.0, 0.0, 0.0])

    def test_rectangle_full_image(self):
        """Test rectangle covering entire image"""
        image = cp.zeros((100, 100, 3), dtype=cp.float32)
        rectangle(image, 0, 0, 100, 100, color=(0.5, 0.5, 0.5))

        # All pixels should be gray
        assert cp.all(image == 0.5), "All pixels should be filled"

    def test_rectangle_negative_coords(self):
        """Test rectangle with negative coordinates"""
        image = cp.zeros((100, 100, 3), dtype=cp.float32)
        rectangle(image, -20, -20, 30, 30)

        # Should draw partial rectangle (bottom-right corner)
        assert cp.any(image[:30, :30] > 0)
        assert cp.allclose(image[10, 10], [1.0, 1.0, 1.0])

    def test_rectangle_zero_size(self):
        """Test rectangle with zero width or height"""
        image = cp.zeros((100, 100, 3), dtype=cp.float32)

        # Zero width
        rectangle(image, 50, 20, 50, 80)
        # Should draw nothing or a line (implementation dependent)

        # Zero height
        rectangle(image, 20, 50, 80, 50)
        # Should draw nothing or a line (implementation dependent)

        # Just check no error occurs
        assert image.shape == (100, 100, 3)

    def test_rectangle_inverted_coords(self):
        """Test rectangle with inverted coordinates (top_left > bottom_right)"""
        image = cp.zeros((100, 100, 3), dtype=cp.float32)
        rectangle(image, top_left_x=80, top_left_y=80, bottom_right_x=20, bottom_right_y=20)

        # Implementation may draw nothing or handle differently
        # Just ensure no crash
        assert image.shape == (100, 100, 3)

    def test_rectangle_outside_image(self):
        """Test rectangle completely outside image bounds"""
        image = cp.zeros((100, 100, 3), dtype=cp.float32)
        rectangle(image, 200, 200, 300, 300)

        # Should draw nothing
        assert cp.all(image == 0.0), "No pixels should be drawn"

    def test_rectangle_multiple_rectangles(self):
        """Test drawing multiple rectangles"""
        image = cp.zeros((512, 512, 3), dtype=cp.float32)

        # Draw 3 rectangles
        rectangle(image, 50, 50, 150, 150, color=(1.0, 0.0, 0.0))
        rectangle(image, 200, 200, 300, 300, color=(0.0, 1.0, 0.0))
        rectangle(image, 350, 350, 450, 450, color=(0.0, 0.0, 1.0))

        # Check each rectangle's center
        assert cp.allclose(image[100, 100], [1.0, 0.0, 0.0], atol=1e-6)
        assert cp.allclose(image[250, 250], [0.0, 1.0, 0.0], atol=1e-6)
        assert cp.allclose(image[400, 400], [0.0, 0.0, 1.0], atol=1e-6)

    def test_rectangle_overlapping(self):
        """Test overlapping rectangles (last one wins)"""
        image = cp.zeros((200, 200, 3), dtype=cp.float32)

        # Draw two overlapping rectangles
        rectangle(image, 50, 50, 150, 150, color=(1.0, 0.0, 0.0))
        rectangle(image, 100, 100, 180, 180, color=(0.0, 1.0, 0.0))

        # Overlapping region should have second color
        assert cp.allclose(image[120, 120], [0.0, 1.0, 0.0], atol=1e-6)

        # Non-overlapping part of first rectangle should have first color
        assert cp.allclose(image[60, 60], [1.0, 0.0, 0.0], atol=1e-6)
