"""Test __init__.py module."""

import importlib
import sys


def test_version_attribute():
    """Test that __version__ is set correctly."""
    # Force reload to ensure we measure the assignment
    if "pytest_green_light" in sys.modules:
        pytest_green_light = importlib.reload(sys.modules["pytest_green_light"])
    else:
        import pytest_green_light

    # Access __version__ to ensure it's measured
    version = pytest_green_light.__version__
    assert version == "0.1.0"
    assert isinstance(version, str)


def test_module_has_version():
    """Test that the module has the __version__ attribute."""
    import pytest_green_light

    assert hasattr(pytest_green_light, "__version__")
    # Directly access the attribute
    assert pytest_green_light.__version__ == "0.1.0"
