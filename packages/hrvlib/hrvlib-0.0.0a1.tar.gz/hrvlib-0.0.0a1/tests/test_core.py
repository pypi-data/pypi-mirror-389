"""Tests for hrvlib core functionality."""

import pytest
from hrvlib import hello
from hrvlib._core import hello_from_bin


def test_hello_from_bin():
    """Test the C++ binding returns expected string."""
    result = hello_from_bin()
    assert isinstance(result, str)
    assert result == "Hello from hrvlib!"


def test_hello():
    """Test the Python wrapper function."""
    result = hello()
    assert isinstance(result, str)
    assert result == "Hello from hrvlib!"


def test_hello_consistency():
    """Test that Python wrapper and C++ binding return same value."""
    assert hello() == hello_from_bin()
