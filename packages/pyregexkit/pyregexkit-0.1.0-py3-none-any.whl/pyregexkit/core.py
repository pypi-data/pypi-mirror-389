"""Core regex utility functions."""

import re
from typing import List, Optional


def match_pattern(pattern: str, text: str, flags: int = 0) -> bool:
    """Check if pattern matches text."""
    try:
        return bool(re.search(pattern, text, flags))
    except re.error:
        return False


def extract_all(pattern: str, text: str, flags: int = 0) -> List[str]:
    """Extract all matches from text."""
    try:
        return re.findall(pattern, text, flags)
    except re.error:
        return []


def replace_all(pattern: str, replacement: str, text: str, flags: int = 0) -> str:
    """Replace all matches in text."""
    try:
        return re.sub(pattern, replacement, text, flags=flags)
    except re.error:
        return text


def find_first(pattern: str, text: str, flags: int = 0) -> Optional[str]:
    """Find first match in text."""
    try:
        match = re.search(pattern, text, flags)
        return match.group(0) if match else None
    except re.error:
        return None


def validate_pattern(pattern: str) -> bool:
    """Validate if pattern is a valid regex."""
    try:
        re.compile(pattern)
        return True
    except re.error:
        return False


def escape_special(text: str) -> str:
    """Escape special regex characters."""
    return re.escape(text)

