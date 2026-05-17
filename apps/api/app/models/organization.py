import uuid

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

ORG_STATUS = SAEnum("trial", "active", "past_due", "suspended", name="org_status")
LANGUAGE = SAEnum("en", "hi", "hinglish", name="language_code")
DATA_RESIDENCY = SAEnum("in", "us", "eu", name="data_residency")


class Organization(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(256), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    plan_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("plans.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(ORG_STATUS, nullable=False, default="trial")
    default_language: Mapped[str] = mapped_column(LANGUAGE, nullable=False, default="hinglish")
    branding: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    data_residency: Mapped[str] = mapped_column(DATA_RESIDENCY, nullable=False, default="in")
