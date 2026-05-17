import pytest
from sqlalchemy import text


@pytest.mark.asyncio
async def test_three_default_plans_exist_after_migration():
    from app.db.session import async_session_factory

    async with async_session_factory() as session:
        codes = (
            await session.execute(text("SELECT code FROM plans ORDER BY code"))
        ).scalars().all()
        assert set(codes) >= {"free", "growth", "enterprise"}
