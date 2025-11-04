"""
ShadeSorter - Deterministic color family classifier.
"""

from shade_sorter.api import (
    classify_from_all,
    classify_from_hex,
    classify_from_hsl,
    classify_from_hsv,
    classify_from_lab,
    classify_from_lch,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "classify_from_hex",
    "classify_from_hsl",
    "classify_from_hsv",
    "classify_from_lab",
    "classify_from_lch",
    "classify_from_all",
]
