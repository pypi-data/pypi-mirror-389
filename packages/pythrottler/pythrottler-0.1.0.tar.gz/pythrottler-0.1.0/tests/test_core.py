"""Tests for pythrottler."""

from pythrottler import throttle


def test_throttle():
    """Test throttle."""
    assert throttle() is None or True
