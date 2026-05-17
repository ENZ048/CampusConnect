import uuid

import pytest
from sqlalchemy import select, text


@pytest.mark.asyncio
async def test_auto_filter_scopes_query_to_current_org():
    from app.db.session import async_session_factory
    from app.db.tenant_filter import set_current_org
    from app.models import AuditLog

    org_a = uuid.uuid4()
    org_b = uuid.uuid4()

    async with async_session_factory() as session:
        await session.execute(text("SET LOCAL row_security = off"))
        for org_id, slug in ((org_a, f"f-{org_a.hex[:8]}"), (org_b, f"g-{org_b.hex[:8]}")):
            await session.execute(
                text(
                    "INSERT INTO organizations (id, name, slug) "
                    "VALUES (:id, :name, :slug) ON CONFLICT DO NOTHING"
                ),
                {"id": org_id, "name": slug, "slug": slug},
            )
            await session.execute(
                text(
                    "INSERT INTO audit_log (id, org_id, action) "
                    "VALUES (gen_random_uuid(), :org_id, 'filter-test')"
                ),
                {"org_id": org_id},
            )
        await session.commit()

    async with async_session_factory() as session:
        await session.execute(text("SET LOCAL row_security = off"))
        with set_current_org(org_a):
            rows = (
                await session.execute(
                    select(AuditLog).where(AuditLog.action == "filter-test")
                )
            ).scalars().all()
            assert len(rows) >= 1
            assert all(row.org_id == org_a for row in rows)


@pytest.mark.asyncio
async def test_auto_filter_bypass_context_returns_all_rows():
    from app.db.session import async_session_factory
    from app.db.tenant_filter import bypass_tenant_filter
    from app.models import AuditLog

    async with async_session_factory() as session:
        await session.execute(text("SET LOCAL row_security = off"))
        with bypass_tenant_filter():
            rows = (
                await session.execute(
                    select(AuditLog).where(AuditLog.action == "filter-test")
                )
            ).scalars().all()
            org_ids = {row.org_id for row in rows}
            assert len(org_ids) >= 2
