"""Test plugin with multiple SQLAlchemy versions."""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Mark async tests individually to avoid warning on sync tests


@pytest.fixture
async def sqlite_engine():
    """Create SQLite async engine for version testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    yield engine
    await engine.dispose()


def test_sqlalchemy_version():
    """Test that SQLAlchemy is installed and version is compatible."""
    import sqlalchemy

    version = sqlalchemy.__version__
    assert version is not None
    # Should be 2.0.0 or higher
    major, minor = map(int, version.split(".")[:2])
    assert major >= 2, f"SQLAlchemy version {version} is too old, need 2.0+"
    assert (major, minor) >= (2, 0), (
        f"SQLAlchemy version {version} is too old, need 2.0+"
    )


@pytest.mark.asyncio
@pytest.mark.sqlalchemy_version
async def test_basic_operations_sqlalchemy_2_0(sqlite_engine):
    """Test basic operations work with SQLAlchemy 2.0+."""
    import sqlalchemy

    version = sqlalchemy.__version__
    major, minor = map(int, version.split(".")[:2])

    if (major, minor) < (2, 0):
        pytest.skip(f"SQLAlchemy {version} is less than 2.0")

    # Test basic connection
    async with sqlite_engine.begin() as conn:
        result = await conn.execute(text("SELECT 1"))
        assert result.scalar() == 1


@pytest.mark.asyncio
@pytest.mark.sqlalchemy_version
async def test_greenlet_spawn_import():
    """Test that greenlet_spawn can be imported from SQLAlchemy."""
    try:
        from sqlalchemy.util._concurrency_py3k import greenlet_spawn

        assert greenlet_spawn is not None
    except ImportError:
        try:
            from sqlalchemy.util import greenlet_spawn

            assert greenlet_spawn is not None
        except ImportError:
            pytest.fail("greenlet_spawn not available in this SQLAlchemy version")


@pytest.mark.asyncio
@pytest.mark.sqlalchemy_version
async def test_plugin_works_with_sqlalchemy_2_0(sqlite_engine):
    """Test that plugin works with SQLAlchemy 2.0."""
    import sqlalchemy

    version = sqlalchemy.__version__
    major, minor = map(int, version.split(".")[:2])

    if (major, minor) < (2, 0):
        pytest.skip(f"SQLAlchemy {version} is less than 2.0")

    # This should work with our plugin
    async with sqlite_engine.begin() as conn:
        await conn.execute(
            text("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
        )
        await conn.execute(text("INSERT INTO test (name) VALUES ('test')"))
        result = await conn.execute(text("SELECT name FROM test WHERE id = 1"))
        assert result.scalar() == "test"


@pytest.mark.asyncio
@pytest.mark.sqlalchemy_version
async def test_async_session_with_sqlalchemy_2_0(sqlite_engine):
    """Test async session works with SQLAlchemy 2.0."""
    import sqlalchemy
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    from sqlalchemy.orm import Mapped, declarative_base, mapped_column

    version = sqlalchemy.__version__
    major, minor = map(int, version.split(".")[:2])

    if (major, minor) < (2, 0):
        pytest.skip(f"SQLAlchemy {version} is less than 2.0")

    Base = declarative_base()

    class TestModel(Base):
        __tablename__ = "test_model"

        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str]

    # Create tables
    async with sqlite_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_maker = async_sessionmaker(sqlite_engine, class_=AsyncSession)

    async with async_session_maker() as session:
        # Test operations
        test_obj = TestModel(id=1, name="test")
        session.add(test_obj)
        await session.commit()

        result = await session.get(TestModel, 1)
        assert result is not None
        assert result.name == "test"


@pytest.mark.asyncio
@pytest.mark.sqlalchemy_version
async def test_version_compatibility():
    """Test compatibility with different SQLAlchemy version patterns."""
    import sqlalchemy

    version = sqlalchemy.__version__

    # Extract version components
    parts = version.split(".")
    major = int(parts[0])
    int(parts[1]) if len(parts) > 1 else 0

    # Plugin should work with SQLAlchemy 2.0+
    assert major >= 2, f"Plugin requires SQLAlchemy 2.0+, got {version}"

    # Test that greenlet_spawn is available
    try:
        from sqlalchemy.util._concurrency_py3k import greenlet_spawn
    except ImportError:
        try:
            from sqlalchemy.util import greenlet_spawn  # noqa: F401
        except ImportError:
            pytest.fail(f"greenlet_spawn not available in SQLAlchemy {version}")


@pytest.mark.asyncio
@pytest.mark.sqlalchemy_version
async def test_plugin_fixtures_with_different_versions(sqlite_engine):
    """Test that plugin fixtures work across SQLAlchemy versions."""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from pytest_green_light.fixtures import async_db_transaction, async_session_factory

    # Test session factory
    async for session in async_session_factory(sqlite_engine):
        result = await session.execute(text("SELECT 1"))
        assert result.scalar() == 1

    # Test transaction management
    async_session_maker = async_sessionmaker(sqlite_engine, class_=AsyncSession)
    async with async_session_maker() as session:
        async with async_db_transaction(session):
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1
