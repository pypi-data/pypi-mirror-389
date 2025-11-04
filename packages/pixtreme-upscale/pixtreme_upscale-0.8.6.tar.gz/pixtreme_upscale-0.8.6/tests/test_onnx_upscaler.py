"""
Test suite for OnnxUpscaler.

Simple E2E test with a single image.
"""

import os

import cupy as cp
import pixtreme as px
import pytest


def test_onnx_upscaler():
    """Test OnnxUpscaler with a single image."""
    device_id = 0
    model_path = "sandbox/models/4xNomosUni_span_multijpg.onnx"
    image_path = "sandbox/example.png"

    # Skip test if model or image not found
    if not os.path.exists(model_path):
        pytest.skip(f"Model not found: {model_path}")
    if not os.path.exists(image_path):
        pytest.skip(f"Image not found: {image_path}")

    with px.Device(device_id):
        # Load image
        image = px.imread(image_path)
        image = px.to_float32(image)

        # Initialize upscaler
        upscaler = px.OnnxUpscaler(model_path=model_path, device_id=device_id)

        # Upscale
        upscaled = upscaler.get(image)

        # Verify output shape (4x upscale)
        h, w, c = image.shape
        expected_shape = (h * 4, w * 4, c)
        assert upscaled.shape == expected_shape, f"Expected shape {expected_shape}, got {upscaled.shape}"

        # Verify dtype (allow fp16 output from fp16 models)
        assert upscaled.dtype in (image.dtype, cp.float16)

        print(f"\nInput: {image.shape} -> Output: {upscaled.shape}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
