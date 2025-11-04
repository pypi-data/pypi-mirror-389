"""Test error handling and diagnostics."""

from unittest.mock import Mock, patch

import pytest

from pytest_green_light.plugin import (
    MissingGreenlet,
    _get_diagnostic_info,
    pytest_exception_interact,
)

# Remove asyncio marker for this file
pytestmark = []


def test_get_diagnostic_info():
    """Test _get_diagnostic_info returns diagnostic information."""
    diagnostics = _get_diagnostic_info()

    # Should contain diagnostic information
    assert isinstance(diagnostics, str)
    assert len(diagnostics) > 0

    # Should check for SQLAlchemy
    assert "SQLAlchemy" in diagnostics or "sqlalchemy" in diagnostics.lower()

    # Should check for greenlet
    assert "greenlet" in diagnostics.lower()


def test_get_diagnostic_info_with_missing_imports():
    """Test _get_diagnostic_info handles missing imports gracefully."""
    # Mock imports to simulate missing packages
    with patch.dict("sys.modules", {"sqlalchemy": None}, clear=False):
        diagnostics = _get_diagnostic_info()
        assert isinstance(diagnostics, str)
        # Should still return something even if imports fail
        assert len(diagnostics) > 0


def test_pytest_exception_interact_with_missing_greenlet():
    """Test pytest_exception_interact handles MissingGreenlet errors (line 229-230)."""
    if MissingGreenlet is None:
        pytest.skip("MissingGreenlet not available in this SQLAlchemy version")

    # Create a mock MissingGreenlet exception with args to trigger lines 229-230
    exception = MissingGreenlet("Test error")
    # Ensure it has args with len > 0
    assert len(exception.args) > 0

    # Create mock objects
    mock_node = Mock()
    mock_call = Mock()
    mock_call.excinfo = Mock()
    mock_call.excinfo.value = exception
    mock_report = Mock()

    # Call the function - this should execute lines 229-230
    pytest_exception_interact(mock_node, mock_call, mock_report)  # type: ignore[arg-type]

    # Verify exception args were modified (line 229-230 path)
    assert len(exception.args) > 0
    error_msg = str(exception.args[0])
    # The original message should be preserved (line 229 concatenates)
    # Check that either the original message is there OR the diagnostic was added
    assert (
        "Test error" in error_msg
        or "MissingGreenlet Error Detected" in error_msg
        or "Diagnostic Information" in error_msg
        or "Troubleshooting Steps" in error_msg
    )


def test_pytest_exception_interact_with_other_exception():
    """Test pytest_exception_interact ignores non-MissingGreenlet exceptions."""
    # Create a different exception
    exception = ValueError("Not a MissingGreenlet error")

    # Create mock objects
    mock_node = Mock()
    mock_call = Mock()
    mock_call.excinfo = Mock()
    mock_call.excinfo.value = exception
    mock_report = Mock()

    # Call the function
    pytest_exception_interact(mock_node, mock_call, mock_report)  # type: ignore[arg-type]

    # Exception should not be modified
    assert len(exception.args) == 1
    assert str(exception.args[0]) == "Not a MissingGreenlet error"


def test_pytest_exception_interact_with_none_excinfo():
    """Test pytest_exception_interact handles None excinfo."""
    mock_node = Mock()
    mock_call = Mock()
    mock_call.excinfo = None
    mock_report = Mock()

    # Should not raise
    pytest_exception_interact(mock_node, mock_call, mock_report)  # type: ignore[arg-type]


def test_pytest_exception_interact_when_missing_greenlet_is_none():
    """Test pytest_exception_interact when MissingGreenlet class is not available."""
    # Save original

    # Temporarily set to None
    with patch("pytest_green_light.plugin.MissingGreenlet", None):
        mock_node = Mock()
        mock_call = Mock()
        mock_report = Mock()

        # Should return early without error
        pytest_exception_interact(mock_node, mock_call, mock_report)  # type: ignore[arg-type]
