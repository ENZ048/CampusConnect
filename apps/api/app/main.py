from fastapi import FastAPI


def create_app() -> FastAPI:
    return FastAPI(
        title="CampusConnect API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )


app = create_app()
