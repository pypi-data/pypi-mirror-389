import os

import cupy as cp
import cv2
import Imath
import numpy as np
import OpenEXR

try:
    import torch

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None  # type: ignore

from ..color.bgr import bgr_to_rgb
from ..constants import (
    IMWRITE_EXR_COMPRESSION,
    IMWRITE_EXR_COMPRESSION_B44,
    IMWRITE_EXR_COMPRESSION_B44A,
    IMWRITE_EXR_COMPRESSION_DWAA,
    IMWRITE_EXR_COMPRESSION_DWAB,
    IMWRITE_EXR_COMPRESSION_NONE,
    IMWRITE_EXR_COMPRESSION_PIZ,
    IMWRITE_EXR_COMPRESSION_PXR24,
    IMWRITE_EXR_COMPRESSION_RLE,
    IMWRITE_EXR_COMPRESSION_ZIP,
    IMWRITE_EXR_COMPRESSION_ZIPS,
    IMWRITE_EXR_TYPE,
    IMWRITE_EXR_TYPE_FLOAT,
    IMWRITE_EXR_TYPE_HALF,
    IMWRITE_JPEG_QUALITY,
    IMWRITE_PNG_COMPRESSION,
    IMWRITE_TIFF_COMPRESSION,
)
from ..utils.dlpack import to_numpy
from ..utils.dtypes import to_float16, to_float32, to_uint8, to_uint16


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

    Examples
    --------
    >>> _parse_params([IMWRITE_JPEG_QUALITY, 95, IMWRITE_JPEG_PROGRESSIVE, 1])
    {1: 95, 2: 1}
    """
    if params is None:
        return {}

    if len(params) % 2 != 0:
        raise ValueError(f"params must have even length (key-value pairs), got {len(params)}")

    return {params[i]: params[i + 1] for i in range(0, len(params), 2)}


def imwrite(output_path: str, image: cp.ndarray | np.ndarray, params: list[int] | None = None) -> bool:
    """Write an image to a file.

    Parameters
    ----------
    output_path : str
        Path to the output image file
    image : cp.ndarray | np.ndarray
        Image array (BGR format for OpenCV compatibility)
    params : list[int] | None, optional
        OpenCV-style encoding parameters [param_id, value, ...], by default None
        Examples:
        - JPEG: [IMWRITE_JPEG_QUALITY, 95]
        - PNG: [IMWRITE_PNG_COMPRESSION, 9, IMWRITE_PNG_FILTER, IMWRITE_PNG_FILTER_PAETH]
        - TIFF: [IMWRITE_TIFF_COMPRESSION, IMWRITE_TIFF_COMPRESSION_LZW]
        - EXR: [IMWRITE_EXR_COMPRESSION, IMWRITE_EXR_COMPRESSION_PIZ, IMWRITE_EXR_TYPE, IMWRITE_EXR_TYPE_FLOAT]

    Returns
    -------
    bool
        True if write succeeded

    Notes
    -----
    - Input image should be in BGR format (OpenCV standard)
    - For RGB images, convert with `bgr_to_rgb()` before calling
    - EXR format: Converts BGR to RGB automatically
    """
    filename, ext = os.path.splitext(output_path)
    ext = ext.lower()

    if isinstance(image, cp.ndarray):
        image = to_numpy(image)
    elif TORCH_AVAILABLE and isinstance(image, torch.Tensor):
        image = to_numpy(image)

    param_dict = _parse_params(params)

    if ext == ".exr":
        # EXR always uses RGB
        image_rgb = bgr_to_rgb(image)

        # Get compression type
        compression_type = param_dict.get(IMWRITE_EXR_COMPRESSION, IMWRITE_EXR_COMPRESSION_DWAA)

        # Get pixel type (HALF or FLOAT)
        exr_type = param_dict.get(IMWRITE_EXR_TYPE, IMWRITE_EXR_TYPE_HALF)

        if exr_type == IMWRITE_EXR_TYPE_FLOAT:
            image_exr = to_float32(image_rgb)
            pixel_type = Imath.PixelType(Imath.PixelType.FLOAT)
        else:  # IMWRITE_EXR_TYPE_HALF
            image_exr = to_float16(image_rgb)
            pixel_type = Imath.PixelType(Imath.PixelType.HALF)

        # Create header
        header = OpenEXR.Header(image_exr.shape[1], image_exr.shape[0])

        # Set compression
        if compression_type == IMWRITE_EXR_COMPRESSION_NONE:
            header["compression"] = Imath.Compression(Imath.Compression.NO_COMPRESSION)
        elif compression_type == IMWRITE_EXR_COMPRESSION_RLE:
            header["compression"] = Imath.Compression(Imath.Compression.RLE_COMPRESSION)
        elif compression_type == IMWRITE_EXR_COMPRESSION_ZIPS:
            header["compression"] = Imath.Compression(Imath.Compression.ZIPS_COMPRESSION)
        elif compression_type == IMWRITE_EXR_COMPRESSION_ZIP:
            header["compression"] = Imath.Compression(Imath.Compression.ZIP_COMPRESSION)
        elif compression_type == IMWRITE_EXR_COMPRESSION_PIZ:
            header["compression"] = Imath.Compression(Imath.Compression.PIZ_COMPRESSION)
        elif compression_type == IMWRITE_EXR_COMPRESSION_PXR24:
            header["compression"] = Imath.Compression(Imath.Compression.PXR24_COMPRESSION)
        elif compression_type == IMWRITE_EXR_COMPRESSION_B44:
            header["compression"] = Imath.Compression(Imath.Compression.B44_COMPRESSION)
        elif compression_type == IMWRITE_EXR_COMPRESSION_B44A:
            header["compression"] = Imath.Compression(Imath.Compression.B44A_COMPRESSION)
        elif compression_type == IMWRITE_EXR_COMPRESSION_DWAA:
            header["compression"] = Imath.Compression(Imath.Compression.DWAA_COMPRESSION)
            # DWAA compression level (1-100, default 45)
            level = param_dict.get(IMWRITE_JPEG_QUALITY, 45)
            header["dwaCompressionLevel"] = float(level)
        elif compression_type == IMWRITE_EXR_COMPRESSION_DWAB:
            header["compression"] = Imath.Compression(Imath.Compression.DWAB_COMPRESSION)
            # DWAB compression level (1-100, default 45)
            level = param_dict.get(IMWRITE_JPEG_QUALITY, 45)
            header["dwaCompressionLevel"] = float(level)
        else:
            # Default to DWAA
            header["compression"] = Imath.Compression(Imath.Compression.DWAA_COMPRESSION)
            header["dwaCompressionLevel"] = 45.0

        # Set channels
        header["channels"] = {
            "R": Imath.Channel(pixel_type),
            "G": Imath.Channel(pixel_type),
            "B": Imath.Channel(pixel_type),
        }

        # Write file
        output = OpenEXR.OutputFile(output_path, header)
        if exr_type == IMWRITE_EXR_TYPE_FLOAT:
            output.writePixels(
                {
                    "R": image_exr[:, :, 0].astype(np.float32).tobytes(),
                    "G": image_exr[:, :, 1].astype(np.float32).tobytes(),
                    "B": image_exr[:, :, 2].astype(np.float32).tobytes(),
                }
            )
        else:
            output.writePixels(
                {
                    "R": image_exr[:, :, 0].astype(np.float16).tobytes(),
                    "G": image_exr[:, :, 1].astype(np.float16).tobytes(),
                    "B": image_exr[:, :, 2].astype(np.float16).tobytes(),
                }
            )
        return True

    else:
        # JPEG/PNG/TIFF use OpenCV (BGR format)
        image_bgr = image

        if ext in [".jpg", ".jpeg"]:
            # JPEG: default quality 100
            quality = param_dict.get(IMWRITE_JPEG_QUALITY, 100)
            image_bgr = to_uint8(image_bgr)

            # Build OpenCV options list
            options = [cv2.IMWRITE_JPEG_QUALITY, quality]

            # Add other JPEG parameters if present
            for key, value in param_dict.items():
                if key != IMWRITE_JPEG_QUALITY:  # Already added
                    options.extend([key, value])

        elif ext == ".png":
            # PNG: default compression 3
            compression = param_dict.get(IMWRITE_PNG_COMPRESSION, 3)
            if image_bgr.dtype != np.uint8:
                image_bgr = to_uint16(image_bgr)

            options = [cv2.IMWRITE_PNG_COMPRESSION, compression]

            # Add other PNG parameters if present
            for key, value in param_dict.items():
                if key != IMWRITE_PNG_COMPRESSION:  # Already added
                    options.extend([key, value])

        elif ext in [".tif", ".tiff"]:
            # TIFF: default compression 5
            compression = param_dict.get(IMWRITE_TIFF_COMPRESSION, 5)
            if image_bgr.dtype != np.uint8:
                image_bgr = to_uint16(image_bgr)

            options = [cv2.IMWRITE_TIFF_COMPRESSION, compression]

            # Add other TIFF parameters if present
            for key, value in param_dict.items():
                if key != IMWRITE_TIFF_COMPRESSION:  # Already added
                    options.extend([key, value])

        else:
            options = []

        return cv2.imwrite(output_path, image_bgr, options)
