"""Test MissingGreenlet import fallback path."""

import sys
from unittest.mock import patch


def test_missing_greenlet_import_exception():
    """Test that MissingGreenlet import exception is handled (line 12-13)."""
    # Test the except ImportError path for MissingGreenlet
    # We need to mock sqlalchemy.exc to raise ImportError when accessing MissingGreenlet

    # Save original module
    original_plugin = sys.modules.get("pytest_green_light.plugin")

    # Create a mock sqlalchemy.exc that raises ImportError
    mock_exc = type("MockExc", (), {})

    def getattr_mock(name):
        if name == "MissingGreenlet":
            raise ImportError("cannot import name 'MissingGreenlet'")
        raise AttributeError(
            f"'{type(mock_exc).__name__}' object has no attribute '{name}'"
        )

    mock_exc.__getattr__ = getattr_mock

    # Mock sqlalchemy.exc
    with patch.dict("sys.modules", {"sqlalchemy.exc": mock_exc}):
        # Reload plugin to test import path
        if "pytest_green_light.plugin" in sys.modules:
            del sys.modules["pytest_green_light.plugin"]

        import importlib

        plugin_module = importlib.import_module("pytest_green_light.plugin")

        # Should have MissingGreenlet as None
        assert plugin_module.MissingGreenlet is None

        # Restore
        sys.modules["pytest_green_light.plugin"] = original_plugin
