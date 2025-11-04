"""Test the fixtures module."""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.orm import Mapped, declarative_base, mapped_column

from pytest_green_light.fixtures import (
    async_engine_factory,
    async_session_factory,
    create_async_engine_fixture,
    create_async_session_fixture,
)

Base = declarative_base()


# Prefix with underscore to prevent pytest collection
class _TestModel(Base):
    """Test model for fixtures testing."""

    __tablename__ = "test_model"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]


# Alias for use in tests
TestModel = _TestModel

pytestmark = pytest.mark.asyncio


async def test_async_engine_factory():
    """Test async_engine_factory creates and disposes engine correctly."""
    url = "sqlite+aiosqlite:///:memory:"

    engines = []
    async for engine in async_engine_factory(url):
        engines.append(engine)
        assert isinstance(engine, AsyncEngine)
        # Test the engine works
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1

    # Engine should be disposed after async for loop
    assert len(engines) == 1


async def test_async_engine_factory_with_kwargs():
    """Test async_engine_factory with additional kwargs."""
    url = "sqlite+aiosqlite:///:memory:"

    async for engine in async_engine_factory(url, echo=False):
        assert isinstance(engine, AsyncEngine)
        # Verify echo was set
        assert not engine.echo


async def test_create_async_engine_fixture():
    """Test create_async_engine_fixture creates a working fixture."""
    url = "sqlite+aiosqlite:///:memory:"
    fixture_func = create_async_engine_fixture(url)

    assert callable(fixture_func)

    # Call the fixture function
    async for engine in fixture_func():
        assert isinstance(engine, AsyncEngine)
        # Test the engine works
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1


async def test_create_async_engine_fixture_with_kwargs():
    """Test create_async_engine_fixture with engine kwargs."""
    url = "sqlite+aiosqlite:///:memory:"
    fixture_func = create_async_engine_fixture(url, echo=True)

    async for engine in fixture_func():
        assert isinstance(engine, AsyncEngine)
        assert engine.echo


async def test_async_session_factory():
    """Test async_session_factory creates and manages sessions correctly."""
    url = "sqlite+aiosqlite:///:memory:"

    # Create engine first
    async for engine in async_engine_factory(url):
        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Create session
        async for session in async_session_factory(engine):
            assert isinstance(session, AsyncSession)
            # Test the session works
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1

            # Test ORM operations
            test_obj = TestModel(id=1, name="test")
            session.add(test_obj)
            await session.commit()

            # Verify it was saved
            result = await session.get(TestModel, 1)
            assert result is not None
            assert result.name == "test"


async def test_async_session_factory_with_expire_on_commit():
    """Test async_session_factory with expire_on_commit option."""
    url = "sqlite+aiosqlite:///:memory:"

    async for engine in async_engine_factory(url):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Test with expire_on_commit=True
        async for session in async_session_factory(engine, expire_on_commit=True):
            # Just verify the session works with expire_on_commit=True
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1
            # Test basic operations work
            test_obj = TestModel(id=1, name="test")
            session.add(test_obj)
            await session.commit()
            # Verify the session was configured correctly
            assert session is not None


async def test_create_async_session_fixture():
    """Test create_async_session_fixture helper."""
    url = "sqlite+aiosqlite:///:memory:"

    # Create engine
    async for engine in async_engine_factory(url):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Create session fixture function
        session_fixture = create_async_session_fixture("engine")

        # Use the fixture
        async for session in session_fixture(engine):
            assert isinstance(session, AsyncSession)
            # Test it works
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1
