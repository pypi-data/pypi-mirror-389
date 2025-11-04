import os

import cupy as cp
import Imath
import OpenEXR
from nvidia import nvimgcodec

from ..color.bgr import rgb_to_bgr
from ..utils.dtypes import to_float16, to_float32, to_uint8, to_uint16


def imread(input_path: str, dtype: str = "fp32") -> cp.ndarray:
    """
    Read an image from a file into a CuPy array.

    Parameters
    ----------
    input_path : str
        Path to the image file
    dtype : str, optional
        Desired data type ("fp32", "fp16", "uint8", "uint16"), by default "fp32"

    Returns
    -------
    cp.ndarray
        Image as a CuPy array in BGR format (OpenCV standard)

    Raises
    ------
    FileNotFoundError
        If the image file does not exist
    RuntimeError
        If image decoding fails

    Notes
    -----
    - Returns images in BGR format (OpenCV standard)
    - Uses nvimgcodec for JPEG/PNG/TIFF (GPU-accelerated)
    - Uses OpenEXR library for EXR format
    - Grayscale images are converted to 3-channel BGR
    - Alpha channel is removed if present
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Image not found at {input_path}")

    filename, ext = os.path.splitext(input_path)
    ext = ext.lower()

    if ext in [".exr"]:
        # EXR format: Use OpenEXR library
        image_exr = OpenEXR.InputFile(input_path)

        # Determine pixel type
        r_header = image_exr.header()["channels"]["R"]
        if "HALF" in str(r_header):
            pixeltype = Imath.PixelType(Imath.PixelType.HALF)
            dtype = "float16"
        else:
            pixeltype = Imath.PixelType(Imath.PixelType.FLOAT)
            dtype = "float32"
        r_str, g_str, b_str = image_exr.channels("RGB", pixeltype)

        # Convert to CuPy array
        red: cp.ndarray = cp.frombuffer(r_str, dtype=dtype)
        green: cp.ndarray = cp.frombuffer(g_str, dtype=dtype)
        blue: cp.ndarray = cp.frombuffer(b_str, dtype=dtype)
        dw = image_exr.header()["dataWindow"]
        size = (dw.max.x - dw.min.x + 1, dw.max.y - dw.min.y + 1)

        # OpenEXR stores RGB, convert to BGR
        image: cp.ndarray = cp.dstack([blue, green, red])
        image = image.reshape(size[1], size[0], 3)

    else:
        # Non-EXR formats: Use nvimgcodec (GPU-accelerated)
        # nvimgcodec v0.6.0+ API: pass path directly to decoder.read()
        decoder = nvimgcodec.Decoder()
        nv_image = decoder.read(input_path)  # RGB
        if nv_image is None:
            raise RuntimeError(f"Failed to read image from {input_path}")
        image = cp.asarray(nv_image)

        if len(image.shape) == 2:
            # Grayscale: Convert to 3-channel BGR
            image = cp.stack([image] * 3, axis=-1)
        elif image.shape[2] == 4:
            # Remove alpha channel
            image = image[:, :, :3]

        # nvimgcodec returns RGB, convert to BGR
        image = rgb_to_bgr(image)

    if dtype == "fp32":
        image = to_float32(image)
    elif dtype == "uint8":
        image = to_uint8(image)
    elif dtype == "uint16":
        image = to_uint16(image)
    elif dtype == "fp16":
        image = to_float16(image)

    return image
