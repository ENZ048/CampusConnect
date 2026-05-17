"""Row-level security tests for tenanted tables.

The campusconnect DB superuser bypasses RLS (BYPASSRLS attribute), so these
tests use a separate non-superuser role (``campusconnect_app``) that IS subject
to the tenant_isolation policies.  A module-scoped fixture ensures the role
exists and holds the necessary table grants before the tests run.
"""

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

APP_ROLE = "campusconnect_app"
APP_PASS = "campusconnect_app"


def _app_engine():
    """Async engine connecting as the non-superuser app role."""
    settings = get_settings()
    url = settings.DATABASE_URL.replace(
        "campusconnect:campusconnect@", f"{APP_ROLE}:{APP_PASS}@"
    )
    return create_async_engine(url, pool_pre_ping=True)


def _app_sessions() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=_app_engine(), expire_on_commit=False, class_=AsyncSession)


# ---------------------------------------------------------------------------
# Module fixture: ensure app role + grants exist
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module", autouse=True)
async def ensure_app_role():
    """Create the app role (if absent) and (re-)grant table access.

    This runs once per module.  It must survive migration up/down cycles that
    may drop and recreate tables, which invalidates pre-existing grants.
    """
    from app.db.session import async_session_factory

    async with async_session_factory() as session:
        # Create role if it doesn't exist
        await session.execute(
            text(
                f"DO $$ BEGIN "
                f"  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '{APP_ROLE}') THEN "
                f"    CREATE ROLE {APP_ROLE} LOGIN PASSWORD '{APP_PASS}' NOSUPERUSER NOBYPASSRLS; "
                f"  END IF; "
                f"END $$"
            )
        )
        db_name = session.bind.url.database  # type: ignore[union-attr]
        await session.execute(text(f"GRANT CONNECT ON DATABASE {db_name} TO {APP_ROLE}"))
        await session.execute(text(f"GRANT USAGE ON SCHEMA public TO {APP_ROLE}"))
        await session.execute(
            text(f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {APP_ROLE}")
        )
        await session.execute(
            text(f"GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {APP_ROLE}")
        )
        await session.commit()
    yield


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rls_isolates_audit_log_between_orgs():
    from app.db.session import async_session_factory

    org_a = uuid.uuid4()
    org_b = uuid.uuid4()

    async with async_session_factory() as session:
        # bypass RLS as superuser to seed data
        await session.execute(text("SET LOCAL row_security = off"))
        await session.execute(
            text(
                "INSERT INTO plans (id, code, name) "
                "VALUES (gen_random_uuid(), 'free', 'Free') ON CONFLICT DO NOTHING"
            )
        )
        for org_id, slug in ((org_a, f"a-{org_a.hex[:8]}"), (org_b, f"b-{org_b.hex[:8]}")):
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
                    "VALUES (gen_random_uuid(), :org_id, 'test')"
                ),
                {"org_id": org_id},
            )
        await session.commit()

    # Use app role (non-superuser, no BYPASSRLS) so RLS policies are enforced.
    app_factory = _app_sessions()

    async with app_factory() as session:
        await session.execute(text(f"SET LOCAL app.current_org_id = '{org_a}'"))
        rows = (await session.execute(text("SELECT org_id FROM audit_log"))).scalars().all()
        assert set(rows) == {org_a}

    async with app_factory() as session:
        await session.execute(text(f"SET LOCAL app.current_org_id = '{org_b}'"))
        rows = (await session.execute(text("SELECT org_id FROM audit_log"))).scalars().all()
        assert set(rows) == {org_b}


@pytest.mark.asyncio
async def test_rls_without_org_setting_returns_no_rows():
    app_factory = _app_sessions()

    async with app_factory() as session:
        await session.execute(text("SET LOCAL app.current_org_id = '00000000-0000-0000-0000-000000000000'"))
        rows = (await session.execute(text("SELECT count(*) FROM audit_log"))).scalar_one()
        assert rows == 0
