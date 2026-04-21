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
from app.ui.localization import t


class CustomersPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self._title_label = QLabel()
        self._title_label.setObjectName("pageTitle")

        self._create_button = QPushButton()
        self._create_button.clicked.connect(self.open_create_dialog)

        self._edit_button = QPushButton()
        self._edit_button.clicked.connect(self.open_edit_dialog)

        self._refresh_button = QPushButton()
        self._refresh_button.clicked.connect(self.load_customers)

        self._table = QTableWidget()
        self._table.setColumnCount(8)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
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

        self.retranslate_ui()
        self.load_customers()

    def retranslate_ui(self) -> None:
        self._title_label.setText(t("Customers"))
        self._create_button.setText(t("New Customer"))
        self._edit_button.setText(t("Edit Customer"))
        self._refresh_button.setText(t("Refresh"))
        self._table.setHorizontalHeaderLabels(
            [
                t("Type"),
                t("Name"),
                t("Company"),
                t("Tax ID"),
                t("Phone"),
                t("Email"),
                t("City"),
                t("Status"),
            ]
        )
        if self._table.rowCount() > 0:
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
                t("No customer selected"),
                t("Select a customer to edit."),
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
            t("Could not load customers"),
            str(exc),
        )

    def _populate_table(self, customers: list[CustomerListItem]) -> None:
        self._table.setRowCount(len(customers))

        for row, customer in enumerate(customers):
            status_text = t("Active") if customer.is_active else t("Inactive")
            customer_type_text = t(customer.customer_type.value.title())
            items = [
                QTableWidgetItem(customer_type_text),
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

            items[0].setData(Qt.UserRole, customer.id)

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

        return id_item.data(Qt.UserRole)
