from calendar import Calendar, month_name
from datetime import date

from PySide6.QtCore import QEvent, QObject, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QGroupBox,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.application.dto.tasks import TaskListItem
from app.application.services.tasks import (
    CompleteTaskService,
    ListCalendarTasksService,
    ReopenTaskService,
)
from app.infrastructure.db.session import SessionLocal
from app.ui.dialogs.task_dialog import TaskDialog
from app.ui.localization import format_date, t
from app.ui.task_colors import task_background
from app.ui.widgets.task_card import TaskCard, task_card_state


class CalendarPage(QWidget):
    task_changed = Signal()

    def __init__(self) -> None:
        super().__init__()

        today = date.today()
        self._display_year = today.year
        self._display_month = today.month
        self._selected_day = today
        self._tasks_by_day: dict[date, list[TaskListItem]] = {}
        self._grid_days: list[date] = []

        self._title_label = QLabel()
        self._title_label.setObjectName("pageTitle")
        self._month_label = QLabel()
        self._previous_month_button = QPushButton()
        self._next_month_button = QPushButton()
        self._today_button = QPushButton()
        self._new_task_button = QPushButton()
        self._refresh_button = QPushButton()

        self._previous_month_button.clicked.connect(self._show_previous_month)
        self._next_month_button.clicked.connect(self._show_next_month)
        self._today_button.clicked.connect(self._show_today)
        self._new_task_button.clicked.connect(self._open_task_dialog)
        self._refresh_button.clicked.connect(self.load_calendar)

        self._calendar_table = QTableWidget(6, 7)
        self._calendar_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._calendar_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._calendar_table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self._calendar_table.verticalHeader().setVisible(False)
        self._calendar_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._calendar_table.cellClicked.connect(self._select_cell)
        for row in range(6):
            self._calendar_table.setRowHeight(row, 104)

        self._selected_day_group = QGroupBox()
        self._selected_day_group.setMinimumWidth(340)
        self._selected_day_group.setMaximumWidth(460)
        self._selected_day_group.setStyleSheet(
            "QGroupBox { background: #ffffff; border: 1px solid #e1e7ef; "
            "border-radius: 16px; padding: 14px; margin-top: 12px; font-weight: 700; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 4px; }"
        )
        self._pending_label = QLabel()
        self._completed_label = QLabel()
        section_style = "font-size: 13px; font-weight: 700; color: #374151; margin-top: 4px;"
        self._pending_label.setStyleSheet(section_style)
        self._completed_label.setStyleSheet(section_style)
        self._pending_tasks_layout = QVBoxLayout()
        self._completed_tasks_layout = QVBoxLayout()

        selected_day_layout = QVBoxLayout()
        selected_day_layout.addWidget(self._pending_label)
        selected_day_layout.addLayout(self._pending_tasks_layout)
        selected_day_layout.addWidget(self._completed_label)
        selected_day_layout.addLayout(self._completed_tasks_layout)
        selected_day_layout.addStretch()
        self._selected_day_group.setLayout(selected_day_layout)

        self._selected_day_scroll = QScrollArea()
        self._selected_day_scroll.setMinimumWidth(360)
        self._selected_day_scroll.setMaximumWidth(480)
        self._selected_day_scroll.setWidgetResizable(True)
        self._selected_day_scroll.setWidget(self._selected_day_group)

        header_layout = QHBoxLayout()
        header_layout.addWidget(self._month_label)
        header_layout.addStretch()
        header_layout.addWidget(self._previous_month_button)
        header_layout.addWidget(self._today_button)
        header_layout.addWidget(self._next_month_button)
        header_layout.addWidget(self._new_task_button)
        header_layout.addWidget(self._refresh_button)

        layout = QVBoxLayout()
        layout.addWidget(self._title_label)
        layout.addLayout(header_layout)
        content_layout = QHBoxLayout()
        content_layout.addWidget(self._selected_day_scroll)
        content_layout.addWidget(self._calendar_table, 1)
        layout.addLayout(content_layout, 1)
        self.setLayout(layout)

        self.retranslate_ui()
        self.load_calendar()

    def retranslate_ui(self) -> None:
        self._title_label.setText(t("Calendar"))
        self._previous_month_button.setText(t("Previous"))
        self._next_month_button.setText(t("Next"))
        self._today_button.setText(t("Today"))
        self._new_task_button.setText(t("New Task"))
        self._refresh_button.setText(t("Refresh"))
        self._calendar_table.setHorizontalHeaderLabels(
            [
                t("Sun"),
                t("Mon"),
                t("Tue"),
                t("Wed"),
                t("Thu"),
                t("Fri"),
                t("Sat"),
            ]
        )
        self._update_month_label()
        self._populate_calendar_grid()
        self._load_selected_day_tasks()

    def load_calendar(self, *_args) -> None:
        self._grid_days = [
            day
            for week in Calendar(firstweekday=6).monthdatescalendar(
                self._display_year,
                self._display_month,
            )
            for day in week
        ]
        while len(self._grid_days) < 42:
            next_day = self._grid_days[-1]
            self._grid_days.append(date.fromordinal(next_day.toordinal() + 1))

        try:
            session = SessionLocal()
        except Exception as exc:
            self._handle_load_error(exc)
            return

        try:
            task_days = ListCalendarTasksService(session).execute(
                self._grid_days[0],
                self._grid_days[-1],
            )
            self._tasks_by_day = {task_day.day: task_day.tasks for task_day in task_days}
            self._populate_calendar_grid()
            self._load_selected_day_tasks()
        except Exception as exc:
            self._handle_load_error(exc)
        finally:
            session.close()

    def _populate_calendar_grid(self) -> None:
        if not self._grid_days:
            return

        self._update_month_label()
        self._calendar_table.clearContents()
        for row in range(6):
            for column in range(7):
                self._calendar_table.removeCellWidget(row, column)
        for index, day in enumerate(self._grid_days[:42]):
            row = index // 7
            column = index % 7
            tasks = self._tasks_by_day.get(day, [])
            item = QTableWidgetItem()
            item.setData(Qt.UserRole, day)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self._calendar_table.setItem(row, column, item)
            self._calendar_table.setCellWidget(row, column, self._calendar_cell_widget(day, tasks))

    def _calendar_cell_widget(self, day: date, tasks: list[TaskListItem]) -> QWidget:
        cell = QFrame()
        cell.setObjectName("calendarDayCell")
        self._register_calendar_click_target(cell, day)
        if day == self._selected_day:
            cell.setStyleSheet(
                "QFrame#calendarDayCell { background: #dbeafe; border: 1px solid #2563eb; }"
            )
        elif day.month != self._display_month:
            cell.setStyleSheet(
                "QFrame#calendarDayCell { background: #f3f4f6; border: 1px solid #e5e7eb; }"
            )
        else:
            cell.setStyleSheet(
                "QFrame#calendarDayCell { background: #ffffff; border: 1px solid #e5e7eb; }"
            )

        layout = QVBoxLayout()
        layout.setContentsMargins(5, 4, 5, 4)
        layout.setSpacing(3)

        day_label = QLabel(str(day.day))
        self._register_calendar_click_target(day_label, day)
        day_label.setStyleSheet(
            "color: #6b7280;" if day.month != self._display_month else "font-weight: 600;"
        )
        layout.addWidget(day_label)

        for task in tasks[:2]:
            task_label = QLabel(self._task_title(task))
            self._register_calendar_click_target(task_label, day)
            task_label.setToolTip(self._task_detail_label(task))
            task_label.setFixedHeight(18)
            task_label.setTextFormat(Qt.PlainText)
            task_label.setStyleSheet(self._task_block_style(task))
            layout.addWidget(task_label)
        if len(tasks) > 2:
            more_label = QLabel(t("+ {count} more").format(count=len(tasks) - 2))
            self._register_calendar_click_target(more_label, day)
            more_label.setStyleSheet("color: #374151; font-size: 11px;")
            layout.addWidget(more_label)
        layout.addStretch()
        cell.setLayout(layout)

        return cell

    def _select_cell(self, row: int, column: int) -> None:
        item = self._calendar_table.item(row, column)
        if item is None:
            return

        selected_day = item.data(Qt.UserRole)
        if selected_day is None:
            return

        self._select_day(selected_day)

    def _select_day(self, selected_day: date) -> None:
        self._selected_day = selected_day
        self._display_year = selected_day.year
        self._display_month = selected_day.month
        self.load_calendar()

    def _register_calendar_click_target(self, widget: QWidget, day: date) -> None:
        widget.setProperty("calendarDayOrdinal", day.toordinal())
        widget.installEventFilter(self)

    def eventFilter(self, source: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.MouseButtonPress:
            task_id = source.property("calendarTaskId")
            if task_id is not None:
                self._open_task_edit_dialog(int(task_id))
                return True
            ordinal = source.property("calendarDayOrdinal")
            if ordinal is not None:
                self._select_day(date.fromordinal(int(ordinal)))
                return True
        return super().eventFilter(source, event)

    def _load_selected_day_tasks(self) -> None:
        try:
            session = SessionLocal()
        except Exception as exc:
            self._handle_load_error(exc)
            return

        try:
            task_days = ListCalendarTasksService(session).execute(
                self._selected_day,
                self._selected_day,
            )
            selected_day_tasks = task_days[0].tasks if task_days else []
            pending_tasks = [task for task in selected_day_tasks if task.completed_at is None]
            completed_tasks = [task for task in selected_day_tasks if task.completed_at is not None]
            self._selected_day_group.setTitle(f"{t('Tasks for')} {format_date(self._selected_day)}")
            self._pending_label.setText(t("Pending tasks"))
            self._completed_label.setText(t("Completed tasks"))
            self._populate_task_section(
                self._pending_tasks_layout,
                pending_tasks,
                t("No pending tasks for selected date."),
                action_label=t("Complete"),
                action=self._complete_task,
            )
            self._populate_task_section(
                self._completed_tasks_layout,
                completed_tasks,
                t("No completed tasks for selected date."),
                action_label=t("Reopen"),
                action=self._reopen_task,
            )
        except Exception as exc:
            self._handle_load_error(exc)
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
            state = task_card_state(task)
            layout.addWidget(
                TaskCard(
                    task=task,
                    title=self._task_title(task),
                    description=self._task_description(task),
                    state=state,
                    action_label=action_label,
                    action_icon="↶" if state == "completed" else "✓",
                    action=action,
                    register_click_target=self._register_task_click_target,
                )
            )

    def _register_task_click_target(self, widget: QWidget, task: TaskListItem) -> None:
        if task.is_auto_order_follow_up:
            return

        widget.setProperty("calendarTaskId", task.id)
        widget.setCursor(Qt.PointingHandCursor)
        widget.installEventFilter(self)

    def _open_task_dialog(self) -> None:
        dialog = TaskDialog(self, default_due_date=self._selected_day)
        if dialog.exec():
            self.load_calendar()
            self.task_changed.emit()

    def _open_task_edit_dialog(self, task_id: int) -> None:
        dialog = TaskDialog(self, task_id=task_id)
        if dialog.exec():
            self.load_calendar()
            self.task_changed.emit()

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
            self.load_calendar()
            self.task_changed.emit()
        except Exception as exc:
            session.rollback()
            QMessageBox.critical(self, t("Could not update task"), t(str(exc)))
        finally:
            session.close()

    def _show_previous_month(self) -> None:
        if self._display_month == 1:
            self._display_year -= 1
            self._display_month = 12
        else:
            self._display_month -= 1
        self._selected_day = date(self._display_year, self._display_month, 1)
        self.load_calendar()

    def _show_next_month(self) -> None:
        if self._display_month == 12:
            self._display_year += 1
            self._display_month = 1
        else:
            self._display_month += 1
        self._selected_day = date(self._display_year, self._display_month, 1)
        self.load_calendar()

    def _show_today(self) -> None:
        today = date.today()
        self._display_year = today.year
        self._display_month = today.month
        self._selected_day = today
        self.load_calendar()

    def _update_month_label(self) -> None:
        self._month_label.setText(f"{t(month_name[self._display_month])} {self._display_year}")

    def _handle_load_error(self, exc: Exception) -> None:
        QMessageBox.critical(self, t("Could not load calendar"), str(exc))

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

    @staticmethod
    def _task_title(task: TaskListItem) -> str:
        if task.is_auto_order_follow_up and task.order_number:
            return f"[{task.order_number}] {t('Follow up')}"
        if task.order_number:
            return f"[{task.order_number}] {task.title}"
        return task.title

    @classmethod
    def _task_detail_label(cls, task: TaskListItem) -> str:
        title = cls._task_title(task)
        description = cls._task_description(task)
        if description:
            return f"{title} ({description})"

        return title

    @staticmethod
    def _task_description(task: TaskListItem) -> str | None:
        if task.notes:
            return t(task.notes) if task.is_auto_order_follow_up else task.notes

        return None

    @staticmethod
    def _task_block_style(task: TaskListItem) -> str:
        if task.completed_at is not None:
            return (
                "background: #ecfdf3; color: #37513d; border-left: 4px solid #86efac; "
                "border-radius: 3px; padding: 1px 4px; text-decoration: line-through;"
            )
        if task.is_auto_order_follow_up:
            return (
                "background: #ede9fe; color: #312e81; border-left: 4px solid #7c3aed; "
                "border-radius: 3px; padding: 1px 4px;"
            )
        return (
            f"background: {task_background(task.color_hex)}; color: #111827; "
            f"border-left: 4px solid {task.color_hex}; border-radius: 3px; padding: 1px 4px;"
        )
