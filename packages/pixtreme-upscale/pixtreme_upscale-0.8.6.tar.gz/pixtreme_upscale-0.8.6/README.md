# pixtreme-upscale

Multi-backend deep learning upscalers for pixtreme

## Overview

`pixtreme-upscale` provides GPU-accelerated deep learning super-resolution with support for ONNX, PyTorch, and TensorRT backends. Integrates with Spandrel for automatic model architecture detection.

## Features

- **Multi-Backend Support**: ONNX Runtime, PyTorch, TensorRT
- **Automatic Tiling**: Handle large images with automatic tiling workflow
- **Model Conversion**: PyTorch → ONNX → TensorRT pipeline
- **Spandrel Integration**: Automatic architecture detection for 100+ models
- **Zero-Copy**: Direct GPU memory operations

## Installation

**Requirements**:
- Python >= 3.12
- CUDA Toolkit 12.x
- NVIDIA GPU with compute capability >= 6.0

```bash
# Base installation (ONNX + PyTorch)
pip install pixtreme-upscale

# With TensorRT support
pip install pixtreme-upscale[tensorrt]
```

Requires `pixtreme-core`, PyTorch, ONNX Runtime, and CUDA Toolkit 12.x.

## Quick Start

```python
import pixtreme_upscale as pu
import pixtreme_core as px

# Read image
img = px.imread("input.jpg")

# ONNX backend (fastest compatibility)
upscaler = pu.OnnxUpscaler("model.onnx")
upscaled = upscaler.get(img)

# PyTorch backend (most flexible)
upscaler = pu.TorchUpscaler("model.pth")
upscaled = upscaler.get(img)

# TensorRT backend (fastest performance)
upscaler = pu.TrtUpscaler("model.onnx")  # Auto-converts to TRT
upscaled = upscaler.get(img)

# Save result
px.imwrite("output.jpg", upscaled)
```

## Automatic Tiling

All upscalers automatically handle large images via tiling:

```python
# Automatically tiles large images
large_img = px.imread("8k_image.jpg")
upscaled = upscaler.get(large_img)  # Handles tiling internally
```

## Model Conversion

```python
from pixtreme_upscale.utils.model_convert import torch_to_onnx, onnx_to_trt

# PyTorch → ONNX
torch_to_onnx("model.pth", "model.onnx", input_shape=(1, 3, 1080, 1920))

# ONNX → TensorRT
onnx_to_trt("model.onnx", "model.trt", precision="fp16")
```

## Supported Models

Works with Spandrel-supported architectures:
- ESRGAN, Real-ESRGAN, RealESRGAN+
- SwinIR, HAT, OmniSR
- And 100+ more architectures

## License

MIT License - see LICENSE file for details.

## Links

- Repository: https://github.com/sync-dev-org/pixtreme
