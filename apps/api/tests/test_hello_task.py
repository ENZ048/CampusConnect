def test_hello_task_runs_eagerly_and_returns_payload(monkeypatch):
    monkeypatch.setenv("CELERY_BROKER_URL", "memory://")
    monkeypatch.setenv("CELERY_RESULT_BACKEND", "cache+memory://")
    from app.worker.celery_app import celery_app
    from app.worker.tasks.hello import hello_world

    celery_app.conf.task_always_eager = True
    result = hello_world.delay("Pratik")
    payload = result.get()
    assert payload["greeting"] == "Hello, Pratik!"
    assert payload["from"] == "campusconnect-worker"
