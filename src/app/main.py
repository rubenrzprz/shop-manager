import logging
import sys

from PySide6.QtWidgets import QApplication

from app.application.services.tasks import (
    GenerateOrderFollowUpTasksService,
    GenerateRecurringTasksService,
)
from app.infrastructure.db.session import SessionLocal
from app.ui.styles import APP_STYLESHEET
from app.ui.windows.main_window import MainWindow

logger = logging.getLogger(__name__)


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Shop Manager")
    app.setApplicationDisplayName("Shop Manager")

    app.setStyleSheet(APP_STYLESHEET)

    _generate_recurring_tasks()

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


def _generate_recurring_tasks() -> None:
    try:
        session = SessionLocal()
    except Exception:
        logger.exception("Could not open a database session for recurring task generation.")
        return

    try:
        GenerateRecurringTasksService(session).execute()
        GenerateOrderFollowUpTasksService(session).execute()
        session.commit()
    except Exception:
        session.rollback()
        logger.exception("Could not generate recurring tasks on startup.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
