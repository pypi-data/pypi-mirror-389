"""Tests for the aidex module."""

import pytest
from aidex import hello, get_version, __version__


def test_hello_default():
    """Test hello function with default argument."""
    assert hello() == "Hello, World!"


def test_hello_with_name():
    """Test hello function with custom name."""
    assert hello("Alice") == "Hello, Alice!"


def test_get_version():
    """Test get_version function."""
    assert get_version() == __version__


def test_version_format():
    """Test that version follows semantic versioning."""
    version_parts = __version__.split(".")
    assert len(version_parts) == 3
    assert all(part.isdigit() for part in version_parts)