from app.worker.celery_app import celery_app


@celery_app.task(name="campusconnect.hello_world")
def hello_world(name: str) -> dict[str, str]:
    return {"greeting": f"Hello, {name}!", "from": "campusconnect-worker"}
