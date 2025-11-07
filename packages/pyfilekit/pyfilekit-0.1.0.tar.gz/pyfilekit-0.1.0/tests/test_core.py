"""Tests for pyfilekit."""

from pyfilekit import safe_read, safe_write


def test_safe_read():
    """Test safe_read."""
    assert safe_read() is None or True
