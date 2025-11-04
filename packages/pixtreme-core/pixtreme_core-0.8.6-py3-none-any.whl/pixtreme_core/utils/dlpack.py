from __future__ import annotations

from typing import TYPE_CHECKING, Any

import cupy as cp
import numpy as np
from nvidia import nvimgcodec

if TYPE_CHECKING:
    import torch

    TORCH_AVAILABLE: bool
else:
    try:
        import torch

        TORCH_AVAILABLE = True
    except ImportError:
        TORCH_AVAILABLE = False
        torch: Any = None


def to_tensor(
    image: np.ndarray | cp.ndarray | nvimgcodec.Image,
    device: "str | torch.device | None" = None,
) -> "torch.Tensor":
    if not TORCH_AVAILABLE:
        raise ImportError("PyTorch is not installed. Please install torch to use to_tensor().")
    if isinstance(image, nvimgcodec.Image):
        image = cp.asarray(image)

    if device is None:
        if isinstance(image, cp.ndarray):
            device_id = image.device.id  # type: ignore
        else:
            device_id = cp.cuda.device.get_device_id()
        device = torch.device(f"cuda:{device_id}")

    tensor: torch.Tensor = torch.as_tensor(image, device=device).permute(2, 0, 1).unsqueeze(0)
    return tensor


def to_numpy(image: "cp.ndarray | torch.Tensor | nvimgcodec.Image") -> np.ndarray:
    if isinstance(image, cp.ndarray):
        image = cp.asnumpy(image)
    elif TORCH_AVAILABLE and isinstance(image, torch.Tensor):
        image = image.squeeze().permute(1, 2, 0).cpu().numpy()
    elif isinstance(image, nvimgcodec.Image):
        image = cp.asarray(image).get()
    else:
        raise ValueError(
            f"Unsupported type: {type(image)}. Supported: np.ndarray, cp.ndarray, torch.Tensor, nvimgcodec.Image"
        )

    assert isinstance(image, np.ndarray)
    return image


def to_cupy(image: "np.ndarray | torch.Tensor | nvimgcodec.Image") -> cp.ndarray:
    if TORCH_AVAILABLE and isinstance(image, torch.Tensor):
        image = image.squeeze().permute(1, 2, 0)

    image = cp.asarray(image)
    return image
