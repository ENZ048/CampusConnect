def test_beat_schedule_includes_heartbeat():
    from app.worker.celery_app import celery_app
    assert "heartbeat" in celery_app.conf.beat_schedule
    entry = celery_app.conf.beat_schedule["heartbeat"]
    assert entry["task"] == "campusconnect.hello_world"
