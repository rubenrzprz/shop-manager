import sys

from PySide6.QtWidgets import QApplication

from app.application.services.tasks import GenerateRecurringTasksService
from app.infrastructure.db.session import SessionLocal
from app.ui.windows.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)

    app.setStyleSheet("""
        QWidget {
            font-size: 13px;
        }

        QLabel#pageTitle {
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 8px;
        }

        QTableWidget {
            gridline-color: #d0d0d0;
        }

        QHeaderView::section {
            background-color: #f3f4f6;
            border: 0;
            border-bottom: 1px solid #c8cdd3;
            border-right: 1px solid #d9dde2;
            font-weight: 600;
            padding: 6px 8px;
        }

        QPushButton {
            min-height: 30px;
            padding: 4px 10px;
        }
    """)

    _generate_recurring_tasks()

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


def _generate_recurring_tasks() -> None:
    try:
        session = SessionLocal()
    except Exception:
        return

    try:
        GenerateRecurringTasksService(session).execute()
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    main()
