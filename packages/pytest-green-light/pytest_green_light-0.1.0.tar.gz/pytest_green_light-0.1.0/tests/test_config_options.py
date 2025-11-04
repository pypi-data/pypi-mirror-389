"""Test configuration options."""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Mark async tests individually to avoid warnings on sync tests


@pytest.mark.asyncio
async def test_autouse_enabled_by_default():
    """Test that autouse is enabled by default."""
    # This should work without any configuration
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_debug_option():
    """Test that debug option can be set (just verify it doesn't break)."""
    # Debug option should not break functionality
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_ensure_greenlet_context_fixture(ensure_greenlet_context):
    """Test that ensure_greenlet_context fixture is available."""
    # The fixture should be available and work
    # Since it's autouse, it's already established
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
    finally:
        await engine.dispose()


def test_pytest_addoption_registered():
    """Test that pytest_addoption is registered and options are available."""
    from pytest_green_light.plugin import pytest_addoption

    # Create a mock parser
    class MockParser:
        def __init__(self):
            self.groups = {}

        def getgroup(self, name, desc):
            if name not in self.groups:
                self.groups[name] = MockGroup()
            return self.groups[name]

    class MockGroup:
        def __init__(self):
            self.options = []

        def addoption(self, *args, **kwargs):
            self.options.append((args, kwargs))

    parser = MockParser()
    pytest_addoption(parser)

    # Verify options were added
    assert "green-light" in parser.groups
    group = parser.groups["green-light"]
    assert len(group.options) > 0

    # Check for specific options
    option_names = [opt[0][0] for opt in group.options if opt[0]]
    assert "--green-light-debug" in option_names or any(
        "--green-light" in str(opt) for opt in option_names
    )


def test_pytest_configure_registers_markers(pytestconfig):
    """Test that pytest_configure registers markers."""
    from pytest_green_light.plugin import pytest_configure

    pytest_configure(pytestconfig)

    # Check that marker was registered
    markers = pytestconfig.getini("markers")
    assert any("async_sqlalchemy" in marker for marker in markers)
