"""Test plugin with PostgreSQL database."""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

pytestmark = pytest.mark.asyncio


@pytest.fixture(scope="function")
def postgresql_db():
    """Create a temporary PostgreSQL database."""
    try:
        from testing.postgresql import Postgresql  # type: ignore[import-untyped]

        postgresql = Postgresql()
        yield postgresql
        postgresql.stop()
    except ImportError:
        pytest.skip("testing.postgresql not available")
    except Exception as e:
        pytest.skip(f"PostgreSQL not available: {e}")


@pytest.fixture
async def postgres_engine(postgresql_db):
    """Create PostgreSQL async engine."""
    try:
        # Get connection URL from testing.postgresql
        url = postgresql_db.url().replace("postgresql://", "postgresql+asyncpg://")
        engine = create_async_engine(url, echo=False)
        # Test connection
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        yield engine
    except Exception as e:
        pytest.skip(f"PostgreSQL not available: {e}")
    finally:
        if "engine" in locals():
            await engine.dispose()


@pytest.mark.postgresql
async def test_postgresql_connection(postgres_engine):
    """Test basic PostgreSQL connection."""
    async with postgres_engine.begin() as conn:
        result = await conn.execute(text("SELECT version()"))
        version = result.scalar()
        assert "PostgreSQL" in version or "postgres" in version.lower()


@pytest.mark.postgresql
async def test_postgresql_create_table(postgres_engine):
    """Test creating a table in PostgreSQL."""
    async with postgres_engine.begin() as conn:
        await conn.execute(
            text("""
            CREATE TEMPORARY TABLE test_table (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100)
            )
        """)
        )
        await conn.execute(text("INSERT INTO test_table (name) VALUES ('test')"))
        result = await conn.execute(text("SELECT name FROM test_table WHERE id = 1"))
        assert result.scalar() == "test"


@pytest.mark.postgresql
async def test_postgresql_transactions(postgres_engine):
    """Test transactions with PostgreSQL."""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from pytest_green_light.fixtures import async_db_transaction

    async_session_maker = async_sessionmaker(postgres_engine, class_=AsyncSession)

    async with async_session_maker() as session:
        async with async_db_transaction(session):
            async with postgres_engine.begin() as conn:
                await conn.execute(
                    text("""
                    CREATE TEMPORARY TABLE test_trans (
                        id SERIAL PRIMARY KEY,
                        value INTEGER
                    )
                """)
                )
                await conn.execute(text("INSERT INTO test_trans (value) VALUES (42)"))

            # Verify data exists during transaction
            async with postgres_engine.begin() as conn:
                result = await conn.execute(
                    text("SELECT value FROM test_trans WHERE id = 1")
                )
                assert result.scalar() == 42


@pytest.mark.postgresql
async def test_postgresql_with_fixtures(postgres_engine):
    """Test PostgreSQL with plugin fixtures."""
    from pytest_green_light.fixtures import async_session_factory

    async for session in async_session_factory(postgres_engine):
        result = await session.execute(text("SELECT current_database()"))
        db_name = result.scalar()
        assert db_name is not None
        assert isinstance(db_name, str)


@pytest.mark.postgresql
async def test_postgresql_orm_operations(postgres_engine):
    """Test ORM operations with PostgreSQL."""
    from sqlalchemy import String
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    from sqlalchemy.orm import Mapped, declarative_base, mapped_column

    Base = declarative_base()

    class TestModel(Base):
        __tablename__ = "test_model"

        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str] = mapped_column(String(100))

    # Create tables
    async with postgres_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_maker = async_sessionmaker(postgres_engine, class_=AsyncSession)

    async with async_session_maker() as session:
        # Create object
        test_obj = TestModel(id=1, name="test")
        session.add(test_obj)
        await session.commit()

        # Query object
        result = await session.get(TestModel, 1)
        assert result is not None
        assert result.name == "test"

        # Cleanup
        await session.delete(result)
        await session.commit()
