from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.application.dto.orders import OrderListItem
from app.application.services.orders import (
    ListOrdersService,
    UpdateOrderService,
    UpdateOrderStatusService,
)
from app.domain.enums import OrderStatus
from app.infrastructure.db.session import SessionLocal
from app.ui.dialog_helpers import question
from app.ui.dialogs.order_dialog import OrderDialog
from app.ui.dialogs.task_dialog import TaskDialog
from app.ui.localization import format_date, order_status_label, t
from app.ui.page_chrome import (
    apply_page_chrome,
    apply_toolbar_chrome,
    build_selection_action_panel,
    configure_table_chrome,
    mark_danger_button,
    mark_primary_button,
    set_selection_actions_enabled,
)


class OrdersPage(QWidget):
    order_changed = Signal()
    task_changed = Signal()

    def __init__(self) -> None:
        super().__init__()

        self._orders_by_id: dict[int, OrderListItem] = {}

        self._title_label = QLabel()
        self._title_label.setObjectName("pageTitle")

        self._create_button = QPushButton()
        mark_primary_button(self._create_button)
        self._create_button.clicked.connect(self.open_create_dialog)

        self._edit_button = QPushButton()
        self._edit_button.clicked.connect(self.open_edit_dialog)

        self._advance_status_button = QPushButton()
        self._advance_status_button.clicked.connect(self.advance_selected_order_status)

        self._revert_status_button = QPushButton()
        self._revert_status_button.clicked.connect(self.revert_selected_order_status)

        self._cancel_order_button = QPushButton()
        mark_danger_button(self._cancel_order_button)
        self._cancel_order_button.clicked.connect(self.cancel_selected_order)

        self._recover_order_button = QPushButton()
        self._recover_order_button.clicked.connect(self.recover_selected_order)

        self._reminder_button = QPushButton()
        self._reminder_button.clicked.connect(self.open_reminder_dialog)

        self._refresh_button = QPushButton()
        self._refresh_button.clicked.connect(self.load_orders)

        self._table = QTableWidget()
        self._table.setColumnCount(7)
        configure_table_chrome(self._table)
        self._table.itemSelectionChanged.connect(self._sync_action_state)

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)

        layout = QVBoxLayout()
        apply_page_chrome(layout)
        layout.addWidget(self._title_label)

        actions_layout = QHBoxLayout()
        apply_toolbar_chrome(actions_layout)
        actions_layout.addWidget(self._create_button)
        actions_layout.addWidget(self._refresh_button)
        actions_layout.addStretch()

        self._selection_panel_title = QLabel()
        self._selection_panel_hint = QLabel()
        self._selection_actions = [
            self._edit_button,
            self._reminder_button,
            self._advance_status_button,
            self._revert_status_button,
            self._recover_order_button,
            self._cancel_order_button,
        ]
        selection_panel = build_selection_action_panel(
            self._selection_panel_title,
            self._selection_panel_hint,
            self._selection_actions,
        )

        content_layout = QHBoxLayout()
        content_layout.setSpacing(14)
        content_layout.addWidget(self._table, 1)
        content_layout.addWidget(selection_panel)

        layout.addLayout(actions_layout)
        layout.addLayout(content_layout, 1)
        self.setLayout(layout)

        self.load_orders()

    def retranslate_ui(self) -> None:
        self._title_label.setText(t("Orders"))
        self._create_button.setText(t("New Order"))
        self._edit_button.setText(t("Edit Order"))
        self._advance_status_button.setText(t("Advance Status"))
        self._revert_status_button.setText(t("Revert Status"))
        self._cancel_order_button.setText(t("Cancel Order"))
        self._recover_order_button.setText(t("Recover Order"))
        self._reminder_button.setText(t("New Reminder"))
        self._refresh_button.setText(t("Refresh"))
        self._selection_panel_title.setText(t("Selected order"))
        self._selection_panel_hint.setText(t("Select an order to use these actions."))
        self._table.setHorizontalHeaderLabels(
            [
                t("Order #"),
                t("Customer"),
                t("Status"),
                t("Order Date"),
                t("Deadline"),
                t("Lines"),
                t("Total"),
            ]
        )
        if self._table.rowCount() > 0:
            self.load_orders()

    def open_create_dialog(self) -> None:
        dialog = OrderDialog(self)
        if dialog.exec():
            self.load_orders()
            self.order_changed.emit()

    def open_order_for_edit(self, order_id: int) -> None:
        self.load_orders()
        for row in range(self._table.rowCount()):
            id_item = self._table.item(row, 0)
            if id_item is not None and id_item.data(Qt.UserRole) == order_id:
                self._table.selectRow(row)
                self.open_edit_dialog()
                return

        QMessageBox.information(
            self,
            t("No order selected"),
            t("Select an active order to edit."),
        )

    def open_edit_dialog(self) -> None:
        order = self._selected_order()
        if order is None:
            QMessageBox.information(
                self, t("No order selected"), t("Select an active order to edit.")
            )
            return

        try:
            session = SessionLocal()
        except Exception as exc:
            QMessageBox.critical(self, t("Could not check order edit policy"), str(exc))
            return

        try:
            edit_rejection_message = UpdateOrderService(session).order_edit_rejection_message(
                order.status
            )
        except Exception as exc:
            QMessageBox.critical(self, t("Could not check order edit policy"), str(exc))
            return
        finally:
            session.close()

        if edit_rejection_message is not None:
            QMessageBox.information(self, t("Order cannot be edited"), t(edit_rejection_message))
            return

        dialog = OrderDialog(self, order_id=order.id)
        if dialog.exec():
            self.load_orders()
            self.order_changed.emit()

    def open_reminder_dialog(self) -> None:
        order = self._selected_order()
        if order is None:
            QMessageBox.information(self, t("No order selected"), t("Select an order."))
            return

        dialog = TaskDialog(
            self,
            default_order_id=order.id,
            default_order_label=f"{order.order_number} - {order.customer_name}",
        )
        if dialog.exec():
            self.task_changed.emit()

    def advance_selected_order_status(self) -> None:
        order = self._selected_order()
        if order is None:
            QMessageBox.information(self, t("No order selected"), t("Select an order to advance."))
            return

        try:
            session = SessionLocal()
        except Exception as exc:
            QMessageBox.critical(self, t("Could not update order status"), str(exc))
            return

        try:
            next_status = UpdateOrderStatusService(session).next_forward_status(order.status)
        except Exception as exc:
            QMessageBox.critical(self, t("Could not update order status"), str(exc))
            return
        finally:
            session.close()

        if next_status is None:
            QMessageBox.information(
                self,
                t("Order cannot advance"),
                t("This order cannot be advanced in the configured workflow."),
            )
            return

        self._transition_selected_order(order, next_status)

    def revert_selected_order_status(self) -> None:
        order = self._selected_order()
        if order is None:
            QMessageBox.information(self, t("No order selected"), t("Select an order to revert."))
            return

        try:
            session = SessionLocal()
        except Exception as exc:
            QMessageBox.critical(self, t("Could not update order status"), str(exc))
            return

        try:
            previous_status = UpdateOrderStatusService(session).previous_status(order.status)
        except Exception as exc:
            QMessageBox.critical(self, t("Could not update order status"), str(exc))
            return
        finally:
            session.close()

        if previous_status is None:
            QMessageBox.information(
                self,
                t("Order cannot revert"),
                t("This order cannot be reverted in the configured workflow."),
            )
            return

        self._transition_selected_order(order, previous_status)

    def cancel_selected_order(self) -> None:
        order = self._selected_order()
        if order is None:
            QMessageBox.information(self, t("No order selected"), t("Select an order to cancel."))
            return

        try:
            session = SessionLocal()
        except Exception as exc:
            QMessageBox.critical(self, t("Could not update order status"), str(exc))
            return

        try:
            can_cancel_order = UpdateOrderStatusService(session).can_transition(
                order.status, OrderStatus.CANCELLED
            )
        except Exception as exc:
            QMessageBox.critical(self, t("Could not update order status"), str(exc))
            return
        finally:
            session.close()

        if not can_cancel_order:
            QMessageBox.information(
                self,
                t("Order cannot be cancelled"),
                t("Completed and cancelled orders cannot be cancelled."),
            )
            return

        response = question(
            self,
            t("Cancel order"),
            t("Cancel this order? This cannot be undone from the current workflow."),
        )
        if response != QMessageBox.Yes:
            return

        self._transition_selected_order(order, OrderStatus.CANCELLED)

    def recover_selected_order(self) -> None:
        order = self._selected_order()
        if order is None:
            QMessageBox.information(self, t("No order selected"), t("Select an order to recover."))
            return

        if order.status != OrderStatus.CANCELLED:
            QMessageBox.information(
                self,
                t("Order cannot be recovered"),
                t("Only cancelled orders can be recovered to draft."),
            )
            return

        response = question(
            self,
            t("Recover order"),
            t("Recover this cancelled order to draft?"),
        )
        if response != QMessageBox.Yes:
            return

        self._transition_selected_order(order, OrderStatus.DRAFT)

    def _transition_selected_order(
        self,
        order: OrderListItem,
        target_status: OrderStatus,
    ) -> None:
        try:
            session = SessionLocal()
        except Exception as exc:
            QMessageBox.critical(self, t("Could not update order status"), str(exc))
            return

        try:
            UpdateOrderStatusService(session).execute(order.id, target_status)
            session.commit()
            self.load_orders()
            self.order_changed.emit()
        except Exception as exc:
            session.rollback()
            QMessageBox.critical(self, t("Could not update order status"), str(exc))
        finally:
            session.close()

    def load_orders(self) -> None:
        try:
            session = SessionLocal()
        except Exception as exc:
            self._handle_load_orders_error(exc)
            return

        try:
            orders = ListOrdersService(session).execute()
            self._populate_table(orders)
            self._sync_action_state()
        except Exception as exc:
            self._handle_load_orders_error(exc)
        finally:
            session.close()

    def _handle_load_orders_error(self, exc: Exception) -> None:
        self._table.setRowCount(0)
        QMessageBox.critical(
            self,
            t("Could not load orders"),
            str(exc),
        )

    def _populate_table(self, orders: list[OrderListItem]) -> None:
        self._orders_by_id = {order.id: order for order in orders}
        self._table.setRowCount(len(orders))

        for row, order in enumerate(orders):
            items = [
                QTableWidgetItem(order.order_number),
                QTableWidgetItem(order.customer_name),
                QTableWidgetItem(order_status_label(order.status)),
                QTableWidgetItem(format_date(order.order_date)),
                QTableWidgetItem(format_date(order.deadline) if order.deadline else ""),
                QTableWidgetItem(str(len(order.lines))),
                QTableWidgetItem(f"{order.total_amount:.2f}"),
            ]

            for item in items:
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)

            items[0].setData(Qt.UserRole, order.id)

            for column, item in enumerate(items):
                self._table.setItem(row, column, item)

    def _selected_order(self) -> OrderListItem | None:
        selected_items = self._table.selectedItems()
        if not selected_items:
            return None

        row = selected_items[0].row()
        id_item = self._table.item(row, 0)
        if id_item is None:
            return None

        order_id = id_item.data(Qt.UserRole)

        return self._orders_by_id.get(order_id)

    def _sync_action_state(self) -> None:
        set_selection_actions_enabled(
            self._selection_actions,
            self._selected_order() is not None,
        )
