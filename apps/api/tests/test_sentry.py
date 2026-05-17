import pytest


def test_sentry_init_is_a_no_op_when_dsn_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SENTRY_DSN_API", raising=False)
    from app.observability.sentry import init_sentry

    init_sentry()  # no exception means pass


def test_sentry_init_is_called_during_app_create(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[None] = []

    def fake_init() -> None:
        calls.append(None)

    monkeypatch.setattr("app.observability.sentry.init_sentry", fake_init)

    import app.main

    before = len(calls)
    app.main.create_app()
    assert len(calls) > before
