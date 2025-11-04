"""Test plugin with MySQL database."""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

pytestmark = pytest.mark.asyncio


@pytest.fixture(scope="function")
def mysqld_db():
    """Create a temporary MySQL database."""
    try:
        from testing.mysqld import Mysqld

        mysqld = Mysqld()
        yield mysqld
        mysqld.stop()
    except ImportError as e:
        pytest.skip(f"testing.mysqld not available: {e}")
    except Exception as e:
        # Log the actual error for debugging
        pytest.skip(f"MySQL not available: {type(e).__name__}: {e}")


@pytest.fixture
async def mysql_engine(mysqld_db):
    """Create MySQL async engine."""
    engine = None
    try:
        # Get connection URL from testing.mysqld
        # testing.mysqld returns URLs like: mysql+pymysql:// or mysql://
        # We need to convert to mysql+aiomysql://
        original_url = mysqld_db.url()
        if "pymysql" in original_url:
            url = original_url.replace("mysql+pymysql://", "mysql+aiomysql://")
        else:
            url = original_url.replace("mysql://", "mysql+aiomysql://")
        # Don't use pool_pre_ping as it can trigger greenlet operations
        # that need context established first
        engine = create_async_engine(url, echo=False)
        # Test connection - use asyncio.wait_for for Python 3.8 compatibility
        import asyncio

        try:
            # Try with timeout for Python 3.11+
            async with asyncio.timeout(5.0):
                async with engine.begin() as conn:
                    await conn.execute(text("SELECT 1"))
        except AttributeError:
            # Fallback for Python 3.8-3.10
            async with engine.begin() as conn:
                await asyncio.wait_for(conn.execute(text("SELECT 1")), timeout=5.0)
        yield engine
    except ImportError as e:
        pytest.skip(f"aiomysql not available: {e}")
    except Exception as e:
        pytest.skip(f"MySQL connection failed: {type(e).__name__}: {e}")
    finally:
        if engine is not None:
            await engine.dispose()


@pytest.mark.mysql
async def test_mysql_connection(mysql_engine):
    """Test basic MySQL connection."""
    async with mysql_engine.begin() as conn:
        result = await conn.execute(text("SELECT VERSION()"))
        version = result.scalar()
        assert version is not None
        assert isinstance(version, str)


@pytest.mark.mysql
async def test_mysql_create_table(mysql_engine):
    """Test creating a table in MySQL."""
    async with mysql_engine.begin() as conn:
        await conn.execute(
            text("""
            CREATE TEMPORARY TABLE test_table (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100)
            )
        """)
        )
        await conn.execute(text("INSERT INTO test_table (name) VALUES ('test')"))
        result = await conn.execute(text("SELECT name FROM test_table WHERE id = 1"))
        assert result.scalar() == "test"


@pytest.mark.mysql
async def test_mysql_transactions(mysql_engine):
    """Test transactions with MySQL."""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from pytest_green_light.fixtures import async_db_transaction

    async_session_maker = async_sessionmaker(mysql_engine, class_=AsyncSession)

    async with async_session_maker() as session:
        async with async_db_transaction(session):
            async with mysql_engine.begin() as conn:
                await conn.execute(
                    text("""
                    CREATE TEMPORARY TABLE test_trans (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        value INT
                    )
                """)
                )
                await conn.execute(text("INSERT INTO test_trans (value) VALUES (42)"))

            # Verify data exists during transaction
            async with mysql_engine.begin() as conn:
                result = await conn.execute(
                    text("SELECT value FROM test_trans WHERE id = 1")
                )
                assert result.scalar() == 42


@pytest.mark.mysql
async def test_mysql_with_fixtures(mysql_engine):
    """Test MySQL with plugin fixtures."""
    from pytest_green_light.fixtures import async_session_factory

    async for session in async_session_factory(mysql_engine):
        result = await session.execute(text("SELECT DATABASE()"))
        db_name = result.scalar()
        assert db_name is not None
        assert isinstance(db_name, str)


@pytest.mark.mysql
async def test_mysql_orm_operations(mysql_engine):
    """Test ORM operations with MySQL."""
    from sqlalchemy import String
    from sqlalchemy.orm import Mapped, declarative_base, mapped_column

    from pytest_green_light.fixtures import async_session_factory

    Base = declarative_base()

    class _MySQLTestModel(Base):
        """Test model for MySQL ORM operations."""

        __tablename__ = "test_model"

        id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
        name: Mapped[str] = mapped_column(String(100))

    TestModel = _MySQLTestModel

    # Create tables - use async execution instead of run_sync
    async with mysql_engine.begin() as conn:
        # Create table using SQL directly to avoid sync operation
        await conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS test_model (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100)
            )
        """)
        )

    # Use plugin's session factory which ensures greenlet context
    async for session in async_session_factory(mysql_engine):
        # Create object
        test_obj = TestModel(name="test")
        session.add(test_obj)
        await session.commit()

        # Query object
        result = await session.get(TestModel, test_obj.id)
        assert result is not None
        assert result.name == "test"

        # Cleanup
        await session.delete(result)
        await session.commit()

        # Drop table
        async with mysql_engine.begin() as conn:
            await conn.execute(text("DROP TABLE IF EXISTS test_model"))
