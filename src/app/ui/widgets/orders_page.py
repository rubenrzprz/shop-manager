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
from app.application.services.orders import ListOrdersService, UpdateOrderService
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
        selected_items = self._table.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No order selected", "Select an active order to edit.")
            return

        row = selected_items[0].row()
        order_id = int(self._table.item(row, 0).text())
        order = self._orders_by_id.get(order_id)
        if order is None:
            QMessageBox.information(self, "No order selected", "Select an active order to edit.")
            return

        if not UpdateOrderService._can_edit_full_order(order.status):
            QMessageBox.information(
                self, "Order cannot be edited", "Only active orders can be edited."
            )
            return

        dialog = OrderDialog(self, order_id=order_id)
        if dialog.exec():
            self.load_orders()

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
