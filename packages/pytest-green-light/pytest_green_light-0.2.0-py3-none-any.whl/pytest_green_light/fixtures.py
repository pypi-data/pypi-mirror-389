"""Fixtures for async SQLAlchemy engines with greenlet context."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Callable

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from pytest_green_light.plugin import _establish_greenlet_context_async


async def async_engine_factory(
    url: str,
    **kwargs: Any,
) -> AsyncGenerator[AsyncEngine, None]:
    """
    Factory fixture that creates an async engine after establishing greenlet context.

    Usage:
        @pytest.fixture
        async def engine(async_engine_factory):
            async for eng in async_engine_factory("sqlite+aiosqlite:///:memory:"):
                yield eng

    Or use the provided fixtures directly.
    """
    # Establish greenlet context BEFORE creating engine
    await _establish_greenlet_context_async()

    # Now create the engine - this should work now
    engine = create_async_engine(url, **kwargs)
    try:
        yield engine
    finally:
        await engine.dispose()


def create_async_engine_fixture(
    url: str,
    **engine_kwargs: Any,
) -> Callable:
    """
    Create a pytest fixture for an async SQLAlchemy engine.

    Args:
        url: Database URL
        **engine_kwargs: Additional kwargs to pass to create_async_engine

    Returns:
        A pytest fixture function
    """

    async def _fixture() -> AsyncGenerator[AsyncEngine, None]:
        async for engine in async_engine_factory(url, **engine_kwargs):
            yield engine

    return _fixture


async def async_session_factory(
    engine: AsyncEngine,
    *,
    expire_on_commit: bool = False,
    **session_kwargs: Any,
) -> AsyncGenerator[AsyncSession, None]:
    """
    Factory fixture that creates an async session from an engine.

    Args:
        engine: Async SQLAlchemy engine
        expire_on_commit: Whether to expire objects on commit
        **session_kwargs: Additional kwargs to pass to async_sessionmaker

    Yields:
        AsyncSession instance

    Usage:
        @pytest.fixture
        async def session(async_session_factory, engine):
            async for sess in async_session_factory(engine):
                yield sess
    """
    # Establish greenlet context before creating session
    await _establish_greenlet_context_async()

    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=expire_on_commit,
        **session_kwargs,
    )

    async with async_session_maker() as session:
        yield session


def create_async_session_fixture(
    engine_fixture_name: str = "async_engine",
    *,
    expire_on_commit: bool = False,
    **session_kwargs: Any,
) -> Callable:
    """
    Create a pytest fixture for an async SQLAlchemy session.

    Args:
        engine_fixture_name: Name of the engine fixture to use
        expire_on_commit: Whether to expire objects on commit
        **session_kwargs: Additional kwargs to pass to async_sessionmaker

    Returns:
        A pytest fixture function

    Usage:
        @pytest.fixture
        async def session(
            create_async_session_fixture("engine")
        ):
            async for sess in create_async_session_fixture("engine")():
                yield sess
    """

    async def _fixture(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
        async for session in async_session_factory(
            engine,
            expire_on_commit=expire_on_commit,
            **session_kwargs,
        ):
            yield session

    # Set the fixture name for dependency injection
    _fixture.__name__ = f"async_session_from_{engine_fixture_name}"

    return _fixture


@asynccontextmanager
async def async_db_transaction(
    session: AsyncSession,
    *,
    rollback: bool = True,
    nested: bool = False,
) -> AsyncGenerator[None, None]:
    """
    Context manager for database transactions with automatic rollback.

    Args:
        session: Async SQLAlchemy session
        rollback: Whether to rollback the transaction on exit (default: True)
        nested: Whether to create a nested transaction (savepoint)

    Yields:
        None - transaction is active during context

    Usage:
        async with async_db_transaction(session):
            # Do database operations
            session.add(obj)
            await session.flush()
        # Transaction automatically rolled back
    """
    if nested:
        # Create a nested transaction (savepoint)
        async with session.begin_nested():
            try:
                yield
            except Exception:
                # Always rollback on exception
                await session.rollback()
                raise
            finally:
                if rollback:
                    await session.rollback()
    else:
        # Use regular transaction
        try:
            yield
        except Exception:
            # Always rollback on exception
            await session.rollback()
            raise
        finally:
            if rollback:
                await session.rollback()


async def async_transaction_fixture(
    session: AsyncSession,
    *,
    rollback: bool = True,
    nested: bool = False,
) -> AsyncGenerator[None, None]:
    """
    Fixture that provides a transaction context with automatic rollback.

    Args:
        session: Async SQLAlchemy session
        rollback: Whether to rollback the transaction on exit (default: True)
        nested: Whether to create a nested transaction (savepoint)

    Yields:
        None - transaction is active during fixture

    Usage:
        @pytest.fixture
        async def transaction(async_transaction_fixture, session):
            async for _ in async_transaction_fixture(session):
                yield

        async def test_my_code(transaction, session):
            # All changes will be rolled back after test
            session.add(obj)
            await session.commit()
    """
    async with async_db_transaction(session, rollback=rollback, nested=nested):
        yield
