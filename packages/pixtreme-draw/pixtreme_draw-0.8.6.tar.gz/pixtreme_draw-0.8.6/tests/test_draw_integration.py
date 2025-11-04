"""Integration tests for pixtreme_draw package"""

import importlib.util

import cupy as cp
import numpy as np
import pytest
from pixtreme_draw import add_label, circle, create_rounded_mask, put_text, rectangle

CV2_AVAILABLE = importlib.util.find_spec("cv2") is not None


class TestDrawIntegration:
    """Integration tests combining multiple drawing functions"""

    def test_draw_all_shapes_on_image(self):
        """Test drawing multiple shapes on same image"""
        image = cp.zeros((512, 512, 3), dtype=cp.float32)

        # Draw circles
        circle(image, 100, 100, 50, color=(1.0, 0.0, 0.0))
        circle(image, 400, 100, 50, color=(0.0, 1.0, 0.0))

        # Draw rectangles
        rectangle(image, 150, 200, 350, 300, color=(0.0, 0.0, 1.0))
        rectangle(image, 200, 350, 300, 450, color=(1.0, 1.0, 0.0))

        # Verify all shapes drawn
        assert cp.allclose(image[100, 100], [1.0, 0.0, 0.0], atol=1e-6)  # Red circle
        assert cp.allclose(image[100, 400], [0.0, 1.0, 0.0], atol=1e-6)  # Green circle
        assert cp.allclose(image[250, 250], [0.0, 0.0, 1.0], atol=1e-6)  # Blue rectangle
        assert cp.allclose(image[400, 250], [1.0, 1.0, 0.0], atol=1e-6)  # Yellow rectangle

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV required")
    def test_create_ui_mockup(self):
        """Test creating a complete UI mockup with mask, shapes, and text"""
        # Create base image
        image = cp.ones((512, 512, 3), dtype=cp.float32) * 0.3  # Dark gray background

        # Add rounded mask overlay
        mask = create_rounded_mask(dsize=(512, 512), mask_offsets=(0.1, 0.1, 0.1, 0.1), radius_ratio=0.05)

        # Blend mask with image
        image = image * (1 - mask) + mask * cp.array([0.8, 0.8, 0.8], dtype=cp.float32)

        # Draw UI elements
        circle(image, 100, 100, 30, color=(0.2, 0.6, 1.0))  # Blue button
        rectangle(image, 200, 80, 450, 120, color=(0.0, 0.8, 0.0))  # Green button

        # Add text labels
        image = put_text(image, text="UI Mockup", org=(50, 50), font_scale=1.0, color=(1.0, 1.0, 1.0))

        # Add bottom label
        result = add_label(image, text="Status: Ready", label_size=40, label_color=(0.2, 0.2, 0.2))

        # Verify final dimensions
        assert result.shape == (512 + 40, 512, 3)
        assert result.dtype == cp.float32

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV required")
    def test_draw_dashboard(self):
        """Test creating a complex dashboard layout"""
        # Create 4K canvas
        image = cp.zeros((1080, 1920, 3), dtype=cp.float32)

        # Draw header bar
        rectangle(image, 0, 0, 1920, 100, color=(0.1, 0.1, 0.3))

        # Draw title
        image = put_text(
            image,
            text="Dashboard",
            org=(50, 70),
            font_scale=2.0,
            color=(1.0, 1.0, 1.0),
            thickness=3,
        )

        # Draw 4 metric boxes
        colors = [(1.0, 0.3, 0.3), (0.3, 1.0, 0.3), (0.3, 0.3, 1.0), (1.0, 1.0, 0.3)]
        positions = [
            (50, 150, 450, 450),
            (500, 150, 900, 450),
            (950, 150, 1350, 450),
            (1400, 150, 1800, 450),
        ]

        for color, (x1, y1, x2, y2) in zip(colors, positions):
            rectangle(image, x1, y1, x2, y2, color=color)
            # Draw indicator circle
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2
            circle(image, cx, cy, 50, color=(1.0, 1.0, 1.0))

        # Verify dashboard created
        assert image.shape == (1080, 1920, 3)
        assert cp.any(image > 0)

    def test_imread_draw_imwrite_simulation(self):
        """Test drawing pipeline with simulated I/O"""
        # Simulate imread (create test image)
        image = cp.random.rand(512, 512, 3).astype(cp.float32) * 0.5

        # Draw annotations
        circle(image, 256, 256, 100, color=(1.0, 0.0, 0.0))
        rectangle(image, 100, 100, 200, 200, color=(0.0, 1.0, 0.0))

        # Simulate imwrite (convert to uint8 range)
        output = (cp.clip(image, 0, 1) * 255).astype(cp.uint8)

        assert output.shape == (512, 512, 3)
        assert output.dtype == cp.uint8

    def test_draw_with_resize_simulation(self):
        """Test drawing integrated with resize operation"""
        # Create small image
        small_image = cp.zeros((256, 256, 3), dtype=cp.float32)

        # Draw on small image
        circle(small_image, 128, 128, 50, color=(1.0, 0.0, 0.0))
        rectangle(small_image, 50, 50, 100, 100, color=(0.0, 1.0, 0.0))

        # Simulate resize (simple nearest neighbor for testing)
        # In real usage, would use pixtreme_core.transform.resize
        large_image = cp.repeat(cp.repeat(small_image, 2, axis=0), 2, axis=1)

        assert large_image.shape == (512, 512, 3)

    def test_draw_1000_circles_performance(self):
        """Test performance with large number of circles"""
        import time

        image = cp.zeros((2048, 2048, 3), dtype=cp.float32)

        start_time = time.time()

        # Draw 1000 circles
        for i in range(1000):
            x = (i * 17) % 2048
            y = (i * 23) % 2048
            radius = 10
            color = (i % 3 == 0, i % 3 == 1, i % 3 == 2)
            circle(image, x, y, radius, color=color)

        elapsed = time.time() - start_time

        # Should complete in reasonable time (< 5 seconds)
        assert elapsed < 5.0, f"Drawing 1000 circles took {elapsed:.2f}s (expected < 5s)"

        # Verify circles drawn
        assert cp.any(image > 0)

    def test_draw_large_image_4k(self):
        """Test drawing on 4K image"""
        image = cp.zeros((2160, 3840, 3), dtype=cp.float32)  # 4K UHD

        # Draw large shapes
        circle(image, 1920, 1080, 500, color=(1.0, 0.0, 0.0))
        rectangle(image, 1000, 500, 2840, 1660, color=(0.0, 0.0, 1.0))

        assert image.shape == (2160, 3840, 3)
        assert cp.any(image > 0)

    def test_draw_numpy_input(self):
        """Test drawing with NumPy array input (should work)"""
        # Create NumPy array
        image_np = np.zeros((256, 256, 3), dtype=np.float32)

        # Convert to CuPy for drawing (pixtreme_draw expects CuPy)
        image_cp = cp.asarray(image_np)

        # Draw on CuPy array
        circle(image_cp, 128, 128, 50, color=(1.0, 0.0, 0.0))

        # Convert back to NumPy
        result_np = cp.asnumpy(image_cp)

        assert isinstance(result_np, np.ndarray)
        assert result_np.shape == (256, 256, 3)
        assert np.any(result_np > 0)

    def test_draw_mixed_operations(self):
        """Test mixing NumPy and CuPy operations"""
        # Start with NumPy
        image_np = np.zeros((512, 512, 3), dtype=np.float32)

        # Convert to CuPy for drawing
        image_cp = cp.asarray(image_np)

        # Draw shapes
        circle(image_cp, 256, 256, 100, color=(1.0, 0.0, 0.0))

        # Convert back to NumPy for processing
        image_np = cp.asnumpy(image_cp)

        # Apply NumPy operation (brightness adjustment)
        image_np = np.clip(image_np * 1.2, 0, 1)

        # Convert back to CuPy for more drawing
        image_cp = cp.asarray(image_np)
        rectangle(image_cp, 100, 100, 400, 400, color=(0.0, 1.0, 0.0))

        assert isinstance(image_cp, cp.ndarray)
        assert cp.any(image_cp > 0)

    def test_draw_grayscale_image(self):
        """Test drawing on grayscale image (should work with broadcasting)"""
        # Create grayscale image (H, W, 3) but all channels same
        image = cp.zeros((256, 256, 3), dtype=cp.float32)
        image[:, :] = 0.5  # Gray background

        # Draw colored shapes
        circle(image, 128, 128, 50, color=(1.0, 0.0, 0.0))

        assert image.shape == (256, 256, 3)
        assert cp.allclose(image[128, 128], [1.0, 0.0, 0.0], atol=1e-6)

    @pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV required")
    def test_complete_annotation_workflow(self):
        """Test complete annotation workflow: image -> draw -> label"""
        # Create test image
        image = cp.ones((512, 512, 3), dtype=cp.float32) * 0.5

        # Draw bounding box
        rectangle(image, 150, 150, 350, 350, color=(0.0, 1.0, 0.0))

        # Draw keypoints
        keypoints = [(200, 200), (300, 200), (250, 300)]
        for x, y in keypoints:
            circle(image, x, y, 5, color=(1.0, 0.0, 0.0))

        # Add detection label
        image = put_text(
            image,
            text="Object: 0.95",
            org=(160, 140),
            font_scale=0.6,
            color=(1.0, 1.0, 1.0),
        )

        # Add bottom status label
        result = add_label(image, text="Detections: 1", label_size=30, label_color=(0.1, 0.1, 0.1))

        # Verify complete workflow
        assert result.shape == (512 + 30, 512, 3)
        assert cp.any(result > 0)

    def test_mask_composition(self):
        """Test compositing multiple masks"""
        # Create two rounded masks
        mask1 = create_rounded_mask(dsize=(512, 512), mask_offsets=(0.1, 0.1, 0.1, 0.1), radius_ratio=0.1)

        mask2 = create_rounded_mask(dsize=(512, 512), mask_offsets=(0.2, 0.2, 0.05, 0.05), radius_ratio=0.15)

        # Composite masks (multiply for intersection)
        composed = mask1 * mask2

        assert composed.shape == (512, 512, 3)
        assert cp.all(composed >= 0.0) and cp.all(composed <= 1.0)

    def test_draw_with_alpha_blending_simulation(self):
        """Test alpha blending simulation with shapes"""
        # Create base image
        base = cp.ones((512, 512, 3), dtype=cp.float32) * 0.3

        # Create overlay image
        overlay = cp.zeros((512, 512, 3), dtype=cp.float32)
        circle(overlay, 256, 256, 100, color=(1.0, 0.0, 0.0))

        # Alpha blend (50% opacity)
        alpha = 0.5
        result = base * (1 - alpha) + overlay * alpha

        assert result.shape == (512, 512, 3)
        assert cp.all(result >= 0.0) and cp.all(result <= 1.0)
