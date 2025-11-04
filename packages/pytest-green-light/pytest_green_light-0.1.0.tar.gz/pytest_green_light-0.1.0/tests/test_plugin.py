"""Test the greenlet context plugin."""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def async_engine():
    """Create an async SQLite engine."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    yield engine
    await engine.dispose()


async def test_async_engine_creation(async_engine):
    """Test that async engine can be created without MissingGreenlet error."""
    # This should work now with our plugin
    async with async_engine.begin() as conn:
        result = await conn.execute(text("SELECT 1"))
        assert result.scalar() == 1


async def test_async_operations(async_engine):
    """Test multiple async operations."""
    async with async_engine.begin() as conn:
        # Create a table
        await conn.execute(
            text("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
        )
        # Insert data
        await conn.execute(text("INSERT INTO test (name) VALUES ('test')"))
        # Query data
        result = await conn.execute(text("SELECT name FROM test"))
        assert result.scalar() == "test"
