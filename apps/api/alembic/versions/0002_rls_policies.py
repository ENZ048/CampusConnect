"""rls policies on tenanted tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-17 00:01:00.000000
"""
from collections.abc import Sequence

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


TENANTED_TABLES = ["audit_log"]


def upgrade() -> None:
    for table in TENANTED_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"""
            CREATE POLICY tenant_isolation ON {table}
                USING (
                    org_id::text = current_setting('app.current_org_id', true)
                )
                WITH CHECK (
                    org_id::text = current_setting('app.current_org_id', true)
                );
            """
        )


def downgrade() -> None:
    for table in TENANTED_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
