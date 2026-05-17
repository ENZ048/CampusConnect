from celery.schedules import crontab

BEAT_SCHEDULE = {
    "heartbeat": {
        "task": "campusconnect.hello_world",
        "schedule": crontab(minute="*"),
        "args": ("beat",),
    },
}
