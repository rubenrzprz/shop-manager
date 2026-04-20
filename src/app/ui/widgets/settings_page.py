from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.application.services.settings import ApplicationSettingsService
from app.infrastructure.db.session import SessionLocal
from app.ui.localization import SUPPORTED_LANGUAGES, set_language, t


class SettingsPage(QWidget):
    language_changed = Signal(str)

    def __init__(self) -> None:
        super().__init__()

        self._title_label = QLabel()
        self._title_label.setObjectName("pageTitle")

        self._language_input = QComboBox()
        for language_code, language_name in SUPPORTED_LANGUAGES.items():
            self._language_input.addItem(language_name, language_code)

        self._language_label = QLabel()
        self._strict_order_workflow_checkbox = QCheckBox()
        self._strict_order_workflow_description = QLabel()
        self._strict_order_workflow_description.setWordWrap(True)

        self._save_button = QPushButton()
        self._save_button.clicked.connect(self.save_settings)

        self._form = QFormLayout()
        self._form.addRow(self._language_label, self._language_input)

        layout = QVBoxLayout()
        layout.addWidget(self._title_label)
        layout.addLayout(self._form)
        layout.addWidget(self._strict_order_workflow_checkbox)
        layout.addWidget(self._strict_order_workflow_description)
        layout.addWidget(self._save_button)
        layout.addStretch()
        self.setLayout(layout)

        self.retranslate_ui()
        self.load_settings()

    def retranslate_ui(self) -> None:
        self._title_label.setText(t("Settings"))
        self._language_label.setText(t("Language"))
        for index in range(self._language_input.count()):
            language_code = self._language_input.itemData(index)
            language_name = "Spanish" if language_code == "es" else "English"
            self._language_input.setItemText(index, t(language_name))
        self._strict_order_workflow_checkbox.setText(t("Strict order workflow"))
        self._strict_order_workflow_description.setText(
            t(
                "When enabled, only draft orders can be fully edited. When disabled, active orders "
                "can be edited with the same rules as drafts."
            )
        )
        self._save_button.setText(t("Save Settings"))

    def load_settings(self) -> None:
        try:
            session = SessionLocal()
        except Exception as exc:
            QMessageBox.critical(self, t("Could not load settings"), str(exc))
            return

        try:
            settings = ApplicationSettingsService(session).get_settings()
            language_index = self._language_input.findData(settings.app_language)
            if language_index >= 0:
                self._language_input.setCurrentIndex(language_index)
            self._strict_order_workflow_checkbox.setChecked(settings.strict_order_workflow_enabled)
        except Exception as exc:
            QMessageBox.critical(self, t("Could not load settings"), str(exc))
        finally:
            session.close()

    def save_settings(self) -> None:
        try:
            session = SessionLocal()
        except Exception as exc:
            QMessageBox.critical(self, t("Could not save settings"), str(exc))
            return

        try:
            service = ApplicationSettingsService(session)
            selected_language = self._language_input.currentData()
            service.set_app_language(selected_language)
            service.set_strict_order_workflow_enabled(
                self._strict_order_workflow_checkbox.isChecked()
            )
            session.commit()
            set_language(selected_language)
            self.language_changed.emit(selected_language)
            QMessageBox.information(self, t("Settings saved"), t("Settings saved."))
        except Exception as exc:
            session.rollback()
            QMessageBox.critical(self, t("Could not save settings"), str(exc))
        finally:
            session.close()
