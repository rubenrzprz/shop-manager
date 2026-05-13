from datetime import date

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
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

from app.application.dto.tasks import (
    DEFAULT_TASK_COLOR_HEX,
    CreateTaskInput,
    CreateTaskSeriesInput,
    UpdateTaskInput,
)
from app.application.services.tasks import (
    CreateTaskSeriesService,
    CreateTaskService,
    DeleteTaskService,
    GenerateRecurringTasksService,
    GetTaskForEditService,
    UpdateTaskService,
)
from app.domain.enums import (
    TaskMonthlyRecurrenceRule,
    TaskRecurrenceType,
    TaskSeriesUpdateScope,
)
from app.infrastructure.db.session import SessionLocal
from app.ui.date_edit import AppDateEdit
from app.ui.dialog_helpers import translate_button_box
from app.ui.localization import t
from app.ui.window_sizing import resize_to_available_screen


class TaskDialog(QDialog):
    _TASK_COLORS = [
        ("Light gray", "#e5e7eb"),
        ("Yellow", "#facc15"),
        ("Amber", "#d97706"),
        ("Orange", "#ea580c"),
        ("Red", "#dc2626"),
        ("Rose", "#e11d48"),
        ("Pink", "#db2777"),
        ("Purple", "#7c3aed"),
        ("Blue", "#2563eb"),
        ("Sky", "#0284c7"),
        ("Teal", "#0f766e"),
        ("Green", "#16a34a"),
        ("Lime", "#65a30d"),
        ("Brown", "#92400e"),
        ("Slate", "#475569"),
        ("Black", "#111827"),
    ]

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
        self._loaded_task_series_id: int | None = None
        self._selected_color_hex = DEFAULT_TASK_COLOR_HEX
        self.setWindowTitle(self._window_title())
        resize_to_available_screen(
            self,
            width_ratio=0.42,
            height_ratio=0.72,
            min_width=520,
            min_height=520,
        )

        self._title_input = QLineEdit()
        self._due_date_input = AppDateEdit()
        due_date = default_due_date or date.today()
        self._due_date_input.setDate(QDate(due_date.year, due_date.month, due_date.day))
        self._notes_input = QPlainTextEdit()
        self._notes_input.setFixedHeight(100)
        self._color_input = QComboBox()
        for label, color_hex in self._TASK_COLORS:
            self._color_input.addItem(self._color_icon(color_hex), t(label), color_hex)

        self._recurring_checkbox = QCheckBox()
        self._recurrence_interval_input = QSpinBox()
        self._recurrence_interval_input.setMinimum(1)
        self._recurrence_interval_input.setMaximum(365)
        self._recurrence_type_input = QComboBox()
        self._recurrence_type_input.addItem(t("days"), TaskRecurrenceType.DAILY)
        self._recurrence_type_input.addItem(t("weeks"), TaskRecurrenceType.WEEKLY)
        self._recurrence_type_input.addItem(t("months"), TaskRecurrenceType.MONTHLY)
        self._monthly_rule_input = QComboBox()
        self._monthly_rule_input.addItem(
            t("Same day as start date"),
            TaskMonthlyRecurrenceRule.DAY_OF_MONTH,
        )
        self._monthly_rule_input.addItem(
            t("First day of month"),
            TaskMonthlyRecurrenceRule.FIRST_DAY_OF_MONTH,
        )
        self._monthly_rule_input.addItem(
            t("Specific day of month"),
            TaskMonthlyRecurrenceRule.SPECIFIC_DAY_OF_MONTH,
        )
        self._monthly_rule_input.addItem(
            t("Last day of month"),
            TaskMonthlyRecurrenceRule.LAST_DAY_OF_MONTH,
        )
        self._monthly_day_input = QSpinBox()
        self._monthly_day_input.setMinimum(1)
        self._monthly_day_input.setMaximum(31)
        self._monthly_day_input.setValue(due_date.day)
        self._ends_on_checkbox = QCheckBox()
        self._ends_on_input = AppDateEdit()
        self._ends_on_input.setDate(self._due_date_input.date())
        self._update_scope_input = QComboBox()
        self._update_scope_input.addItem(t("This task only"), TaskSeriesUpdateScope.OCCURRENCE)
        self._update_scope_input.addItem(
            t("This and future tasks"),
            TaskSeriesUpdateScope.FUTURE,
        )
        self._update_scope_input.addItem(t("Whole series"), TaskSeriesUpdateScope.SERIES)
        self._recurring_checkbox.toggled.connect(self._sync_recurring_controls)
        self._recurrence_type_input.currentIndexChanged.connect(self._sync_recurring_controls)
        self._monthly_rule_input.currentIndexChanged.connect(self._sync_recurring_controls)
        self._update_scope_input.currentIndexChanged.connect(self._sync_recurring_controls)
        self._ends_on_checkbox.toggled.connect(self._sync_recurring_controls)

        form = QFormLayout()
        self._form = form
        if self._order_id is not None:
            order_label = QLabel(default_order_label or str(self._order_id))
            order_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            order_label.setMinimumHeight(self._title_input.sizeHint().height())
            form.addRow(t("Order"), order_label)
        form.addRow(t("Title"), self._title_input)
        form.addRow(t("Due date"), self._due_date_input)
        form.addRow(t("Color"), self._color_input)
        form.addRow(t("Notes"), self._notes_input)

        self._recurring_label = QLabel()
        if self._task_id is not None:
            form.addRow(t("Apply to"), self._update_scope_input)
        if self._task_id is None:
            form.addRow(t("Recurring"), self._recurring_checkbox)
        form.addRow(t("Every"), self._recurrence_interval_input)
        form.addRow(t("Period"), self._recurrence_type_input)
        form.addRow(t("Monthly rule"), self._monthly_rule_input)
        form.addRow(t("Day of month"), self._monthly_day_input)
        form.addRow(t("Ends"), self._ends_on_checkbox)
        form.addRow(t("End date"), self._ends_on_input)

        self._buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        translate_button_box(self._buttons)
        if self._task_id is not None:
            self._delete_button = self._buttons.addButton(
                t("Delete"),
                QDialogButtonBox.DestructiveRole,
            )
            self._delete_button.clicked.connect(self._delete_task)
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
            self._loaded_task_series_id = task.task_series_id
            self._title_input.setText(task.title)
            self._notes_input.setPlainText(task.notes or "")
            self._set_combo_value(self._color_input, task.color_hex)
            self._due_date_input.setDate(
                QDate(task.due_date.year, task.due_date.month, task.due_date.day)
            )
            if task.task_series_id is not None:
                self._set_combo_value(self._recurrence_type_input, task.recurrence_type)
                self._recurrence_interval_input.setValue(task.recurrence_interval or 1)
                self._set_combo_value(
                    self._monthly_rule_input,
                    task.monthly_rule or TaskMonthlyRecurrenceRule.DAY_OF_MONTH,
                )
                self._monthly_day_input.setValue(task.monthly_day or task.due_date.day)
                if task.series_ends_on is not None:
                    self._ends_on_checkbox.setChecked(True)
                    self._ends_on_input.setDate(
                        QDate(
                            task.series_ends_on.year,
                            task.series_ends_on.month,
                            task.series_ends_on.day,
                        )
                    )
            else:
                self._form.setRowVisible(self._update_scope_input, False)
        except Exception as exc:
            QMessageBox.critical(self, t("Could not load task"), t(str(exc)))
        finally:
            session.close()

    def _sync_recurring_controls(self) -> None:
        editing_series = (
            self._task_id is not None
            and self._loaded_task_series_id is not None
            and self._update_scope_input.currentData() != TaskSeriesUpdateScope.OCCURRENCE
        )
        recurring_enabled = self._recurring_checkbox.isChecked() or editing_series
        self._recurrence_interval_input.setEnabled(recurring_enabled)
        self._recurrence_type_input.setEnabled(recurring_enabled)
        self._monthly_rule_input.setEnabled(
            recurring_enabled
            and self._recurrence_type_input.currentData() == TaskRecurrenceType.MONTHLY
        )
        monthly_day_visible = (
            recurring_enabled
            and self._recurrence_type_input.currentData() == TaskRecurrenceType.MONTHLY
            and self._monthly_rule_input.currentData()
            == TaskMonthlyRecurrenceRule.SPECIFIC_DAY_OF_MONTH
        )
        self._monthly_day_input.setEnabled(monthly_day_visible)
        self._ends_on_checkbox.setEnabled(recurring_enabled)
        self._ends_on_input.setEnabled(recurring_enabled and self._ends_on_checkbox.isChecked())
        show_recurring_controls = self._task_id is None or self._loaded_task_series_id is not None
        self._recurrence_interval_input.setVisible(show_recurring_controls)
        self._recurrence_type_input.setVisible(show_recurring_controls)
        self._monthly_rule_input.setVisible(show_recurring_controls)
        self._monthly_day_input.setVisible(show_recurring_controls and monthly_day_visible)
        self._ends_on_checkbox.setVisible(show_recurring_controls)
        self._ends_on_input.setVisible(show_recurring_controls)
        self._form.setRowVisible(self._recurrence_interval_input, show_recurring_controls)
        self._form.setRowVisible(self._recurrence_type_input, show_recurring_controls)
        self._form.setRowVisible(self._monthly_rule_input, show_recurring_controls)
        self._form.setRowVisible(
            self._monthly_day_input,
            show_recurring_controls and monthly_day_visible,
        )
        self._form.setRowVisible(self._ends_on_checkbox, show_recurring_controls)
        self._form.setRowVisible(self._ends_on_input, show_recurring_controls)

    def _on_accept(self) -> None:
        if self._task_id is not None:
            self._update_task()
            return
        if self._recurring_checkbox.isChecked():
            self._create_recurring_task()
            return

        self._create_one_off_task()

    def _create_one_off_task(self) -> None:
        data = CreateTaskInput(
            title=self._title_input.text(),
            due_date=self._due_date_input.date().toPython(),
            notes=self._notes_input.toPlainText().strip() or None,
            order_id=self._order_id,
            color_hex=self._color_input.currentData(),
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
            color_hex=self._color_input.currentData(),
            monthly_rule=self._monthly_rule_input.currentData(),
            monthly_day=(
                self._monthly_day_input.value()
                if self._monthly_rule_input.currentData()
                == TaskMonthlyRecurrenceRule.SPECIFIC_DAY_OF_MONTH
                else None
            ),
            order_id=self._order_id,
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
            color_hex=self._color_input.currentData(),
            update_scope=self._update_scope_input.currentData(),
            recurrence_type=self._recurrence_type_input.currentData(),
            recurrence_interval=self._recurrence_interval_input.value(),
            monthly_rule=self._monthly_rule_input.currentData(),
            monthly_day=(
                self._monthly_day_input.value()
                if self._monthly_rule_input.currentData()
                == TaskMonthlyRecurrenceRule.SPECIFIC_DAY_OF_MONTH
                else None
            ),
            ends_on=(
                self._ends_on_input.date().toPython()
                if self._ends_on_checkbox.isChecked()
                else None
            ),
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

    def _delete_task(self) -> None:
        if self._task_id is None:
            return

        scope = self._confirm_delete_scope()
        if scope is None:
            return

        self._run_task_write(
            lambda session: DeleteTaskService(session).execute(self._task_id, scope),
            t("Could not delete task"),
        )

    def _confirm_delete_scope(self) -> TaskSeriesUpdateScope | None:
        if self._loaded_task_series_id is None:
            message_box = QMessageBox(self)
            message_box.setIcon(QMessageBox.Question)
            message_box.setWindowTitle(t("Delete task"))
            message_box.setText(t("Delete this task?"))
            message_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            message_box.setDefaultButton(QMessageBox.No)
            return (
                TaskSeriesUpdateScope.OCCURRENCE if message_box.exec() == QMessageBox.Yes else None
            )

        message_box = QMessageBox(self)
        message_box.setIcon(QMessageBox.Question)
        message_box.setWindowTitle(t("Delete recurring task"))
        message_box.setText(t("Delete which recurring tasks?"))
        occurrence_button = message_box.addButton(
            t("This task only"),
            QMessageBox.AcceptRole,
        )
        future_button = message_box.addButton(
            t("This and future tasks"),
            QMessageBox.AcceptRole,
        )
        message_box.addButton(t("Cancel"), QMessageBox.RejectRole)
        message_box.exec()
        clicked_button = message_box.clickedButton()
        if clicked_button == occurrence_button:
            return TaskSeriesUpdateScope.OCCURRENCE
        if clicked_button == future_button:
            return TaskSeriesUpdateScope.FUTURE

        return None

    @staticmethod
    def _color_icon(color_hex: str) -> QIcon:
        pixmap = QPixmap(18, 18)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(color_hex))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(3, 3, 12, 12)
        painter.end()
        return QIcon(pixmap)

    @staticmethod
    def _set_combo_value(combo: QComboBox, value) -> None:
        for index in range(combo.count()):
            if combo.itemData(index) == value:
                combo.setCurrentIndex(index)
                return
