"""Test excinfo None path (line 198)."""

from unittest.mock import Mock

from pytest_green_light.plugin import pytest_exception_interact


def test_pytest_exception_interact_excinfo_none():
    """Test pytest_exception_interact when excinfo is None (line 198)."""
    mock_node = Mock()
    mock_call = Mock()
    mock_call.excinfo = None  # This should trigger line 198
    mock_report = Mock()

    # Should return early without error
    pytest_exception_interact(mock_node, mock_call, mock_report)  # type: ignore[arg-type]

    # If we get here, it worked correctly
