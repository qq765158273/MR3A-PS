"""Convert browser screenshots to MaaFramework's BGR image format."""

import io

import numpy as np
from PIL import Image


def png_to_bgr(data: bytes) -> np.ndarray:
    with Image.open(io.BytesIO(data)) as image:
        rgb = np.asarray(image.convert("RGB"), dtype=np.uint8)
    return np.ascontiguousarray(rgb[:, :, ::-1])
