from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.application.dto.customers import CustomerPickerItem
from app.application.services.customers import ListCustomerPickerOptionsService
from app.infrastructure.db.session import SessionLocal


class CustomerPickerDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._customers: list[CustomerPickerItem] = []
        self._selected_customer: CustomerPickerItem | None = None

        self.setWindowTitle("Select Customer")
        self.resize(760, 420)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search by name, company, tax ID, phone, or email")
        self._search_input.textChanged.connect(self._apply_filter)

        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels(
            ["ID", "Type", "Name", "Company", "Tax ID", "Phone", "Status"]
        )
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        self._table.doubleClicked.connect(self._accept_selected_customer)

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)

        self._buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self._buttons.accepted.connect(self._accept_selected_customer)
        self._buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Customer"))
        layout.addWidget(self._search_input)
        layout.addWidget(self._table)
        layout.addWidget(self._buttons)
        self.setLayout(layout)

        self._load_customers()

    @property
    def selected_customer(self) -> CustomerPickerItem | None:
        return self._selected_customer

    def _load_customers(self) -> None:
        try:
            session = SessionLocal()
        except Exception as exc:
            QMessageBox.critical(self, "Could not load customers", str(exc))
            return

        try:
            self._customers = ListCustomerPickerOptionsService(session).execute()
            self._apply_filter()
        except Exception as exc:
            QMessageBox.critical(self, "Could not load customers", str(exc))
        finally:
            session.close()

    def _apply_filter(self) -> None:
        query = self._search_input.text().strip().lower()
        customers = [
            customer
            for customer in self._customers
            if self._matches_customer(customer, query)
        ]

        self._populate_table(customers)

    @staticmethod
    def _matches_customer(customer: CustomerPickerItem, query: str) -> bool:
        if not query:
            return True

        fields = [
            customer.name,
            customer.company_name,
            customer.tax_id,
            customer.phone,
            customer.email,
        ]

        return any(query in (field or "").lower() for field in fields)

    def _populate_table(self, customers: list[CustomerPickerItem]) -> None:
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
                QTableWidgetItem(status_text),
            ]

            for item in items:
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setData(Qt.UserRole, customer)
                if not customer.is_active:
                    item.setForeground(QColor("#777777"))
                    item.setBackground(QColor("#f2f2f2"))

            for column, item in enumerate(items):
                self._table.setItem(row, column, item)

    def _accept_selected_customer(self) -> None:
        customer = self._selected_table_customer()

        if customer is None:
            QMessageBox.information(self, "No customer selected", "Select a customer.")
            return

        if not customer.is_active:
            QMessageBox.information(
                self,
                "Inactive customer",
                "Select an active customer.",
            )
            return

        self._selected_customer = customer
        self.accept()

    def _selected_table_customer(self) -> CustomerPickerItem | None:
        selected_items = self._table.selectedItems()

        if not selected_items:
            return None

        return selected_items[0].data(Qt.UserRole)
