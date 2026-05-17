from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)

from app.config import get_settings

_initialized = False


def init_otel() -> None:
    global _initialized
    if _initialized:
        return
    settings = get_settings()
    resource = Resource.create(
        {
            "service.name": settings.OTEL_SERVICE_NAME_API,
            "deployment.environment": settings.APP_ENV,
        }
    )
    provider = TracerProvider(resource=resource)

    if settings.OTEL_EXPORTER_OTLP_ENDPOINT:
        provider.add_span_processor(
            BatchSpanProcessor(
                OTLPSpanExporter(endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT)
            )
        )
    else:
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(provider)

    SQLAlchemyInstrumentor().instrument()
    CeleryInstrumentor().instrument()
    RedisInstrumentor().instrument()
    _initialized = True


def instrument_app(app: FastAPI) -> None:
    FastAPIInstrumentor.instrument_app(app)
