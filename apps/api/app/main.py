from fastapi import FastAPI

from app.middleware.request_id import RequestIDMiddleware
from app.routers import health, metrics


def create_app() -> FastAPI:
    from app.observability.otel import init_otel, instrument_app
    from app.observability.sentry import init_sentry

    init_sentry()
    init_otel()
    app = FastAPI(
        title="CampusConnect API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.add_middleware(RequestIDMiddleware)
    app.include_router(health.router)
    app.include_router(metrics.router)
    instrument_app(app)
    return app


app = create_app()
