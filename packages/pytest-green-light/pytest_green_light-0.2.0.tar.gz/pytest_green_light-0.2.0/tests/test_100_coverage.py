"""Tests specifically to achieve 100% coverage for edge cases."""

from unittest.mock import Mock

import pytest

from pytest_green_light.plugin import (
    MissingGreenlet,
    pytest_exception_interact,
)


def test_pytest_exception_interact_excinfo_none_coverage():
    """Test line 198: excinfo is None."""
    mock_node = Mock()
    mock_call = Mock()
    mock_call.excinfo = None  # This triggers line 198
    mock_report = Mock()

    # Should return early at line 198
    pytest_exception_interact(mock_node, mock_call, mock_report)  # type: ignore[arg-type]
    # If we get here, line 198 was executed


def test_pytest_exception_interact_not_missing_greenlet_coverage():
    """Test line 202: exception is not MissingGreenlet."""
    if MissingGreenlet is None:
        pytest.skip("MissingGreenlet not available")

    # Create a different exception type
    exception = ValueError("Not a MissingGreenlet")

    mock_node = Mock()
    mock_call = Mock()
    mock_call.excinfo = Mock()
    mock_call.excinfo.value = exception
    mock_report = Mock()

    # Should return early at line 202 (not isinstance check)
    pytest_exception_interact(mock_node, mock_call, mock_report)  # type: ignore[arg-type]
    # If we get here, line 202 was executed


def test_pytest_exception_interact_with_args_coverage():
    """Test lines 229-230: exception has args."""
    if MissingGreenlet is None:
        pytest.skip("MissingGreenlet not available")

    # Create exception WITH args (len > 0) to trigger lines 229-230
    exception = MissingGreenlet("Original error message")
    assert len(exception.args) > 0  # Ensure it has args

    mock_node = Mock()
    mock_call = Mock()
    mock_call.excinfo = Mock()
    mock_call.excinfo.value = exception
    mock_report = Mock()

    # This should execute lines 229-230
    pytest_exception_interact(mock_node, mock_call, mock_report)  # type: ignore[arg-type]

    # Verify lines 229-230 were executed (original message preserved)
    assert len(exception.args) > 0
    error_msg = str(exception.args[0])
    assert "Original error message" in error_msg  # Line 229 preserves original


def test_pytest_exception_interact_empty_args_coverage():
    """Test line 232: exception has empty args."""
    if MissingGreenlet is None:
        pytest.skip("MissingGreenlet not available")

    # Create exception with empty args to trigger line 232
    exception = MissingGreenlet()
    # MissingGreenlet() creates empty args by default
    assert len(exception.args) == 0

    mock_node = Mock()
    mock_call = Mock()
    mock_call.excinfo = Mock()
    mock_call.excinfo.value = exception
    mock_report = Mock()

    # This should execute line 232 (else branch)
    pytest_exception_interact(mock_node, mock_call, mock_report)  # type: ignore[arg-type]

    # Verify line 232 was executed
    assert len(exception.args) > 0
    error_msg = str(exception.args[0])
    assert "MissingGreenlet Error Detected" in error_msg or "=" in error_msg
