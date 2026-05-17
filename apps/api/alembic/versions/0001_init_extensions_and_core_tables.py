"""init extensions and core tables

Revision ID: 0001
Revises:
Create Date: 2026-05-17 00:00:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()

    conn.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector"))
    conn.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
    conn.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))

    conn.execute(sa.text("CREATE TYPE org_status AS ENUM ('trial', 'active', 'past_due', 'suspended')"))
    conn.execute(sa.text("CREATE TYPE language_code AS ENUM ('en', 'hi', 'hinglish')"))
    conn.execute(sa.text("CREATE TYPE data_residency AS ENUM ('in', 'us', 'eu')"))
    conn.execute(sa.text("CREATE TYPE user_role AS ENUM ('platform_admin', 'org_admin', 'counsellor')"))
    conn.execute(sa.text("CREATE TYPE user_status AS ENUM ('invited', 'active', 'disabled')"))

    conn.execute(sa.text("""
        CREATE TABLE plans (
            id          UUID PRIMARY KEY,
            code        VARCHAR(32)  NOT NULL UNIQUE,
            name        VARCHAR(128) NOT NULL,
            monthly_inr INTEGER      NOT NULL DEFAULT 0,
            monthly_lead_quota INTEGER NOT NULL DEFAULT 0,
            features    JSONB        NOT NULL DEFAULT '{}',
            created_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
            updated_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
        )
    """))

    conn.execute(sa.text("""
        CREATE TABLE organizations (
            id               UUID PRIMARY KEY,
            name             VARCHAR(256)   NOT NULL,
            slug             VARCHAR(64)    NOT NULL UNIQUE,
            plan_id          UUID           REFERENCES plans(id),
            status           org_status     NOT NULL DEFAULT 'trial',
            default_language language_code  NOT NULL DEFAULT 'hinglish',
            branding         JSONB          NOT NULL DEFAULT '{}',
            data_residency   data_residency NOT NULL DEFAULT 'in',
            created_at       TIMESTAMPTZ    NOT NULL DEFAULT now(),
            updated_at       TIMESTAMPTZ    NOT NULL DEFAULT now()
        )
    """))

    conn.execute(sa.text("""
        CREATE TABLE users (
            id          UUID PRIMARY KEY,
            org_id      UUID        REFERENCES organizations(id) ON DELETE CASCADE,
            email       VARCHAR(320) NOT NULL UNIQUE,
            name        VARCHAR(256),
            role        user_role   NOT NULL DEFAULT 'org_admin',
            status      user_status NOT NULL DEFAULT 'invited',
            last_seen_at TIMESTAMPTZ,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """))
    conn.execute(sa.text("CREATE INDEX ix_users_org_id ON users (org_id)"))
    conn.execute(sa.text("CREATE INDEX ix_users_email  ON users (email)"))

    conn.execute(sa.text("""
        CREATE TABLE audit_log (
            id            UUID PRIMARY KEY,
            org_id        UUID        NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
            actor_user_id UUID        REFERENCES users(id) ON DELETE SET NULL,
            action        VARCHAR(64) NOT NULL,
            target_type   VARCHAR(64),
            target_id     UUID,
            meta          JSONB       NOT NULL DEFAULT '{}',
            created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """))
    conn.execute(sa.text("CREATE INDEX ix_audit_log_org_id ON audit_log (org_id)"))
    conn.execute(sa.text("CREATE INDEX ix_audit_log_action ON audit_log (action)"))


def downgrade() -> None:
    conn = op.get_bind()

    conn.execute(sa.text("DROP INDEX IF EXISTS ix_audit_log_action"))
    conn.execute(sa.text("DROP INDEX IF EXISTS ix_audit_log_org_id"))
    conn.execute(sa.text("DROP TABLE IF EXISTS audit_log"))

    conn.execute(sa.text("DROP INDEX IF EXISTS ix_users_email"))
    conn.execute(sa.text("DROP INDEX IF EXISTS ix_users_org_id"))
    conn.execute(sa.text("DROP TABLE IF EXISTS users"))

    conn.execute(sa.text("DROP TABLE IF EXISTS organizations"))
    conn.execute(sa.text("DROP TABLE IF EXISTS plans"))

    for enum_name in ("user_status", "user_role", "data_residency", "language_code", "org_status"):
        conn.execute(sa.text(f"DROP TYPE IF EXISTS {enum_name}"))
