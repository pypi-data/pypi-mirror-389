"""pixtreme-upscale: Multi-backend deep learning upscalers"""

__version__ = "0.8.6"

from .onnx_upscaler import OnnxUpscaler
from .torch_upscaler import TorchUpscaler
from .trt_upscaler import TrtUpscaler
from .utils.layout import Layout, guess_image_layout
from .utils.model_convert import (
    check_onnx_model,
    check_torch_model,
    check_trt_model,
    onnx_to_onnx_dynamic,
    onnx_to_trt,
    onnx_to_trt_dynamic_shape,
    onnx_to_trt_fixed_shape,
    torch_to_onnx,
)

__all__ = [
    # Upscaler classes
    "OnnxUpscaler",
    "TorchUpscaler",
    "TrtUpscaler",
    # Layout utilities
    "Layout",
    "guess_image_layout",
    # Model conversion utilities
    "check_onnx_model",
    "check_torch_model",
    "check_trt_model",
    "onnx_to_onnx_dynamic",
    "onnx_to_trt",
    "onnx_to_trt_dynamic_shape",
    "onnx_to_trt_fixed_shape",
    "torch_to_onnx",
]
