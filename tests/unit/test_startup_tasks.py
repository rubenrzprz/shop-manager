import logging

import app.main as main_module


class FakeSession:
    def __init__(self) -> None:
        self.rolled_back = False
        self.closed = False

    def commit(self) -> None:
        raise AssertionError("commit should not be called after generation fails")

    def rollback(self) -> None:
        self.rolled_back = True

    def close(self) -> None:
        self.closed = True


class FailingGenerateRecurringTasksService:
    def __init__(self, session) -> None:
        self._session = session

    def execute(self) -> int:
        raise RuntimeError("generation failed")


def test_generate_recurring_tasks_logs_generation_errors(monkeypatch, caplog):
    session = FakeSession()
    monkeypatch.setattr(main_module, "SessionLocal", lambda: session)
    monkeypatch.setattr(
        main_module,
        "GenerateRecurringTasksService",
        FailingGenerateRecurringTasksService,
    )

    with caplog.at_level(logging.ERROR):
        main_module._generate_recurring_tasks()

    assert session.rolled_back
    assert session.closed
    assert "Could not generate recurring tasks on startup." in caplog.text


def test_generate_recurring_tasks_logs_session_errors(monkeypatch, caplog):
    def fail_session():
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(main_module, "SessionLocal", fail_session)

    with caplog.at_level(logging.ERROR):
        main_module._generate_recurring_tasks()

    assert "Could not open a database session for recurring task generation." in caplog.text
