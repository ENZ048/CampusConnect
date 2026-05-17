from fastapi import FastAPI

from app.middleware.request_id import RequestIDMiddleware


def create_app() -> FastAPI:
    app = FastAPI(
        title="CampusConnect API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.add_middleware(RequestIDMiddleware)
    return app


app = create_app()
