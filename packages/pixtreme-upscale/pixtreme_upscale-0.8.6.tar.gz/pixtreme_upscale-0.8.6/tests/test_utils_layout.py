"""
Test suite for pixtreme_upscale.utils.layout module.

Tests the guess_image_layout() function with various array shapes.
"""

import cupy as cp
import pytest
from pixtreme_upscale.utils.layout import guess_image_layout


class TestGuessImageLayout:
    """Test guess_image_layout() function."""

    def test_layout_2d_hw(self):
        """Test 2D array (H, W) -> 'HW'."""
        image = cp.zeros((100, 200), dtype=cp.float32)
        result = guess_image_layout(image)
        assert result == "HW", f"Expected 'HW', got '{result}'"

    def test_layout_3d_hwc_typical(self):
        """Test 3D array (H, W, C) with typical channel count -> 'HWC'."""
        # (H=100, W=200, C=3)
        image = cp.zeros((100, 200, 3), dtype=cp.float32)
        result = guess_image_layout(image)
        assert result == "HWC", f"Expected 'HWC', got '{result}'"

    def test_layout_3d_hwc_grayscale(self):
        """Test 3D array (H, W, 1) -> 'HWC'."""
        image = cp.zeros((100, 200, 1), dtype=cp.float32)
        result = guess_image_layout(image)
        assert result == "HWC", f"Expected 'HWC', got '{result}'"

    def test_layout_3d_hwc_rgba(self):
        """Test 3D array (H, W, 4) -> 'HWC'."""
        image = cp.zeros((100, 200, 4), dtype=cp.float32)
        result = guess_image_layout(image)
        assert result == "HWC", f"Expected 'HWC', got '{result}'"

    def test_layout_3d_chw_typical(self):
        """Test 3D array (C, H, W) with typical channel count -> 'CHW'."""
        # (C=3, H=100, W=200)
        image = cp.zeros((3, 100, 200), dtype=cp.float32)
        result = guess_image_layout(image)
        assert result == "CHW", f"Expected 'CHW', got '{result}'"

    def test_layout_3d_chw_grayscale(self):
        """Test 3D array (1, H, W) -> 'CHW'."""
        image = cp.zeros((1, 100, 200), dtype=cp.float32)
        result = guess_image_layout(image)
        assert result == "CHW", f"Expected 'CHW', got '{result}'"

    def test_layout_3d_chw_rgba(self):
        """Test 3D array (4, H, W) -> 'CHW'."""
        image = cp.zeros((4, 100, 200), dtype=cp.float32)
        result = guess_image_layout(image)
        assert result == "CHW", f"Expected 'CHW', got '{result}'"

    def test_layout_3d_ambiguous_square(self):
        """Test 3D array (3, 3, 3) -> 'ambiguous'."""
        # All dimensions are 3, cannot distinguish HWC vs CHW
        image = cp.zeros((3, 3, 3), dtype=cp.float32)
        result = guess_image_layout(image)
        assert result == "ambiguous", f"Expected 'ambiguous', got '{result}'"

    def test_layout_3d_chw_small(self):
        """Test 3D array (C, H, W) with small dimensions -> 'CHW'."""
        # (3, 2, 2) - 3 channels, 2x2 image → CHW
        image = cp.zeros((3, 2, 2), dtype=cp.float32)
        result = guess_image_layout(image)
        assert result == "CHW", f"Expected 'CHW', got '{result}'"

    def test_layout_4d_nchw_typical(self):
        """Test 4D array (N, C, H, W) -> 'NCHW'."""
        # (N=2, C=3, H=100, W=200)
        image = cp.zeros((2, 3, 100, 200), dtype=cp.float32)
        result = guess_image_layout(image)
        assert result == "NCHW", f"Expected 'NCHW', got '{result}'"

    def test_layout_4d_nchw_grayscale(self):
        """Test 4D array (N, 1, H, W) -> 'NCHW'."""
        image = cp.zeros((2, 1, 100, 200), dtype=cp.float32)
        result = guess_image_layout(image)
        assert result == "NCHW", f"Expected 'NCHW', got '{result}'"

    def test_layout_4d_nchw_rgba(self):
        """Test 4D array (N, 4, H, W) -> 'NCHW'."""
        image = cp.zeros((2, 4, 100, 200), dtype=cp.float32)
        result = guess_image_layout(image)
        assert result == "NCHW", f"Expected 'NCHW', got '{result}'"

    def test_layout_4d_nhwc_typical(self):
        """Test 4D array (N, H, W, C) -> 'NHWC'."""
        # (N=2, H=100, W=200, C=3)
        image = cp.zeros((2, 100, 200, 3), dtype=cp.float32)
        result = guess_image_layout(image)
        assert result == "NHWC", f"Expected 'NHWC', got '{result}'"

    def test_layout_4d_nhwc_grayscale(self):
        """Test 4D array (N, H, W, 1) -> 'NHWC'."""
        image = cp.zeros((2, 100, 200, 1), dtype=cp.float32)
        result = guess_image_layout(image)
        assert result == "NHWC", f"Expected 'NHWC', got '{result}'"

    def test_layout_4d_nhwc_rgba(self):
        """Test 4D array (N, H, W, 4) -> 'NHWC'."""
        image = cp.zeros((2, 100, 200, 4), dtype=cp.float32)
        result = guess_image_layout(image)
        assert result == "NHWC", f"Expected 'NHWC', got '{result}'"

    def test_layout_4d_ambiguous_square(self):
        """Test 4D array (2, 3, 3, 3) -> 'ambiguous'."""
        # Small H/W dimensions, cannot distinguish
        image = cp.zeros((2, 3, 3, 3), dtype=cp.float32)
        result = guess_image_layout(image)
        assert result == "ambiguous", f"Expected 'ambiguous', got '{result}'"

    def test_layout_4d_ambiguous_batch_channels(self):
        """Test 4D array with ambiguous batch/channel dims -> 'ambiguous'."""
        # (4, 3, 2, 2) - too small H/W to determine
        image = cp.zeros((4, 3, 2, 2), dtype=cp.float32)
        result = guess_image_layout(image)
        assert result == "ambiguous", f"Expected 'ambiguous', got '{result}'"

    def test_layout_unsupported_5d(self):
        """Test 5D array -> 'unsupported'."""
        image = cp.zeros((2, 3, 100, 200, 3), dtype=cp.float32)
        result = guess_image_layout(image)
        assert result == "unsupported", f"Expected 'unsupported', got '{result}'"

    def test_layout_unsupported_1d(self):
        """Test 1D array -> 'unsupported'."""
        image = cp.zeros((100,), dtype=cp.float32)
        result = guess_image_layout(image)
        assert result == "unsupported", f"Expected 'unsupported', got '{result}'"

    def test_layout_type_annotation(self):
        """Test that Layout type includes all expected values."""
        # This is a compile-time check, but we can verify the literal values
        expected_values = {
            "HW",
            "HWC",
            "CHW",
            "NHWC",
            "NCHW",
            "ambiguous",
            "unsupported",
        }

        # Test each expected layout value
        test_cases = [
            ((100, 200), "HW"),
            ((100, 200, 3), "HWC"),
            ((3, 100, 200), "CHW"),
            ((2, 100, 200, 3), "NHWC"),
            ((2, 3, 100, 200), "NCHW"),
            ((3, 3, 3), "ambiguous"),
            ((2, 3, 4, 5, 6), "unsupported"),
        ]

        results = {guess_image_layout(cp.zeros(shape, dtype=cp.float32)) for shape, _ in test_cases}
        assert results == expected_values, f"Layout values mismatch: {results} vs {expected_values}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
