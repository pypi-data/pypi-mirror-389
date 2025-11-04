"""Test transaction management features."""

import pytest
from sqlalchemy.orm import Mapped, declarative_base, mapped_column

from pytest_green_light.fixtures import (
    async_db_transaction,
    async_engine_factory,
    async_session_factory,
    async_transaction_fixture,
)

Base = declarative_base()


class TransactionTestModel(Base):
    __tablename__ = "transaction_test_model"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]


pytestmark = pytest.mark.asyncio


async def test_async_db_transaction_rollback():
    """Test that async_db_transaction automatically rolls back."""
    url = "sqlite+aiosqlite:///:memory:"

    async for engine in async_engine_factory(url):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async for session in async_session_factory(engine):
            # Create an object in a transaction
            async with async_db_transaction(session, rollback=True):
                obj = TransactionTestModel(id=1, name="test")
                session.add(obj)
                await session.flush()
                # Verify it was flushed
                result = await session.get(TransactionTestModel, 1)
                assert result is not None
                assert result.name == "test"

            # After transaction context, changes should be rolled back
            result = await session.get(TransactionTestModel, 1)
            assert result is None


async def test_async_db_transaction_commit():
    """Test that async_db_transaction can commit when rollback=False."""
    url = "sqlite+aiosqlite:///:memory:"

    async for engine in async_engine_factory(url):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async for session in async_session_factory(engine):
            # Create an object and commit
            async with async_db_transaction(session, rollback=False):
                obj = TransactionTestModel(id=1, name="test")
                session.add(obj)
                await session.commit()

            # Verify it was committed
            result = await session.get(TransactionTestModel, 1)
            assert result is not None
            assert result.name == "test"


async def test_async_db_transaction_nested():
    """Test nested transactions (savepoints)."""
    url = "sqlite+aiosqlite:///:memory:"

    async for engine in async_engine_factory(url):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async for session in async_session_factory(engine):
            # Create first object
            obj1 = TransactionTestModel(id=1, name="first")
            session.add(obj1)
            await session.commit()

            # Nested transaction
            async with async_db_transaction(session, nested=True, rollback=True):
                obj2 = TransactionTestModel(id=2, name="second")
                session.add(obj2)
                await session.flush()
                # Verify both exist
                result1 = await session.get(TransactionTestModel, 1)
                result2 = await session.get(TransactionTestModel, 2)
                assert result1 is not None
                assert result2 is not None

            # After nested transaction rollback, only first should exist
            result1 = await session.get(TransactionTestModel, 1)
            result2 = await session.get(TransactionTestModel, 2)
            assert result1 is not None
            assert result2 is None


async def test_async_db_transaction_exception_handling():
    """Test that exceptions cause rollback."""
    url = "sqlite+aiosqlite:///:memory:"

    async for engine in async_engine_factory(url):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async for session in async_session_factory(engine):
            try:
                async with async_db_transaction(session, rollback=True):
                    obj = TransactionTestModel(id=1, name="test")
                    session.add(obj)
                    await session.flush()
                    raise ValueError("Test exception")
            except ValueError:
                pass  # Expected

            # Verify rollback happened
            result = await session.get(TransactionTestModel, 1)
            assert result is None


async def test_async_transaction_fixture():
    """Test async_transaction_fixture."""
    url = "sqlite+aiosqlite:///:memory:"

    async for engine in async_engine_factory(url):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async for session in async_session_factory(engine):
            # Use transaction fixture
            async for _ in async_transaction_fixture(session, rollback=True):
                obj = TransactionTestModel(id=1, name="test")
                session.add(obj)
                await session.flush()
                # Verify it was flushed
                result = await session.get(TransactionTestModel, 1)
                assert result is not None

            # After fixture, changes should be rolled back
            result = await session.get(TransactionTestModel, 1)
            assert result is None


async def test_async_transaction_fixture_with_commit():
    """Test async_transaction_fixture with commit."""
    url = "sqlite+aiosqlite:///:memory:"

    async for engine in async_engine_factory(url):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async for session in async_session_factory(engine):
            # Use transaction fixture with commit
            async for _ in async_transaction_fixture(session, rollback=False):
                obj = TransactionTestModel(id=1, name="test")
                session.add(obj)
                await session.commit()

            # Verify it was committed
            result = await session.get(TransactionTestModel, 1)
            assert result is not None


async def test_async_db_transaction_nested_exception():
    """Test nested transaction exception handling."""
    url = "sqlite+aiosqlite:///:memory:"

    async for engine in async_engine_factory(url):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async for session in async_session_factory(engine):
            # Create first object
            obj1 = TransactionTestModel(id=1, name="first")
            session.add(obj1)
            await session.commit()

            # Nested transaction with exception
            try:
                async with async_db_transaction(session, nested=True, rollback=True):
                    obj2 = TransactionTestModel(id=2, name="second")
                    session.add(obj2)
                    await session.flush()
                    raise ValueError("Test exception in nested transaction")
            except ValueError:
                pass  # Expected

            # Verify rollback happened - only first should exist
            result1 = await session.get(TransactionTestModel, 1)
            result2 = await session.get(TransactionTestModel, 2)
            assert result1 is not None
            assert result2 is None
