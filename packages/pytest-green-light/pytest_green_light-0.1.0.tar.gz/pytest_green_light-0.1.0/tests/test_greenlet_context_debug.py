"""Test greenlet context establishment with debug mode to cover all paths."""

from unittest.mock import patch

import pytest

from pytest_green_light.plugin import _establish_greenlet_context_async


@pytest.mark.asyncio
async def test_establish_greenlet_context_async_success_with_debug():
    """Test successful greenlet context establishment with debug (line 50-52)."""
    import warnings

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        await _establish_greenlet_context_async(debug=True)
        # Should have a warning about successful establishment
        plugin_warnings = [
            warning
            for warning in w
            if "Greenlet context established successfully" in str(warning.message)
        ]
        assert len(plugin_warnings) > 0


@pytest.mark.asyncio
async def test_establish_greenlet_context_async_exception_with_debug():
    """Test exception handling with debug enabled (line 56-63)."""

    # Mock greenlet_spawn to raise an exception
    async def mock_greenlet_spawn(func):
        raise RuntimeError("Test error")

    import warnings

    with patch("pytest_green_light.plugin.greenlet_spawn", mock_greenlet_spawn):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            await _establish_greenlet_context_async(debug=True)
            # Should have a warning about the failure (line 58-62)
            plugin_warnings = [
                warning
                for warning in w
                if "Failed to establish greenlet context" in str(warning.message)
            ]
            assert len(plugin_warnings) > 0
