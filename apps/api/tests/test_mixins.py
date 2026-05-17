import uuid

from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column


def test_tenanted_mixin_adds_org_id_column():
    from app.db.base import Base
    from app.models.mixins import TenantedMixin

    class _Foo(TenantedMixin, Base):
        __tablename__ = "_foo_test_tenanted"
        id: Mapped[int] = mapped_column(Integer, primary_key=True)

    cols = {c.name for c in _Foo.__table__.columns}
    assert "org_id" in cols
    assert "id" in cols


def test_timestamp_mixin_adds_created_at_updated_at():
    from app.db.base import Base
    from app.models.mixins import TimestampMixin

    class _Bar(TimestampMixin, Base):
        __tablename__ = "_bar_test_timestamp"
        id: Mapped[int] = mapped_column(Integer, primary_key=True)

    cols = {c.name for c in _Bar.__table__.columns}
    assert "created_at" in cols
    assert "updated_at" in cols


def test_uuid_pk_mixin_uses_uuid_default():
    from app.db.base import Base
    from app.models.mixins import UUIDPrimaryKeyMixin

    class _Baz(UUIDPrimaryKeyMixin, Base):
        __tablename__ = "_baz_test_uuid"

    inst = _Baz()
    assert isinstance(inst.id, uuid.UUID)
