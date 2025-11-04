import cupy as cp
import cv2
import numpy as np

from ..utils.dtypes import to_float16, to_float32, to_uint8, to_uint16


def imdecode(src: bytes, dtype: str = "fp32") -> cp.ndarray:
    """
    Decode an image from a bytes object into a CuPy array.

    Parameters
    ----------
    src : bytes
        Input image data as bytes
    dtype : str, optional
        Desired data type ("fp32", "fp16", "uint8", "uint16"), by default "fp32"

    Returns
    -------
    cp.ndarray
        Image as a CuPy array in BGR format (OpenCV standard)

    Raises
    ------
    RuntimeError
        If image decoding fails

    Notes
    -----
    - Returns images in BGR format (OpenCV standard)
    - Uses OpenCV's imdecode for memory decoding
    """
    # Decode the image from the bytes object
    image = cv2.imdecode(np.frombuffer(src, np.uint8), cv2.IMREAD_UNCHANGED)
    if image is None:
        raise RuntimeError("Failed to decode image from bytes")

    image = cp.asarray(image)

    if dtype == "fp32":
        image = to_float32(image)
    elif dtype == "uint8":
        image = to_uint8(image)
    elif dtype == "uint16":
        image = to_uint16(image)
    elif dtype == "fp16":
        image = to_float16(image)
    else:
        image = to_float32(image)

    return image
