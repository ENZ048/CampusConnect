from fastapi import APIRouter, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    generate_latest,
    multiprocess,
)

router = APIRouter(tags=["metrics"])

REQUESTS = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)


@router.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    registry = CollectorRegistry()
    try:
        multiprocess.MultiProcessCollector(registry)  # type: ignore[no-untyped-call]
        data = generate_latest(registry)
    except (ValueError, OSError):
        data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
