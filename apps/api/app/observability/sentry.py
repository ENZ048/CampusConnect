import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from app.config import get_settings


def init_sentry() -> None:
    settings = get_settings()
    if not settings.SENTRY_DSN_API:
        return
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN_API,
        environment=settings.APP_ENV,
        traces_sample_rate=0.1,
        send_default_pii=False,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
            CeleryIntegration(),
        ],
    )
