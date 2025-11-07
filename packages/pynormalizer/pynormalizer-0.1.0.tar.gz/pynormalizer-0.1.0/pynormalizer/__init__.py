"""Unicode, whitespace, and accent normalization for multilingual text."""

from .core import (
    normalize_unicode,
    normalize_whitespace,
    remove_accents,
    normalize_line_endings,
    normalize_case,
)

__version__ = "0.1.0"
__all__ = [
    "normalize_unicode",
    "normalize_whitespace",
    "remove_accents",
    "normalize_line_endings",
    "normalize_case",
]

