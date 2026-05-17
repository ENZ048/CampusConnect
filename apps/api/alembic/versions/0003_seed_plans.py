"""seed default plans

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-17 00:02:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


PLANS = [
    (
        "free",
        "Free",
        0,
        100,
        '{"campaigns": false, "rag": true, "languages": ["en","hi","hinglish"]}',
    ),
    (
        "growth",
        "Growth",
        299900,
        1000,
        '{"campaigns": true, "rag": true, "languages": ["en","hi","hinglish"]}',
    ),
    (
        "enterprise",
        "Enterprise",
        0,
        100000,
        (
            '{"campaigns": true, "rag": true, '
            '"languages": ["en","hi","hinglish"], "sla": "24h", "sso": true}'
        ),
    ),
]

_INSERT_SQL = sa.text(
    "INSERT INTO plans (id, code, name, monthly_inr, monthly_lead_quota, features) "
    "VALUES (gen_random_uuid(), :code, :name, :monthly_inr, :monthly_lead_quota, :features) "
    "ON CONFLICT (code) DO NOTHING"
)

_DELETE_SQL = sa.text("DELETE FROM plans WHERE code = :code")


def upgrade() -> None:
    conn = op.get_bind()
    for code, name, monthly_inr, monthly_lead_quota, features_json in PLANS:
        conn.execute(
            _INSERT_SQL,
            {
                "code": code,
                "name": name,
                "monthly_inr": monthly_inr,
                "monthly_lead_quota": monthly_lead_quota,
                "features": features_json,
            },
        )


def downgrade() -> None:
    conn = op.get_bind()
    for code, *_ in PLANS:
        conn.execute(_DELETE_SQL, {"code": code})
