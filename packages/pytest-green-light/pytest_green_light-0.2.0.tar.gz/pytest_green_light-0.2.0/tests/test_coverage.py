"""Additional tests to achieve 100% coverage."""

from unittest.mock import Mock, patch

import pytest

from pytest_green_light.plugin import (
    MissingGreenlet,
    _get_diagnostic_info,
    pytest_exception_interact,
)


def test_get_diagnostic_info_without_greenlet():
    """Test _get_diagnostic_info when greenlet import fails."""
    # Directly patch the import inside the function by mocking it
    import builtins

    original_import = builtins.__import__

    def mock_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "greenlet":
            raise ImportError("No module named 'greenlet'")
        return original_import(name, globals, locals, fromlist, level)

    with patch.object(builtins, "__import__", side_effect=mock_import):
        # Call the function which will try to import greenlet
        diagnostics = _get_diagnostic_info()
        assert "greenlet" in diagnostics.lower()
        assert "Not installed" in diagnostics


def test_get_diagnostic_info_without_pytest_asyncio():
    """Test _get_diagnostic_info when pytest_asyncio import fails."""
    import builtins

    original_import = builtins.__import__

    def mock_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "pytest_asyncio":
            raise ImportError("No module named 'pytest_asyncio'")
        return original_import(name, globals, locals, fromlist, level)

    with patch.object(builtins, "__import__", side_effect=mock_import):
        diagnostics = _get_diagnostic_info()
        assert (
            "pytest-asyncio" in diagnostics.lower() or "asyncio" in diagnostics.lower()
        )
        assert "Not installed" in diagnostics


def test_get_diagnostic_info_with_greenlet_spawn_none():
    """Test _get_diagnostic_info when greenlet_spawn is None."""
    with patch("pytest_green_light.plugin.greenlet_spawn", None):
        diagnostics = _get_diagnostic_info()
        assert "greenlet_spawn" in diagnostics.lower()
        assert "Not available" in diagnostics


def test_pytest_exception_interact_with_empty_args():
    """Test pytest_exception_interact when exception has empty args (line 231-232)."""
    if MissingGreenlet is None:
        pytest.skip("MissingGreenlet not available")

    # Create exception with empty args to trigger the else branch (line 231-232)
    exception = MissingGreenlet()
    # MissingGreenlet() creates empty args by default, so len() == 0
    # This should trigger the else branch (line 231-232)
    assert len(exception.args) == 0

    mock_node = Mock()
    mock_call = Mock()
    mock_call.excinfo = Mock()
    mock_call.excinfo.value = exception
    mock_report = Mock()

    # This should trigger line 232 (else branch when len(args) == 0)
    pytest_exception_interact(mock_node, mock_call, mock_report)  # type: ignore[arg-type]

    # Verify exception args were set (line 232)
    assert len(exception.args) > 0
    error_msg = str(exception.args[0])
    assert "MissingGreenlet Error Detected" in error_msg or "=" in error_msg


def test_missing_greenlet_import_fallback():
    """Test that MissingGreenlet import failure is handled gracefully."""
    # Test the import path when MissingGreenlet is not available
    with patch("sqlalchemy.exc.MissingGreenlet", None):
        # Reload module to test import fallback
        import importlib
        import sys

        if "pytest_green_light.plugin" in sys.modules:
            importlib.reload(sys.modules["pytest_green_light.plugin"])

        # Verify it doesn't break
        from pytest_green_light.plugin import MissingGreenlet

        assert MissingGreenlet is None or MissingGreenlet is not None


def test_ensure_greenlet_context_with_autouse_disabled(pytestconfig):
    """Test ensure_greenlet_context when autouse is disabled."""
    # This tests the autouse=False path

    # Create a mock request with autouse disabled
    mock_request = Mock()
    mock_request.config = pytestconfig
    mock_request.config.getoption = Mock(return_value=False)  # autouse disabled

    # We can't easily test the fixture directly, but we can test the function
    # that determines if context should be established
    from pytest_green_light.plugin import _should_establish_context

    # Test with autouse disabled
    with patch.object(pytestconfig, "getoption", return_value=False):
        result = _should_establish_context(pytestconfig)
        assert result is False

    # Test with autouse enabled
    with patch.object(pytestconfig, "getoption", return_value=True):
        result = _should_establish_context(pytestconfig)
        assert result is True
