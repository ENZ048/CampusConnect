"""seed default plans

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-17 00:02:00.000000
"""
from collections.abc import Sequence

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
        '{"campaigns": true, "rag": true, "languages": ["en","hi","hinglish"], "sla": "24h", "sso": true}',
    ),
]


def upgrade() -> None:
    for code, name, monthly_inr, monthly_lead_quota, features_json in PLANS:
        op.execute(
            f"""
            INSERT INTO plans (id, code, name, monthly_inr, monthly_lead_quota, features)
            VALUES (gen_random_uuid(), '{code}', '{name}', {monthly_inr}, {monthly_lead_quota}, '{features_json}')
            ON CONFLICT (code) DO NOTHING
            """
        )


def downgrade() -> None:
    for code, *_ in PLANS:
        op.execute(f"DELETE FROM plans WHERE code = '{code}'")
