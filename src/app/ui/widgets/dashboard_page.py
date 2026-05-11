from datetime import date, datetime, timedelta

from PySide6.QtCore import QDate, QEvent, QObject, Qt, Signal
from PySide6.QtWidgets import (
    QCalendarWidget,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
)

from app.application.dto.dashboard import DashboardOrderItem
from app.application.dto.tasks import TaskListItem
from app.application.services.dashboard import (
    ACTIVE_DASHBOARD_ORDER_STATUSES,
    GetDashboardSummaryService,
)
from app.application.services.tasks import (
    CompleteTaskService,
    ListDashboardTasksService,
    ReopenTaskService,
)
from app.domain.enums import OrderStatus
from app.infrastructure.db.session import SessionLocal
from app.ui.date_edit import AppDateEdit
from app.ui.dialogs.task_dialog import TaskDialog
from app.ui.localization import order_status_label, t


class DashboardPage(QWidget):
    action_requested = Signal(str)
    order_requested = Signal(int)
    task_changed = Signal()

    def __init__(self) -> None:
        super().__init__()

        self._title_label = QLabel()
        self._title_label.setObjectName("pageTitle")

        self._shortcuts_title_label = self._section_title()
        self._products_button = self._shortcut_button("📦", "new_product", "#eff6ff", "#1e3a8a")
        self._orders_button = self._shortcut_button("🧾", "new_order", "#fef2f2", "#7f1d1d")
        self._customers_button = self._shortcut_button("👤", "new_customer", "#fffbeb", "#78350f")
        self._suppliers_button = self._shortcut_button("🤝", "new_supplier", "#f0fdf4", "#14532d")
        self._tasks_button = self._shortcut_button("✓", "new_task", "#f5f3ff", "#312e81")
        self._calendar_button = self._shortcut_button("📅", "calendar", "#ecfeff", "#164e63")
        self._settings_button = self._shortcut_button("⚙", "settings", "#f9fafb", "#374151")

        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 18, 0)
        left_layout.setSpacing(12)
        left_layout.addWidget(self._shortcuts_title_label)
        left_layout.addStretch()
        left_layout.addWidget(self._products_button)
        left_layout.addWidget(self._orders_button)
        left_layout.addWidget(self._customers_button)
        left_layout.addWidget(self._suppliers_button)
        left_layout.addWidget(self._tasks_button)
        left_layout.addWidget(self._calendar_button)
        left_layout.addWidget(self._settings_button)
        left_layout.addStretch()
        left_column = QFrame()
        left_column.setObjectName("shortcutRail")
        left_column.setLayout(left_layout)
        left_column.setStyleSheet("QFrame#shortcutRail { border-right: 1px solid #e5e7eb; }")

        self._summary_title_label = self._section_title()
        self._open_orders_label = self._subsection_title()
        self._order_counts_layout = QGridLayout()
        self._order_counts_layout.setSpacing(8)
        self._due_soon_label = self._subsection_title()
        self._due_soon_layout = QVBoxLayout()
        self._due_soon_layout.setSpacing(8)
        self._recent_orders_label = self._subsection_title()
        self._recent_orders_layout = QVBoxLayout()
        self._recent_orders_layout.setSpacing(8)

        middle_layout = QVBoxLayout()
        middle_layout.setContentsMargins(12, 0, 12, 0)
        middle_layout.setSpacing(12)
        middle_layout.addWidget(self._summary_title_label)
        middle_layout.addWidget(self._open_orders_label)
        middle_layout.addLayout(self._order_counts_layout)
        middle_layout.addSpacing(4)
        middle_layout.addWidget(self._due_soon_label)
        middle_layout.addLayout(self._due_soon_layout)
        middle_layout.addSpacing(10)
        middle_layout.addWidget(self._recent_orders_label)
        middle_layout.addLayout(self._recent_orders_layout)
        middle_layout.addStretch()
        middle_content = QWidget()
        middle_content.setLayout(middle_layout)
        middle_content.setStyleSheet("QWidget { background: #f7f8fa; }")

        middle_scroll = QScrollArea()
        middle_scroll.setWidgetResizable(True)
        middle_scroll.setFrameShape(QFrame.NoFrame)
        middle_scroll.setWidget(middle_content)
        middle_scroll.setStyleSheet("QScrollArea { background: #f7f8fa; }")

        middle_column_layout = QVBoxLayout()
        middle_column_layout.setContentsMargins(10, 0, 10, 0)
        middle_column_layout.addWidget(middle_scroll)
        middle_column = QFrame()
        middle_column.setObjectName("summaryColumn")
        middle_column.setLayout(middle_column_layout)
        middle_column.setStyleSheet("QFrame#summaryColumn { background: #f7f8fa; }")

        self._tasks_title_label = self._section_title()
        self._selected_date_input = AppDateEdit()
        self._selected_date_input.setVisible(False)
        self._selected_date_button = self._date_button("")
        self._selected_date_button.clicked.connect(self._open_date_selector)
        today = date.today()
        self._selected_date_input.setDate(QDate(today.year, today.month, today.day))
        self._selected_date_input.dateChanged.connect(self.load_tasks)
        self._previous_day_button = self._date_button("<")
        self._previous_day_button.clicked.connect(lambda: self._move_selected_day(-1))
        self._next_day_button = self._date_button(">")
        self._next_day_button.clicked.connect(lambda: self._move_selected_day(1))
        self._today_button = self._date_button("")
        self._today_button.clicked.connect(self._select_today)
        self._add_task_button = self._date_button("+")
        self._add_task_button.clicked.connect(self._open_task_dialog)
        self._overdue_label = self._subsection_title()
        self._pending_label = self._subsection_title()
        self._completed_label = self._subsection_title()
        self._overdue_tasks_layout = QVBoxLayout()
        self._overdue_tasks_layout.setSpacing(8)
        self._pending_tasks_layout = QVBoxLayout()
        self._pending_tasks_layout.setSpacing(8)
        self._completed_tasks_layout = QVBoxLayout()
        self._completed_tasks_layout.setSpacing(8)

        task_date_layout = QHBoxLayout()
        task_date_layout.setSpacing(8)
        task_date_layout.addWidget(self._previous_day_button)
        task_date_layout.addWidget(self._selected_date_button, 1)
        task_date_layout.addWidget(self._next_day_button)
        task_date_layout.addWidget(self._today_button)
        task_date_layout.addWidget(self._add_task_button)

        tasks_content = QWidget()
        tasks_content.setStyleSheet("QWidget { background: #ffffff; }")
        tasks_layout = QVBoxLayout()
        tasks_layout.setContentsMargins(0, 0, 0, 0)
        tasks_layout.setSpacing(12)
        tasks_layout.addWidget(self._tasks_title_label)
        tasks_layout.addLayout(task_date_layout)
        tasks_layout.addWidget(self._overdue_label)
        tasks_layout.addLayout(self._overdue_tasks_layout)
        tasks_layout.addWidget(self._pending_label)
        tasks_layout.addLayout(self._pending_tasks_layout)
        tasks_layout.addWidget(self._completed_label)
        tasks_layout.addLayout(self._completed_tasks_layout)
        tasks_layout.addStretch()
        tasks_content.setLayout(tasks_layout)

        tasks_scroll = QScrollArea()
        tasks_scroll.setWidgetResizable(True)
        tasks_scroll.setFrameShape(QFrame.NoFrame)
        tasks_scroll.setWidget(tasks_content)
        tasks_scroll.setStyleSheet("QScrollArea { background: #ffffff; border: none; }")

        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(12, 0, 0, 0)
        right_layout.addWidget(tasks_scroll)
        right_column = QWidget()
        right_column.setLayout(right_layout)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(0)
        content_layout.addWidget(left_column, 1)
        content_layout.addWidget(middle_column, 1)
        content_layout.addWidget(right_column, 1)

        layout = QVBoxLayout()
        layout.addWidget(self._title_label)
        layout.addLayout(content_layout, 1)
        self.setLayout(layout)

        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        self._title_label.setText(t("Dashboard"))
        self._shortcuts_title_label.setText(t("Quick Actions"))
        self._products_button.setText(f"📦  {t('New Product')}")
        self._orders_button.setText(f"🧾  {t('New Order')}")
        self._customers_button.setText(f"👤  {t('New Customer')}")
        self._suppliers_button.setText(f"🤝  {t('New Supplier')}")
        self._tasks_button.setText(f"✓  {t('New Task')}")
        self._calendar_button.setText(f"📅  {t('Calendar')}")
        self._settings_button.setText(f"⚙  {t('Settings')}")

        self._summary_title_label.setText(t("Orders Overview"))
        self._open_orders_label.setText(t("Open Orders"))
        self._due_soon_label.setText(t("Orders Due Soon"))
        self._recent_orders_label.setText(t("Recent Orders"))

        self._tasks_title_label.setText(t("Daily Tasks"))
        self._previous_day_button.setText("<")
        self._next_day_button.setText(">")
        self._today_button.setText(t("Today"))
        self._add_task_button.setText("+")
        self._sync_selected_date_button()
        self._overdue_label.setText(t("Overdue"))
        self._pending_label.setText(t("Pending tasks"))
        self._completed_label.setText(t("Completed tasks"))
        self._load_dashboard()

    def load_tasks(self, *_args) -> None:
        self._sync_selected_date_button()
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
                section="overdue",
            )
            self._populate_task_section(
                self._pending_tasks_layout,
                task_list.pending_today,
                t("No pending tasks for selected date."),
                action_label=t("Complete"),
                action=self._complete_task,
                section="pending",
            )
            self._populate_task_section(
                self._completed_tasks_layout,
                task_list.completed_today,
                t("No completed tasks for selected date."),
                action_label=t("Reopen"),
                action=self._reopen_task,
                section="completed",
            )
        except Exception as exc:
            self._handle_load_tasks_error(exc)
        finally:
            session.close()

    def load_summary(self) -> None:
        try:
            session = SessionLocal()
        except Exception as exc:
            self._handle_load_summary_error(exc)
            return

        try:
            summary = GetDashboardSummaryService(session).execute()
            self._populate_order_counts(summary.active_order_counts)
            self._populate_order_section(
                self._due_soon_layout,
                summary.due_soon_orders,
                t("No orders due soon."),
                include_deadline=True,
            )
            self._populate_order_section(
                self._recent_orders_layout,
                summary.recent_orders,
                t("No recent orders."),
                include_deadline=False,
            )
        except Exception as exc:
            self._handle_load_summary_error(exc)
        finally:
            session.close()

    def reload_dashboard(self) -> None:
        self._load_dashboard()

    def _load_dashboard(self, *_args) -> None:
        self.load_summary()
        self.load_tasks()

    def _shortcut_button(
        self,
        _symbol: str,
        action: str,
        background: str,
        foreground: str,
    ) -> QPushButton:
        button = QPushButton()
        button.setMinimumHeight(48)
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button.setStyleSheet(
            "QPushButton { "
            f"background: {background}; color: {foreground}; "
            "border: 1px solid rgba(15, 23, 42, 0.08); border-radius: 20px; "
            "padding: 10px 14px; text-align: left; font-weight: 650; "
            "} "
            "QPushButton:hover { border: 1px solid rgba(15, 23, 42, 0.22); }"
        )
        if action == "new_task":
            button.clicked.connect(self._open_task_dialog)
        else:
            button.clicked.connect(
                lambda _checked=False, requested=action: self.action_requested.emit(requested)
            )
        return button

    def _date_button(self, label: str) -> QPushButton:
        button = QPushButton(label)
        button.setMinimumHeight(36)
        button.setStyleSheet(
            "QPushButton { background: #f9fafb; border: 1px solid #e5e7eb; "
            "border-radius: 12px; padding: 6px 10px; font-weight: 600; }"
            "QPushButton:hover { background: #f3f4f6; }"
        )
        return button

    def _open_date_selector(self) -> None:
        menu = QMenu(self)
        calendar = QCalendarWidget()
        calendar.setSelectedDate(self._selected_date_input.date())
        action = QWidgetAction(menu)
        action.setDefaultWidget(calendar)
        menu.addAction(action)
        calendar.clicked.connect(
            lambda selected_date: self._set_date_from_calendar(menu, selected_date)
        )
        menu.exec(self._selected_date_button.mapToGlobal(self._selected_date_button.rect().bottomLeft()))

    def _set_date_from_calendar(self, menu: QMenu, selected_date: QDate) -> None:
        self._selected_date_input.setDate(selected_date)
        menu.close()

    def _sync_selected_date_button(self) -> None:
        self._selected_date_button.setText(self._selected_date().isoformat())

    def _section_title(self) -> QLabel:
        label = QLabel()
        label.setStyleSheet("font-size: 16px; font-weight: 700; color: #111827;")
        return label

    def _subsection_title(self) -> QLabel:
        label = QLabel()
        label.setStyleSheet("font-size: 13px; font-weight: 700; color: #374151;")
        return label

    def _populate_order_counts(self, counts: dict[OrderStatus, int]) -> None:
        self._clear_layout(self._order_counts_layout)
        for status in ACTIVE_DASHBOARD_ORDER_STATUSES:
            count_label = QLabel(f"{order_status_label(status)}\n{counts.get(status, 0)}")
            count_label.setAlignment(Qt.AlignCenter)
            count_label.setStyleSheet(
                "background: #ffffff; border-radius: 14px; padding: 8px; "
                "font-weight: 650; color: #111827;"
            )
            index = self._order_counts_layout.count()
            self._order_counts_layout.addWidget(count_label, index // 2, index % 2)

    def _populate_order_section(
        self,
        layout: QVBoxLayout,
        orders: list[DashboardOrderItem],
        empty_text: str,
        *,
        include_deadline: bool,
    ) -> None:
        self._clear_layout(layout)
        if not orders:
            empty_label = QLabel(empty_text)
            empty_label.setObjectName("emptyState")
            layout.addWidget(empty_label)
            return

        for order in orders:
            layout.addWidget(self._order_row(order, include_deadline=include_deadline))

    def _order_row(self, order: DashboardOrderItem, *, include_deadline: bool) -> QFrame:
        frame = QFrame()
        frame.setObjectName("orderRow")
        self._register_order_click_target(frame, order.id)
        frame.setStyleSheet(
            "QFrame#orderRow { background: transparent; border: none; border-radius: 0; }"
        )
        title = QLabel(f"{order.order_number} · {order.customer_name}")
        self._register_order_click_target(title, order.id)
        title.setWordWrap(True)
        title.setStyleSheet("font-weight: 650; color: #111827;")
        badge = QLabel(
            self._deadline_distance_label(order.deadline)
            if include_deadline and order.deadline is not None
            else self._recent_activity_label(order)
        )
        self._register_order_click_target(badge, order.id)
        badge.setStyleSheet(
            "background: #ffffff; border-radius: 10px; color: #374151; "
            "font-size: 11px; padding: 3px 7px;"
        )
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.addWidget(title, 1)
        header_layout.addWidget(badge, 0, Qt.AlignTop)
        detail_parts = [order_status_label(order.status), f"{t('Total')}: {order.total_amount}"]
        if include_deadline and order.deadline is not None:
            detail_parts.insert(0, f"{t('Deadline')}: {order.deadline.isoformat()}")
        else:
            detail_parts.insert(0, f"{t('Order date')}: {order.order_date.isoformat()}")
        detail = QLabel("  ·  ".join(detail_parts))
        self._register_order_click_target(detail, order.id)
        detail.setWordWrap(True)
        detail.setStyleSheet("color: #6b7280;")
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 10, 12, 10)
        layout.addLayout(header_layout)
        layout.addWidget(detail)
        frame.setLayout(layout)
        return frame

    def _register_order_click_target(self, widget: QWidget, order_id: int) -> None:
        widget.setProperty("dashboardOrderId", order_id)
        widget.setCursor(Qt.PointingHandCursor)
        widget.installEventFilter(self)

    def eventFilter(self, source: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.MouseButtonPress:
            order_id = source.property("dashboardOrderId")
            if order_id is not None:
                self.order_requested.emit(int(order_id))
                return True
            task_id = source.property("dashboardTaskId")
            if task_id is not None:
                self._open_task_edit_dialog(int(task_id))
                return True
        return super().eventFilter(source, event)

    def _populate_task_section(
        self,
        layout: QVBoxLayout,
        tasks: list[TaskListItem],
        empty_text: str,
        action_label: str,
        action,
        section: str,
    ) -> None:
        self._clear_layout(layout)

        if not tasks:
            empty_label = QLabel(empty_text)
            empty_label.setObjectName("emptyState")
            layout.addWidget(empty_label)
            return

        for task in tasks:
            layout.addWidget(self._task_row(task, action_label, action, section))

    def _task_row(
        self,
        task: TaskListItem,
        action_label: str,
        action,
        section: str,
    ) -> QFrame:
        frame = QFrame()
        background, border, icon = self._task_row_treatment(section)
        frame.setObjectName("taskRow")
        self._register_task_click_target(frame, task)
        frame.setStyleSheet(
            f"QFrame#taskRow {{ background: {background}; border: 1px solid {border}; "
            "border-radius: 16px; }}"
            "QFrame#taskRow QLabel { background: transparent; }"
        )
        icon_label = QLabel(icon)
        self._register_task_click_target(icon_label, task)
        icon_label.setFixedWidth(24)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 18px;")
        title_label = QLabel(self._task_title(task))
        self._register_task_click_target(title_label, task)
        title_label.setWordWrap(True)
        title_label.setStyleSheet("font-weight: 650; color: #111827;")
        meta_label = QLabel(self._task_meta(task))
        self._register_task_click_target(meta_label, task)
        meta_label.setWordWrap(True)
        meta_label.setStyleSheet("color: #6b7280;")
        button = QPushButton(action_label)
        button.setMinimumHeight(30)
        button.setStyleSheet(
            "QPushButton { background: #f9fafb; border: 1px solid #e5e7eb; "
            "border-radius: 10px; padding: 4px 8px; }"
            "QPushButton:hover { background: #f3f4f6; }"
        )
        button.clicked.connect(lambda _checked=False, task_id=task.id: action(task_id))
        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(3)
        text_layout.addWidget(title_label)
        text_layout.addWidget(meta_label)
        row = QHBoxLayout()
        row.setContentsMargins(12, 10, 12, 10)
        row.setSpacing(10)
        row.addWidget(icon_label, 0, Qt.AlignVCenter)
        row.addLayout(text_layout, 1)
        row.addWidget(button)
        frame.setLayout(row)
        return frame

    def _register_task_click_target(self, widget: QWidget, task: TaskListItem) -> None:
        if task.is_auto_order_follow_up:
            return

        widget.setProperty("dashboardTaskId", task.id)
        widget.setCursor(Qt.PointingHandCursor)
        widget.installEventFilter(self)

    @staticmethod
    def _task_title(task: TaskListItem) -> str:
        order_prefix = f"[{task.order_number}] " if task.order_number else ""
        if task.is_auto_order_follow_up and task.order_number:
            return f"{order_prefix}{t('Follow up')}"

        return f"{order_prefix}{task.title}"

    @staticmethod
    def _task_meta(task: TaskListItem) -> str:
        details = [f"{t('Due date')}: {task.due_date.isoformat()}"]
        if task.notes:
            notes = t(task.notes) if task.is_auto_order_follow_up else task.notes
            details.append(notes)

        return " · ".join(details)

    @classmethod
    def _task_label(cls, task: TaskListItem) -> str:
        title = cls._task_title(task)
        if task.notes:
            notes = t(task.notes) if task.is_auto_order_follow_up else task.notes
            return f"{task.due_date.isoformat()} - {title} ({notes})"

        return f"{task.due_date.isoformat()} - {title}"

    @staticmethod
    def _task_row_treatment(section: str) -> tuple[str, str, str]:
        if section == "overdue":
            return "#ffedd5", "#fdba74", "!"
        if section == "completed":
            return "#dcfce7", "#86efac", "✓"

        return "#ffffff", "#e5e7eb", "○"

    @staticmethod
    def _deadline_distance_label(deadline: date) -> str:
        days = (deadline - date.today()).days
        if days < 0:
            return f"{t('Overdue by')} {abs(days)} {t('days')}"
        if days == 0:
            return t("Due today")
        if days == 1:
            return t("1 day left")

        return f"{days} {t('days left')}"

    @staticmethod
    def _recent_activity_label(order: DashboardOrderItem) -> str:
        if order.updated_at > order.created_at:
            return DashboardPage._days_ago_label(
                t("Updated"),
                DashboardPage._local_date(order.updated_at),
            )

        return DashboardPage._days_ago_label(
            t("Created"),
            DashboardPage._local_date(order.created_at),
        )

    @staticmethod
    def _local_date(value: datetime) -> date:
        return value.date()

    @staticmethod
    def _days_ago_label(prefix: str, activity_date: date) -> str:
        days = (date.today() - activity_date).days
        if days <= 0:
            return t("{prefix} today").format(prefix=prefix)
        if days == 1:
            return t("{prefix} yesterday").format(prefix=prefix)

        return t("{prefix} {count} days ago").format(prefix=prefix, count=days)

    def _open_task_dialog(self) -> None:
        dialog = TaskDialog(self, default_due_date=self._selected_date())
        if dialog.exec():
            self.load_tasks()
            self.task_changed.emit()

    def _open_task_edit_dialog(self, task_id: int) -> None:
        dialog = TaskDialog(self, task_id=task_id)
        if dialog.exec():
            self.load_tasks()
            self.task_changed.emit()

    def _move_selected_day(self, day_delta: int) -> None:
        selected_day = self._selected_date() + timedelta(days=day_delta)
        self._set_selected_date(selected_day)

    def _select_today(self) -> None:
        self._set_selected_date(date.today())

    def _set_selected_date(self, selected_day: date) -> None:
        selected_qdate = QDate(selected_day.year, selected_day.month, selected_day.day)
        if self._selected_date_input.date() == selected_qdate:
            self.load_tasks()
        else:
            self._selected_date_input.setDate(selected_qdate)

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

    def _handle_load_summary_error(self, exc: Exception) -> None:
        self._clear_layout(self._order_counts_layout)
        self._clear_layout(self._due_soon_layout)
        self._clear_layout(self._recent_orders_layout)
        QMessageBox.critical(self, t("Could not load dashboard"), str(exc))

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            child_layout = item.layout()
            widget = item.widget()
            if child_layout is not None:
                self._clear_layout(child_layout)
                child_layout.deleteLater()
            if widget is not None:
                widget.deleteLater()
