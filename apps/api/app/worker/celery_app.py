from celery import Celery

from app.config import get_settings
from app.observability.otel import init_otel
from app.observability.sentry import init_sentry

_settings = get_settings()


def _build() -> Celery:
    init_sentry()
    init_otel()
    app = Celery(
        "campusconnect",
        broker=_settings.CELERY_BROKER_URL,
        backend=_settings.CELERY_RESULT_BACKEND,
        include=["app.worker.tasks.hello"],
    )
    app.conf.update(
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        broker_connection_retry_on_startup=True,
        worker_prefetch_multiplier=1,
    )
    return app


celery_app = _build()

from app.worker.beat_schedule import BEAT_SCHEDULE  # noqa: E402

celery_app.conf.beat_schedule = BEAT_SCHEDULE
