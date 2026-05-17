import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

from sqlalchemy import event
from sqlalchemy.orm import Session, with_loader_criteria

from app.models.mixins import TenantedMixin

_current_org: ContextVar[uuid.UUID | None] = ContextVar("current_org", default=None)
_bypass: ContextVar[bool] = ContextVar("bypass_tenant_filter", default=False)
_listeners_installed = False


@contextmanager
def set_current_org(org_id: uuid.UUID) -> Iterator[None]:
    token = _current_org.set(org_id)
    try:
        yield
    finally:
        _current_org.reset(token)


@contextmanager
def bypass_tenant_filter() -> Iterator[None]:
    token = _bypass.set(True)
    try:
        yield
    finally:
        _bypass.reset(token)


def install_listeners() -> None:
    """SQLAlchemy 2.x: hook into Session.do_orm_execute and inject a
    with_loader_criteria filter on every TenantedMixin SELECT.

    Idempotent — safe to call multiple times."""
    global _listeners_installed
    if _listeners_installed:
        return
    _listeners_installed = True

    @event.listens_for(Session, "do_orm_execute")
    def _do_orm_execute(state):  # type: ignore[no-untyped-def]
        if _bypass.get():
            return
        if not state.is_select:
            return
        org = _current_org.get()
        if org is None:
            return
        state.statement = state.statement.options(
            with_loader_criteria(
                TenantedMixin,
                lambda cls: cls.org_id == org,
                include_aliases=True,
            )
        )
