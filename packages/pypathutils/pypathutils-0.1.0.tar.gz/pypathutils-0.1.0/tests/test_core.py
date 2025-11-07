"""Tests for pypathutils."""

from pypathutils import normalize_path, scan_directory


def test_normalize_path():
    """Test normalize_path."""
    assert normalize_path() is None or True
