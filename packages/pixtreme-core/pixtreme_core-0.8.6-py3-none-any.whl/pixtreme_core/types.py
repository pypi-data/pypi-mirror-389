"""Type aliases for pixtreme using PEP 695 syntax (Python 3.12+).

This module provides modern type aliases using the 'type' keyword introduced
in PEP 695, offering better type checking and IDE support compared to
traditional typing.TypeAlias approach.

Examples
--------
>>> from pixtreme_core.types import DType
>>>
>>> def process(img, dtype: DType):
...     return img.astype(dtype)
"""

from typing import Literal

# Data type specifier for image operations
type DType = Literal["uint8", "uint16", "fp16", "fp32", "fp64"]
