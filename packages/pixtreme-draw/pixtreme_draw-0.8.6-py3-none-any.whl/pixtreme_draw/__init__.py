"""pixtreme-draw: GPU-accelerated drawing primitives"""

__version__ = "0.8.6"

from .mask import create_rounded_mask
from .shape import circle, rectangle
from .text import add_label, put_text

__all__ = [
    "create_rounded_mask",
    "circle",
    "rectangle",
    "add_label",
    "put_text",
]
