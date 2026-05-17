def test_app_is_a_fastapi_instance(app):
    from fastapi import FastAPI
    assert isinstance(app, FastAPI)


def test_app_has_a_title(app):
    assert app.title == "CampusConnect API"
