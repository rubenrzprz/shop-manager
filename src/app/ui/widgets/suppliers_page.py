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

from app.application.dto.suppliers import SupplierListItem
from app.application.services.suppliers import ListSuppliersService
from app.infrastructure.db.session import SessionLocal
from app.ui.dialogs.supplier_dialog import SupplierDialog


class SuppliersPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self._title_label = QLabel("Suppliers")
        self._title_label.setObjectName("pageTitle")

        self._create_button = QPushButton("New Supplier")
        self._create_button.clicked.connect(self.open_create_dialog)

        self._edit_button = QPushButton("Edit Supplier")
        self._edit_button.clicked.connect(self.open_edit_dialog)

        self._refresh_button = QPushButton("Refresh")
        self._refresh_button.clicked.connect(self.load_suppliers)

        self._table = QTableWidget()
        self._table.setColumnCount(8)
        self._table.setHorizontalHeaderLabels(
            ["ID", "Name", "Tax ID", "Phone", "Email", "City", "Country", "Status"]
        )
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
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

        self.load_suppliers()

    def open_create_dialog(self) -> None:
        dialog = SupplierDialog(self)
        if dialog.exec():
            self.load_suppliers()

    def open_edit_dialog(self) -> None:
        supplier_id = self._selected_supplier_id()

        if supplier_id is None:
            QMessageBox.information(
                self,
                "No supplier selected",
                "Select a supplier to edit.",
            )
            return

        dialog = SupplierDialog(self, supplier_id=supplier_id)
        if dialog.exec():
            self.load_suppliers()

    def load_suppliers(self) -> None:
        try:
            session = SessionLocal()
        except Exception as exc:
            self._handle_load_suppliers_error(exc)
            return

        try:
            suppliers = ListSuppliersService(session).execute()
            self._populate_table(suppliers)
        except Exception as exc:
            self._handle_load_suppliers_error(exc)
        finally:
            session.close()

    def _handle_load_suppliers_error(self, exc: Exception) -> None:
        self._table.setRowCount(0)
        QMessageBox.critical(
            self,
            "Could not load suppliers",
            str(exc),
        )

    def _populate_table(self, suppliers: list[SupplierListItem]) -> None:
        self._table.setRowCount(len(suppliers))

        for row, supplier in enumerate(suppliers):
            status_text = "Active" if supplier.is_active else "Inactive"
            items = [
                QTableWidgetItem(str(supplier.id)),
                QTableWidgetItem(supplier.name),
                QTableWidgetItem(supplier.tax_id or ""),
                QTableWidgetItem(supplier.phone or ""),
                QTableWidgetItem(supplier.email or ""),
                QTableWidgetItem(supplier.city or ""),
                QTableWidgetItem(supplier.country or ""),
                QTableWidgetItem(status_text),
            ]

            for item in items:
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                if not supplier.is_active:
                    item.setForeground(QColor("#777777"))
                    item.setBackground(QColor("#f2f2f2"))

            for column, item in enumerate(items):
                self._table.setItem(row, column, item)

    def _selected_supplier_id(self) -> int | None:
        selected_items = self._table.selectedItems()

        if not selected_items:
            return None

        row = selected_items[0].row()
        id_item = self._table.item(row, 0)

        if id_item is None:
            return None

        return int(id_item.text())
