from PySide6.QtWidgets import (
    QCheckBox,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.application.services.settings import ApplicationSettingsService
from app.infrastructure.db.session import SessionLocal


class SettingsPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self._title_label = QLabel("Settings")
        self._title_label.setObjectName("pageTitle")

        self._strict_order_workflow_checkbox = QCheckBox("Strict order workflow")
        self._strict_order_workflow_description = QLabel(
            "When enabled, only draft orders can be fully edited. When disabled, active orders "
            "can be edited with the same rules as drafts."
        )
        self._strict_order_workflow_description.setWordWrap(True)

        self._save_button = QPushButton("Save Settings")
        self._save_button.clicked.connect(self.save_settings)

        layout = QVBoxLayout()
        layout.addWidget(self._title_label)
        layout.addWidget(self._strict_order_workflow_checkbox)
        layout.addWidget(self._strict_order_workflow_description)
        layout.addWidget(self._save_button)
        layout.addStretch()
        self.setLayout(layout)

        self.load_settings()

    def load_settings(self) -> None:
        try:
            session = SessionLocal()
        except Exception as exc:
            QMessageBox.critical(self, "Could not load settings", str(exc))
            return

        try:
            settings = ApplicationSettingsService(session).get_settings()
            self._strict_order_workflow_checkbox.setChecked(settings.strict_order_workflow_enabled)
        except Exception as exc:
            QMessageBox.critical(self, "Could not load settings", str(exc))
        finally:
            session.close()

    def save_settings(self) -> None:
        try:
            session = SessionLocal()
        except Exception as exc:
            QMessageBox.critical(self, "Could not save settings", str(exc))
            return

        try:
            ApplicationSettingsService(session).set_strict_order_workflow_enabled(
                self._strict_order_workflow_checkbox.isChecked()
            )
            session.commit()
            QMessageBox.information(self, "Settings saved", "Settings saved.")
        except Exception as exc:
            session.rollback()
            QMessageBox.critical(self, "Could not save settings", str(exc))
        finally:
            session.close()
