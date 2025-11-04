import cupy as cp
import cv2
import numpy as np

from ..constants import (
    IMWRITE_JPEG_QUALITY,
    IMWRITE_PNG_COMPRESSION,
    IMWRITE_TIFF_COMPRESSION,
)
from ..utils.dtypes import to_uint8, to_uint16


def _parse_params(params: list[int] | None) -> dict[int, int]:
    """Parse OpenCV-style params list into a dictionary.

    Parameters
    ----------
    params : list[int] | None
        OpenCV-style parameter list [param_id, value, param_id, value, ...]

    Returns
    -------
    dict[int, int]
        Dictionary mapping parameter ID to value
    """
    if params is None:
        return {}

    if len(params) % 2 != 0:
        raise ValueError(f"params must have even length (key-value pairs), got {len(params)}")

    return {params[i]: params[i + 1] for i in range(0, len(params), 2)}


def imencode(image: cp.ndarray, ext: str = ".png", params: list[int] | None = None) -> bytes:
    """Encode an image to bytes from a CuPy array.

    Parameters
    ----------
    image : cp.ndarray
        Input image as a CuPy array (BGR format)
    ext : str, optional
        Image format extension (e.g., ".png", ".jpg"), by default ".png"
    params : list[int] | None, optional
        OpenCV-style encoding parameters [param_id, value, ...], by default None
        Examples:
        - JPEG: [IMWRITE_JPEG_QUALITY, 95]
        - PNG: [IMWRITE_PNG_COMPRESSION, 9]
        - TIFF: [IMWRITE_TIFF_COMPRESSION, IMWRITE_TIFF_COMPRESSION_LZW]

    Returns
    -------
    bytes
        Encoded image as bytes

    Raises
    ------
    ValueError
        If unsupported format is specified
    RuntimeError
        If encoding fails

    Notes
    -----
    Input image should be in BGR format (OpenCV standard)
    """
    image = cp.asnumpy(image)
    param_dict = _parse_params(params)

    if "jpg" in ext.lower() or "jpeg" in ext.lower():
        # JPEG: default quality 100
        quality = param_dict.get(IMWRITE_JPEG_QUALITY, 100)
        image = to_uint8(image)

        # Build OpenCV options list
        options = [cv2.IMWRITE_JPEG_QUALITY, quality]

        # Add other JPEG parameters if present
        for key, value in param_dict.items():
            if key != IMWRITE_JPEG_QUALITY:  # Already added
                options.extend([key, value])

    elif "png" in ext.lower():
        # PNG: default compression 3
        compression = param_dict.get(IMWRITE_PNG_COMPRESSION, 3)
        if image.dtype != np.uint8:
            image = to_uint16(image)

        options = [cv2.IMWRITE_PNG_COMPRESSION, compression]

        # Add other PNG parameters if present
        for key, value in param_dict.items():
            if key != IMWRITE_PNG_COMPRESSION:  # Already added
                options.extend([key, value])

    elif "tiff" in ext.lower() or "tif" in ext.lower():
        # TIFF: default compression 5
        compression = param_dict.get(IMWRITE_TIFF_COMPRESSION, 5)
        if image.dtype != np.uint8:
            image = to_uint16(image)

        options = [cv2.IMWRITE_TIFF_COMPRESSION, compression]

        # Add other TIFF parameters if present
        for key, value in param_dict.items():
            if key != IMWRITE_TIFF_COMPRESSION:  # Already added
                options.extend([key, value])

    else:
        raise ValueError(f"Unsupported image format: {ext}. Supported formats: .jpg, .jpeg, .png, .tiff, .tif")

    success, encoded_image = cv2.imencode(ext.lower() if ext.startswith(".") else f".{ext.lower()}", image, options)
    if not success:
        raise RuntimeError(f"Failed to encode image to {ext} format")
    return encoded_image.tobytes()
