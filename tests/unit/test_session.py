import importlib


def test_session_module_imports_without_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    session_module = importlib.import_module("app.infrastructure.db.session")
    session_module = importlib.reload(session_module)

    assert session_module._engine is None


def test_get_engine_raises_when_database_url_is_missing(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    session_module = importlib.import_module("app.infrastructure.db.session")
    session_module = importlib.reload(session_module)

    try:
        session_module.get_engine()
    except RuntimeError as exc:
        assert str(exc) == "DATABASE_URL is not configured."
    else:
        raise AssertionError("Expected get_engine() to fail without DATABASE_URL.")
