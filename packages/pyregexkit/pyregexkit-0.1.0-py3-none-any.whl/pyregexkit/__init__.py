"""Simplify regex matching, extraction, and replacement with human-friendly syntax."""

from .core import (
    match_pattern,
    extract_all,
    replace_all,
    find_first,
    validate_pattern,
    escape_special,
)

__version__ = "0.1.0"
__all__ = [
    "match_pattern",
    "extract_all",
    "replace_all",
    "find_first",
    "validate_pattern",
    "escape_special",
]

