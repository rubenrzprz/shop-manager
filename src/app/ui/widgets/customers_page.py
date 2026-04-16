from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
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

from app.application.dto.customers import CustomerListItem
from app.application.services.customers import ListCustomersService
from app.infrastructure.db.session import SessionLocal
from app.ui.dialogs.customer_dialog import CustomerDialog


class CustomersPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self._title_label = QLabel("Customers")
        self._title_label.setObjectName("pageTitle")

        self._create_button = QPushButton("New Customer")
        self._create_button.clicked.connect(self.open_create_dialog)

        self._edit_button = QPushButton("Edit Customer")
        self._edit_button.clicked.connect(self.open_edit_dialog)

        self._refresh_button = QPushButton("Refresh")
        self._refresh_button.clicked.connect(self.load_customers)

        self._table = QTableWidget()
        self._table.setColumnCount(9)
        self._table.setHorizontalHeaderLabels(
            ["ID", "Type", "Name", "Company", "Tax ID", "Phone", "Email", "City", "Status"]
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
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.Stretch)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)

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

        self.load_customers()

    def open_create_dialog(self) -> None:
        dialog = CustomerDialog(self)
        if dialog.exec():
            self.load_customers()

    def open_edit_dialog(self) -> None:
        customer_id = self._selected_customer_id()

        if customer_id is None:
            QMessageBox.information(
                self,
                "No customer selected",
                "Select a customer to edit.",
            )
            return

        dialog = CustomerDialog(self, customer_id=customer_id)
        if dialog.exec():
            self.load_customers()

    def load_customers(self) -> None:
        try:
            session = SessionLocal()
        except Exception as exc:
            self._handle_load_customers_error(exc)
            return

        try:
            customers = ListCustomersService(session).execute()
            self._populate_table(customers)
        except Exception as exc:
            self._handle_load_customers_error(exc)
        finally:
            session.close()

    def _handle_load_customers_error(self, exc: Exception) -> None:
        self._table.setRowCount(0)
        QMessageBox.critical(
            self,
            "Could not load customers",
            str(exc),
        )

    def _populate_table(self, customers: list[CustomerListItem]) -> None:
        self._table.setRowCount(len(customers))

        for row, customer in enumerate(customers):
            status_text = "Active" if customer.is_active else "Inactive"
            items = [
                QTableWidgetItem(str(customer.id)),
                QTableWidgetItem(customer.customer_type.value.title()),
                QTableWidgetItem(customer.name),
                QTableWidgetItem(customer.company_name or ""),
                QTableWidgetItem(customer.tax_id or ""),
                QTableWidgetItem(customer.phone or ""),
                QTableWidgetItem(customer.email or ""),
                QTableWidgetItem(customer.city or ""),
                QTableWidgetItem(status_text),
            ]

            for item in items:
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                if not customer.is_active:
                    item.setForeground(QColor("#777777"))
                    item.setBackground(QColor("#f2f2f2"))

            for column, item in enumerate(items):
                self._table.setItem(row, column, item)

    def _selected_customer_id(self) -> int | None:
        selected_items = self._table.selectedItems()

        if not selected_items:
            return None

        row = selected_items[0].row()
        id_item = self._table.item(row, 0)

        if id_item is None:
            return None

        return int(id_item.text())
