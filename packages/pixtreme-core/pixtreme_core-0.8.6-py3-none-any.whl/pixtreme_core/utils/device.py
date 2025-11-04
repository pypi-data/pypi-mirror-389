"""CUDA device context manager."""

import cupy as cp


class Device:
    """Context manager for CUDA device selection.

    Args:
        device_id: CUDA device ID to use.

    Example:
        >>> import pixtreme as px
        >>> with px.Device(1):
        ...     image = px.imread("image.png")  # Uses GPU 1
    """

    def __init__(self, device_id: int = 0):
        self.device_id = device_id
        self._device = cp.cuda.Device(device_id)

    def __enter__(self):
        self._device.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self._device.__exit__(exc_type, exc_val, exc_tb)
