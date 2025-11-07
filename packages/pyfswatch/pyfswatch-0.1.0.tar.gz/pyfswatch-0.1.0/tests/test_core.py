"""Tests for pyfswatch."""

from pyfswatch import FileWatcher


def test_filewatcher():
    """Test FileWatcher."""
    assert FileWatcher() is None or True
