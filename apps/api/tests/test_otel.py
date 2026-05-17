import pytest


def test_otel_init_does_not_raise(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
    from app.observability.otel import init_otel

    init_otel()  # idempotent + no exception means pass


def test_traceparent_or_request_id_returned(client) -> None:
    response = client.get("/healthz")
    # The FastAPI instrumentor may add traceparent; we always have x-request-id.
    assert response.headers.get("x-request-id")
