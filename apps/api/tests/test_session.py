import pytest
from sqlalchemy import text


@pytest.mark.asyncio
async def test_async_session_executes_select_1():
    from app.db.session import async_session_factory
    async with async_session_factory() as session:
        result = await session.execute(text("SELECT 1"))
        assert result.scalar_one() == 1


@pytest.mark.asyncio
async def test_pgvector_extension_available():
    from app.db.session import async_session_factory
    async with async_session_factory() as session:
        await session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        result = await session.execute(
            text("SELECT extname FROM pg_extension WHERE extname='vector'")
        )
        assert result.scalar_one() == "vector"
        await session.commit()
