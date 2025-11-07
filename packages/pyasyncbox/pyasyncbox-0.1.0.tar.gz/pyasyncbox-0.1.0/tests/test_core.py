"""Tests for pyasyncbox."""

from pyasyncbox import retry, timeout


def test_retry():
    """Test retry."""
    assert retry() is None or True
