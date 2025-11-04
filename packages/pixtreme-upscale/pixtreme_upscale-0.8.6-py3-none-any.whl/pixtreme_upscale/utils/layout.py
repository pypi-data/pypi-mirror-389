from typing import Literal

import cupy as cp

Layout = Literal["HW", "HWC", "CHW", "NHWC", "NCHW", "ambiguous", "unsupported"]


def guess_image_layout(image: cp.ndarray) -> Layout:
    """
    Infer the layout of an image array.

    Args:
        image (cp.ndarray): The input image array.
    Returns:
        Layout: The inferred layout of the image array.
    """
    nd = image.ndim
    # 2D: HW
    if nd == 2:
        return "HW"
    # 3D: HWC vs CHW
    elif nd == 3:
        c_first, c_last = image.shape[0], image.shape[-1]
        candidates = []
        if c_first in (1, 3, 4):
            candidates.append("CHW")
        if c_last in (1, 3, 4):
            candidates.append("HWC")
        # If candidates is one, return it
        if len(candidates) == 1:
            return candidates[0]
        # Tie-break: channel first vs channel last
        if c_first <= 4 and image.shape[1] > 4 and image.shape[2] > 4:
            return "CHW"
        if c_last <= 4 and image.shape[0] > 4 and image.shape[1] > 4:
            return "HWC"
        return "ambiguous"
    # 4D: NHWC vs NCHW
    elif nd == 4:
        # Candidate 1:  NCHW → (N, C, H, W)
        if image.shape[1] in (1, 3, 4) and image.shape[2] > 4 and image.shape[3] > 4:
            return "NCHW"
        # Candidate 2: NHWC → (N, H, W, C)
        if image.shape[-1] in (1, 3, 4) and image.shape[1] > 4 and image.shape[2] > 4:
            return "NHWC"
        return "ambiguous"
    else:
        return "unsupported"
