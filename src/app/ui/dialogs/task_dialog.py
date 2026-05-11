from datetime import date

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QSpinBox,
    QVBoxLayout,
)

from app.application.dto.tasks import CreateTaskInput, CreateTaskSeriesInput, UpdateTaskInput
from app.application.services.tasks import (
    CreateTaskSeriesService,
    CreateTaskService,
    GenerateRecurringTasksService,
    GetTaskForEditService,
    UpdateTaskService,
)
from app.domain.enums import TaskRecurrenceType
from app.infrastructure.db.session import SessionLocal
from app.ui.date_edit import AppDateEdit
from app.ui.dialog_helpers import translate_button_box
from app.ui.localization import t


class TaskDialog(QDialog):
    def __init__(
        self,
        parent=None,
        default_due_date: date | None = None,
        default_order_id: int | None = None,
        default_order_label: str | None = None,
        task_id: int | None = None,
    ) -> None:
        super().__init__(parent)

        self._task_id = task_id
        self._order_id = default_order_id
        self.setWindowTitle(self._window_title())
        self.resize(460, 360)

        self._title_input = QLineEdit()
        self._due_date_input = AppDateEdit()
        due_date = default_due_date or date.today()
        self._due_date_input.setDate(QDate(due_date.year, due_date.month, due_date.day))
        self._notes_input = QPlainTextEdit()
        self._notes_input.setFixedHeight(100)

        self._recurring_checkbox = QCheckBox()
        self._recurrence_interval_input = QSpinBox()
        self._recurrence_interval_input.setMinimum(1)
        self._recurrence_interval_input.setMaximum(365)
        self._recurrence_type_input = QComboBox()
        self._recurrence_type_input.addItem(t("days"), TaskRecurrenceType.DAILY)
        self._recurrence_type_input.addItem(t("weeks"), TaskRecurrenceType.WEEKLY)
        self._recurrence_type_input.addItem(t("months"), TaskRecurrenceType.MONTHLY)
        self._ends_on_checkbox = QCheckBox()
        self._ends_on_input = AppDateEdit()
        self._ends_on_input.setDate(self._due_date_input.date())
        self._recurring_checkbox.toggled.connect(self._sync_recurring_controls)
        self._ends_on_checkbox.toggled.connect(self._sync_recurring_controls)

        form = QFormLayout()
        if self._order_id is not None:
            order_label = QLabel(default_order_label or str(self._order_id))
            order_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            order_label.setMinimumHeight(self._title_input.sizeHint().height())
            form.addRow(t("Order"), order_label)
        form.addRow(t("Title"), self._title_input)
        form.addRow(t("Due date"), self._due_date_input)
        form.addRow(t("Notes"), self._notes_input)

        if self._task_id is None and self._order_id is None:
            form.addRow(t("Recurring"), self._recurring_checkbox)
            form.addRow(t("Every"), self._recurrence_interval_input)
            form.addRow(t("Period"), self._recurrence_type_input)
            form.addRow(t("Ends"), self._ends_on_checkbox)
            form.addRow(t("End date"), self._ends_on_input)

        self._buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        translate_button_box(self._buttons)
        self._buttons.accepted.connect(self._on_accept)
        self._buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(self._buttons)
        self.setLayout(layout)

        if self._task_id is not None:
            self._load_task()
        self._sync_recurring_controls()

    def _window_title(self) -> str:
        if self._task_id is not None:
            return t("Edit Task")
        if self._order_id is not None:
            return t("Create Order Reminder")
        return t("Create Task")

    def _load_task(self) -> None:
        try:
            session = SessionLocal()
        except Exception as exc:
            QMessageBox.critical(self, t("Could not load task"), str(exc))
            return

        try:
            task = GetTaskForEditService(session).execute(self._task_id)
            self._title_input.setText(task.title)
            self._notes_input.setPlainText(task.notes or "")
            self._due_date_input.setDate(QDate(task.due_date.year, task.due_date.month, task.due_date.day))
        except Exception as exc:
            QMessageBox.critical(self, t("Could not load task"), t(str(exc)))
        finally:
            session.close()

    def _sync_recurring_controls(self) -> None:
        recurring_enabled = self._recurring_checkbox.isChecked()
        self._recurrence_interval_input.setEnabled(recurring_enabled)
        self._recurrence_type_input.setEnabled(recurring_enabled)
        self._ends_on_checkbox.setEnabled(recurring_enabled)
        self._ends_on_input.setEnabled(recurring_enabled and self._ends_on_checkbox.isChecked())

    def _on_accept(self) -> None:
        if self._task_id is not None:
            self._update_task()
            return
        if self._recurring_checkbox.isChecked() and self._order_id is None:
            self._create_recurring_task()
            return

        self._create_one_off_task()

    def _create_one_off_task(self) -> None:
        data = CreateTaskInput(
            title=self._title_input.text(),
            due_date=self._due_date_input.date().toPython(),
            notes=self._notes_input.toPlainText().strip() or None,
            order_id=self._order_id,
        )
        self._run_task_write(
            lambda session: CreateTaskService(session).execute(data),
            t("Could not create task"),
        )

    def _create_recurring_task(self) -> None:
        starts_on = self._due_date_input.date().toPython()
        data = CreateTaskSeriesInput(
            title=self._title_input.text(),
            notes=self._notes_input.toPlainText().strip() or None,
            recurrence_type=self._recurrence_type_input.currentData(),
            recurrence_interval=self._recurrence_interval_input.value(),
            starts_on=starts_on,
            ends_on=(
                self._ends_on_input.date().toPython()
                if self._ends_on_checkbox.isChecked()
                else None
            ),
        )

        def create_series(session):
            CreateTaskSeriesService(session).execute(data)
            GenerateRecurringTasksService(session).execute(date.today())

        self._run_task_write(create_series, t("Could not create task"))

    def _update_task(self) -> None:
        data = UpdateTaskInput(
            title=self._title_input.text(),
            due_date=self._due_date_input.date().toPython(),
            notes=self._notes_input.toPlainText().strip() or None,
        )
        self._run_task_write(
            lambda session: UpdateTaskService(session).execute(self._task_id, data),
            t("Could not update task"),
        )

    def _run_task_write(self, callback, error_title: str) -> None:
        try:
            session = SessionLocal()
        except Exception as exc:
            QMessageBox.critical(self, error_title, str(exc))
            return

        try:
            callback(session)
            session.commit()
            self.accept()
        except Exception as exc:
            session.rollback()
            QMessageBox.critical(self, error_title, t(str(exc)))
        finally:
            session.close()
