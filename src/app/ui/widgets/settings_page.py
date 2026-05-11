from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.application.services.settings import (
    MAX_DEFAULT_ORDER_FOLLOW_UP_DAYS,
    MAX_TASK_GENERATION_HORIZON_DAYS,
    MIN_DEFAULT_ORDER_FOLLOW_UP_DAYS,
    MIN_TASK_GENERATION_HORIZON_DAYS,
    ApplicationSettingsService,
)
from app.domain.enums import OrderStatus
from app.infrastructure.db.session import SessionLocal
from app.ui.dialog_helpers import question
from app.ui.localization import SUPPORTED_LANGUAGES, order_status_label, set_language, t


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
        self._task_generation_horizon_label = QLabel()
        self._task_generation_horizon_input = QSpinBox()
        self._task_generation_horizon_input.setRange(
            MIN_TASK_GENERATION_HORIZON_DAYS,
            MAX_TASK_GENERATION_HORIZON_DAYS,
        )
        self._task_generation_horizon_input.setSuffix(" days")
        self._task_generation_horizon_description = QLabel()
        self._task_generation_horizon_description.setWordWrap(True)
        self._default_order_follow_up_label = QLabel()
        self._default_order_follow_up_input = QSpinBox()
        self._default_order_follow_up_input.setRange(
            MIN_DEFAULT_ORDER_FOLLOW_UP_DAYS,
            MAX_DEFAULT_ORDER_FOLLOW_UP_DAYS,
        )
        self._default_order_follow_up_description = QLabel()
        self._default_order_follow_up_description.setWordWrap(True)
        self._strict_order_workflow_checkbox = QCheckBox()
        self._strict_order_workflow_description = QLabel()
        self._strict_order_workflow_description.setWordWrap(True)

        self._order_status_group = QGroupBox()
        self._order_status_description = QLabel()
        self._order_status_description.setWordWrap(True)
        self._order_status_checkboxes: dict[OrderStatus, QCheckBox] = {}
        order_status_layout = QVBoxLayout()
        order_status_layout.addWidget(self._order_status_description)
        for status in (
            OrderStatus.DRAFT,
            OrderStatus.CONFIRMED,
            OrderStatus.IN_PROGRESS,
            OrderStatus.READY,
            OrderStatus.COMPLETED,
            OrderStatus.CANCELLED,
        ):
            checkbox = QCheckBox()
            if status in {OrderStatus.DRAFT, OrderStatus.COMPLETED, OrderStatus.CANCELLED}:
                checkbox.setChecked(True)
                checkbox.setEnabled(False)
            self._order_status_checkboxes[status] = checkbox
            order_status_layout.addWidget(checkbox)
        self._order_status_group.setLayout(order_status_layout)

        self._save_button = QPushButton()
        self._save_button.clicked.connect(self.save_settings)

        self._form = QFormLayout()
        self._form.addRow(self._language_label, self._language_input)
        self._form.addRow(
            self._task_generation_horizon_label,
            self._task_generation_horizon_input,
        )
        self._form.addRow(
            self._default_order_follow_up_label,
            self._default_order_follow_up_input,
        )

        layout = QVBoxLayout()
        layout.addWidget(self._title_label)
        layout.addLayout(self._form)
        layout.addWidget(self._task_generation_horizon_description)
        layout.addWidget(self._default_order_follow_up_description)
        layout.addWidget(self._strict_order_workflow_checkbox)
        layout.addWidget(self._strict_order_workflow_description)
        layout.addWidget(self._order_status_group)
        layout.addWidget(self._save_button)
        layout.addStretch()
        self.setLayout(layout)

        self.retranslate_ui()
        self.load_settings()

    def retranslate_ui(self) -> None:
        self._title_label.setText(t("Settings"))
        self._language_label.setText(t("Language"))
        self._task_generation_horizon_label.setText(t("Task generation horizon"))
        self._task_generation_horizon_input.setSuffix(f" {t('days')}")
        self._task_generation_horizon_description.setText(
            t("Recurring task occurrences are generated this many days ahead.")
        )
        self._default_order_follow_up_label.setText(t("Default order follow-up"))
        self._default_order_follow_up_input.setSuffix(f" {t('days')}")
        self._default_order_follow_up_description.setText(
            t("Automatic active-order follow-up reminders repeat after this many days.")
        )
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
        self._order_status_group.setTitle(t("Enabled order statuses"))
        self._order_status_description.setText(
            t(
                "Choose which statuses are used when advancing or reverting orders. Draft, "
                "completed, and cancelled are always required."
            )
        )
        for status, checkbox in self._order_status_checkboxes.items():
            checkbox.setText(t(status.value.title().replace("_", " ")))
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
            self._task_generation_horizon_input.setValue(settings.task_generation_horizon_days)
            self._default_order_follow_up_input.setValue(settings.default_order_follow_up_days)
            for status, checkbox in self._order_status_checkboxes.items():
                checkbox.setChecked(status in settings.enabled_order_statuses)
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
            enabled_order_statuses = self._enabled_order_statuses_value()
            conversion_counts = service.disabled_order_status_conversion_counts(
                enabled_order_statuses
            )
            if conversion_counts and not self._confirm_disabled_status_conversion(
                conversion_counts
            ):
                return

            service.set_app_language(selected_language)
            service.set_strict_order_workflow_enabled(
                self._strict_order_workflow_checkbox.isChecked()
            )
            service.set_task_generation_horizon_days(self._task_generation_horizon_input.value())
            service.set_default_order_follow_up_days(self._default_order_follow_up_input.value())
            service.set_enabled_order_statuses(enabled_order_statuses)
            session.commit()
            set_language(selected_language)
            self.language_changed.emit(selected_language)
            QMessageBox.information(self, t("Settings saved"), t("Settings saved."))
        except Exception as exc:
            session.rollback()
            QMessageBox.critical(self, t("Could not save settings"), str(exc))
        finally:
            session.close()

    def _enabled_order_statuses_value(self) -> tuple[OrderStatus, ...]:
        return tuple(
            status
            for status, checkbox in self._order_status_checkboxes.items()
            if checkbox.isChecked()
        )

    def _confirm_disabled_status_conversion(
        self,
        conversion_counts: dict[OrderStatus, int],
    ) -> bool:
        status_summary = ", ".join(
            f"{order_status_label(status)} ({count})" for status, count in conversion_counts.items()
        )
        response = question(
            self,
            t("Disable order statuses"),
            (
                f"{t('Orders currently in disabled statuses will be converted to draft:')} "
                f"{status_summary}\n\n{t('Continue saving settings?')}"
            ),
        )
        return response == QMessageBox.Yes
