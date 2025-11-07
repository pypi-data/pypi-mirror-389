"""Tests for pyregexkit core functions."""

import pytest
from pyregexkit import (
    match_pattern,
    extract_all,
    replace_all,
    find_first,
    validate_pattern,
    escape_special,
)


def test_match_pattern():
    assert match_pattern(r"\d+", "123") is True
    assert match_pattern(r"\d+", "abc") is False


def test_extract_all():
    assert extract_all(r"\d+", "abc123def456") == ["123", "456"]


def test_replace_all():
    assert replace_all(r"\d+", "X", "abc123def456") == "abcXdefX"


def test_find_first():
    assert find_first(r"\d+", "abc123def") == "123"
    assert find_first(r"\d+", "abc") is None


def test_validate_pattern():
    assert validate_pattern(r"\d+") is True
    assert validate_pattern(r"[") is False


def test_escape_special():
    assert escape_special(".*+") == r"\.\*\+"

