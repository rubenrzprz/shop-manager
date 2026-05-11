from datetime import date

from PySide6.QtCore import QDate, Signal
from PySide6.QtWidgets import (
    QDateEdit,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.application.dto.tasks import TaskListItem
from app.application.services.tasks import (
    CompleteTaskService,
    ListDashboardTasksService,
    ReopenTaskService,
)
from app.infrastructure.db.session import SessionLocal
from app.ui.dialogs.task_dialog import TaskDialog
from app.ui.localization import t


class DashboardPage(QWidget):
    action_requested = Signal(str)
    task_changed = Signal()

    def __init__(self) -> None:
        super().__init__()

        self._title_label = QLabel()
        self._title_label.setObjectName("pageTitle")

        self._shortcuts_group = QGroupBox()
        self._products_button = QPushButton()
        self._suppliers_button = QPushButton()
        self._customers_button = QPushButton()
        self._orders_button = QPushButton()
        self._settings_button = QPushButton()

        self._products_button.clicked.connect(lambda: self.action_requested.emit("new_product"))
        self._suppliers_button.clicked.connect(lambda: self.action_requested.emit("new_supplier"))
        self._customers_button.clicked.connect(lambda: self.action_requested.emit("new_customer"))
        self._orders_button.clicked.connect(lambda: self.action_requested.emit("new_order"))
        self._settings_button.clicked.connect(lambda: self.action_requested.emit("settings"))

        shortcuts_layout = QGridLayout()
        shortcuts_layout.addWidget(self._products_button, 0, 0)
        shortcuts_layout.addWidget(self._suppliers_button, 0, 1)
        shortcuts_layout.addWidget(self._customers_button, 0, 2)
        shortcuts_layout.addWidget(self._orders_button, 1, 0)
        shortcuts_layout.addWidget(self._settings_button, 1, 1)
        self._shortcuts_group.setLayout(shortcuts_layout)

        self._daily_tasks_group = QGroupBox()
        self._selected_date_label = QLabel()
        self._selected_date_input = QDateEdit()
        self._selected_date_input.setCalendarPopup(True)
        today = date.today()
        self._selected_date_input.setDate(QDate(today.year, today.month, today.day))
        self._selected_date_input.dateChanged.connect(self.load_tasks)
        self._today_button = QPushButton()
        self._today_button.clicked.connect(self._select_today)
        self._new_task_button = QPushButton()
        self._refresh_tasks_button = QPushButton()
        self._overdue_label = QLabel()
        self._pending_label = QLabel()
        self._completed_label = QLabel()
        self._overdue_tasks_layout = QVBoxLayout()
        self._pending_tasks_layout = QVBoxLayout()
        self._completed_tasks_layout = QVBoxLayout()
        self._new_task_button.clicked.connect(self._open_task_dialog)
        self._refresh_tasks_button.clicked.connect(self.load_tasks)

        tasks_layout = QVBoxLayout()
        task_actions_layout = QHBoxLayout()
        task_actions_layout.addWidget(self._selected_date_label)
        task_actions_layout.addWidget(self._selected_date_input)
        task_actions_layout.addWidget(self._today_button)
        task_actions_layout.addWidget(self._new_task_button)
        task_actions_layout.addWidget(self._refresh_tasks_button)
        task_actions_layout.addStretch()
        tasks_layout.addLayout(task_actions_layout)
        tasks_layout.addWidget(self._overdue_label)
        tasks_layout.addLayout(self._overdue_tasks_layout)
        tasks_layout.addWidget(self._pending_label)
        tasks_layout.addLayout(self._pending_tasks_layout)
        tasks_layout.addWidget(self._completed_label)
        tasks_layout.addLayout(self._completed_tasks_layout)
        self._daily_tasks_group.setLayout(tasks_layout)

        layout = QVBoxLayout()
        layout.addWidget(self._title_label)
        layout.addWidget(self._shortcuts_group)
        layout.addWidget(self._daily_tasks_group)
        layout.addStretch()
        self.setLayout(layout)

        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        self._title_label.setText(t("Dashboard"))
        self._shortcuts_group.setTitle(t("Quick Actions"))
        self._products_button.setText(t("Create Product"))
        self._suppliers_button.setText(t("Create Supplier"))
        self._customers_button.setText(t("Create Customer"))
        self._orders_button.setText(t("Create Order"))
        self._settings_button.setText(t("Settings"))

        self._daily_tasks_group.setTitle(t("Daily Tasks"))
        self._selected_date_label.setText(t("Selected date"))
        self._today_button.setText(t("Today"))
        self._new_task_button.setText(t("New Task"))
        self._refresh_tasks_button.setText(t("Refresh"))
        self._overdue_label.setText(t("Overdue"))
        self._pending_label.setText(t("Pending tasks"))
        self._completed_label.setText(t("Completed tasks"))
        self.load_tasks()

    def load_tasks(self, *_args) -> None:
        try:
            session = SessionLocal()
        except Exception as exc:
            self._handle_load_tasks_error(exc)
            return

        try:
            selected_day = self._selected_date()
            task_list = ListDashboardTasksService(session).execute(selected_day)
            self._populate_task_section(
                self._overdue_tasks_layout,
                task_list.overdue,
                t("No overdue tasks."),
                action_label=t("Complete"),
                action=self._complete_task,
            )
            self._populate_task_section(
                self._pending_tasks_layout,
                task_list.pending_today,
                t("No pending tasks for selected date."),
                action_label=t("Complete"),
                action=self._complete_task,
            )
            self._populate_task_section(
                self._completed_tasks_layout,
                task_list.completed_today,
                t("No completed tasks for selected date."),
                action_label=t("Reopen"),
                action=self._reopen_task,
            )
        except Exception as exc:
            self._handle_load_tasks_error(exc)
        finally:
            session.close()

    def _populate_task_section(
        self,
        layout: QVBoxLayout,
        tasks: list[TaskListItem],
        empty_text: str,
        action_label: str,
        action,
    ) -> None:
        self._clear_layout(layout)

        if not tasks:
            empty_label = QLabel(empty_text)
            empty_label.setObjectName("emptyState")
            layout.addWidget(empty_label)
            return

        for task in tasks:
            layout.addLayout(self._task_row(task, action_label, action))

    def _task_row(self, task: TaskListItem, action_label: str, action) -> QHBoxLayout:
        row = QHBoxLayout()
        label = QLabel(self._task_label(task))
        button = QPushButton(action_label)
        button.clicked.connect(lambda _checked=False, task_id=task.id: action(task_id))
        row.addWidget(label, 1)
        row.addWidget(button)
        return row

    @staticmethod
    def _task_label(task: TaskListItem) -> str:
        order_prefix = f"[{task.order_number}] " if task.order_number else ""
        if task.is_auto_order_follow_up and task.order_number:
            title = f"{order_prefix}{t('Follow up')}"
        else:
            title = f"{order_prefix}{task.title}"
        if task.notes:
            notes = t(task.notes) if task.is_auto_order_follow_up else task.notes
            return f"{task.due_date.isoformat()} - {title} ({notes})"

        return f"{task.due_date.isoformat()} - {title}"

    def _open_task_dialog(self) -> None:
        dialog = TaskDialog(self, default_due_date=self._selected_date())
        if dialog.exec():
            self.load_tasks()
            self.task_changed.emit()

    def _select_today(self) -> None:
        today = date.today()
        today_qdate = QDate(today.year, today.month, today.day)
        if self._selected_date_input.date() == today_qdate:
            self.load_tasks()
        else:
            self._selected_date_input.setDate(today_qdate)

    def _selected_date(self) -> date:
        return self._selected_date_input.date().toPython()

    def _complete_task(self, task_id: int) -> None:
        self._change_task_completion(task_id, complete=True)

    def _reopen_task(self, task_id: int) -> None:
        self._change_task_completion(task_id, complete=False)

    def _change_task_completion(self, task_id: int, complete: bool) -> None:
        try:
            session = SessionLocal()
        except Exception as exc:
            QMessageBox.critical(self, t("Could not update task"), str(exc))
            return

        try:
            if complete:
                CompleteTaskService(session).execute(task_id)
            else:
                ReopenTaskService(session).execute(task_id)
            session.commit()
            self.load_tasks()
            self.task_changed.emit()
        except Exception as exc:
            session.rollback()
            QMessageBox.critical(self, t("Could not update task"), t(str(exc)))
        finally:
            session.close()

    def _handle_load_tasks_error(self, exc: Exception) -> None:
        self._clear_layout(self._overdue_tasks_layout)
        self._clear_layout(self._pending_tasks_layout)
        self._clear_layout(self._completed_tasks_layout)
        QMessageBox.critical(self, t("Could not load tasks"), str(exc))

    def _clear_layout(self, layout: QVBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            child_layout = item.layout()
            widget = item.widget()
            if child_layout is not None:
                self._clear_layout(child_layout)
                child_layout.deleteLater()
            if widget is not None:
                widget.deleteLater()
