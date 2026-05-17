from sqlalchemy import Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Plan(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "plans"

    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    monthly_inr: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    monthly_lead_quota: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    features: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
