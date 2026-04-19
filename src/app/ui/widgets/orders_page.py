from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
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
from app.ui.dialogs.order_dialog import OrderDialog


class OrdersPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self._orders_by_id: dict[int, OrderListItem] = {}

        self._title_label = QLabel("Orders")
        self._title_label.setObjectName("pageTitle")

        self._create_button = QPushButton("New Order")
        self._create_button.clicked.connect(self.open_create_dialog)

        self._edit_button = QPushButton("Edit Order")
        self._edit_button.clicked.connect(self.open_edit_dialog)

        self._advance_status_button = QPushButton("Advance Status")
        self._advance_status_button.clicked.connect(self.advance_selected_order_status)

        self._revert_status_button = QPushButton("Revert Status")
        self._revert_status_button.clicked.connect(self.revert_selected_order_status)

        self._cancel_order_button = QPushButton("Cancel Order")
        self._cancel_order_button.clicked.connect(self.cancel_selected_order)

        self._refresh_button = QPushButton("Refresh")
        self._refresh_button.clicked.connect(self.load_orders)

        self._table = QTableWidget()
        self._table.setColumnCount(8)
        self._table.setHorizontalHeaderLabels(
            ["ID", "Order #", "Customer", "Status", "Order Date", "Deadline", "Lines", "Total"]
        )
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)

        layout = QVBoxLayout()
        layout.addWidget(self._title_label)

        actions_layout = QHBoxLayout()
        actions_layout.addWidget(self._create_button)
        actions_layout.addWidget(self._edit_button)
        actions_layout.addWidget(self._advance_status_button)
        actions_layout.addWidget(self._revert_status_button)
        actions_layout.addWidget(self._cancel_order_button)
        actions_layout.addWidget(self._refresh_button)
        actions_layout.addStretch()

        layout.addLayout(actions_layout)
        layout.addWidget(self._table)
        self.setLayout(layout)

        self.load_orders()

    def open_create_dialog(self) -> None:
        dialog = OrderDialog(self)
        if dialog.exec():
            self.load_orders()

    def open_edit_dialog(self) -> None:
        order = self._selected_order()
        if order is None:
            QMessageBox.information(self, "No order selected", "Select an active order to edit.")
            return

        try:
            session = SessionLocal()
        except Exception as exc:
            QMessageBox.critical(self, "Could not check order edit policy", str(exc))
            return

        try:
            edit_rejection_message = UpdateOrderService(session).full_order_edit_rejection_message(
                order.status
            )
        except Exception as exc:
            QMessageBox.critical(self, "Could not check order edit policy", str(exc))
            return
        finally:
            session.close()

        if edit_rejection_message is not None:
            QMessageBox.information(self, "Order cannot be edited", edit_rejection_message)
            return

        dialog = OrderDialog(self, order_id=order.id)
        if dialog.exec():
            self.load_orders()

    def advance_selected_order_status(self) -> None:
        order = self._selected_order()
        if order is None:
            QMessageBox.information(self, "No order selected", "Select an order to advance.")
            return

        next_status = UpdateOrderStatusService.next_forward_status(order.status)
        if next_status is None:
            QMessageBox.information(
                self,
                "Order cannot advance",
                "Completed and cancelled orders cannot be advanced.",
            )
            return

        self._transition_selected_order(order, next_status)

    def revert_selected_order_status(self) -> None:
        order = self._selected_order()
        if order is None:
            QMessageBox.information(self, "No order selected", "Select an order to revert.")
            return

        previous_status = UpdateOrderStatusService.previous_status(order.status)
        if previous_status is None:
            QMessageBox.information(
                self,
                "Order cannot revert",
                "Draft and cancelled orders cannot be reverted.",
            )
            return

        self._transition_selected_order(order, previous_status)

    def cancel_selected_order(self) -> None:
        order = self._selected_order()
        if order is None:
            QMessageBox.information(self, "No order selected", "Select an order to cancel.")
            return

        if not UpdateOrderStatusService.can_transition(order.status, OrderStatus.CANCELLED):
            QMessageBox.information(
                self,
                "Order cannot be cancelled",
                "Completed and cancelled orders cannot be cancelled.",
            )
            return

        response = QMessageBox.question(
            self,
            "Cancel order",
            "Cancel this order? This cannot be undone from the current workflow.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if response != QMessageBox.Yes:
            return

        self._transition_selected_order(order, OrderStatus.CANCELLED)

    def _transition_selected_order(
        self,
        order: OrderListItem,
        target_status: OrderStatus,
    ) -> None:
        try:
            session = SessionLocal()
        except Exception as exc:
            QMessageBox.critical(self, "Could not update order status", str(exc))
            return

        try:
            UpdateOrderStatusService(session).execute(order.id, target_status)
            session.commit()
            self.load_orders()
        except Exception as exc:
            session.rollback()
            QMessageBox.critical(self, "Could not update order status", str(exc))
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
        except Exception as exc:
            self._handle_load_orders_error(exc)
        finally:
            session.close()

    def _handle_load_orders_error(self, exc: Exception) -> None:
        self._table.setRowCount(0)
        QMessageBox.critical(
            self,
            "Could not load orders",
            str(exc),
        )

    def _populate_table(self, orders: list[OrderListItem]) -> None:
        self._orders_by_id = {order.id: order for order in orders}
        self._table.setRowCount(len(orders))

        for row, order in enumerate(orders):
            items = [
                QTableWidgetItem(str(order.id)),
                QTableWidgetItem(order.order_number),
                QTableWidgetItem(order.customer_name),
                QTableWidgetItem(order.status.value.title().replace("_", " ")),
                QTableWidgetItem(order.order_date.isoformat()),
                QTableWidgetItem(order.deadline.isoformat() if order.deadline else ""),
                QTableWidgetItem(str(len(order.lines))),
                QTableWidgetItem(f"{order.total_amount:.2f}"),
            ]

            for item in items:
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)

            for column, item in enumerate(items):
                self._table.setItem(row, column, item)

    def _selected_order(self) -> OrderListItem | None:
        selected_items = self._table.selectedItems()
        if not selected_items:
            return None

        row = selected_items[0].row()
        order_id = int(self._table.item(row, 0).text())

        return self._orders_by_id.get(order_id)
