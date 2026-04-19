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

from app.application.dto.suppliers import SupplierPickerItem
from app.application.services.suppliers import ListSupplierPickerOptionsService
from app.infrastructure.db.session import SessionLocal
from app.ui.dialog_helpers import translate_button_box
from app.ui.localization import t


class SupplierPickerDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._suppliers: list[SupplierPickerItem] = []
        self._selected_supplier: SupplierPickerItem | None = None

        self.setWindowTitle(t("Select Supplier"))
        self.resize(700, 420)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText(t("Search by name, tax ID, phone, or email"))
        self._search_input.textChanged.connect(self._apply_filter)

        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels(
            [t("ID"), t("Name"), t("Tax ID"), t("Phone"), t("Email"), t("Status")]
        )
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        self._table.doubleClicked.connect(self._accept_selected_supplier)

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)

        self._buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        translate_button_box(self._buttons)
        self._buttons.accepted.connect(self._accept_selected_supplier)
        self._buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(QLabel(t("Supplier")))
        layout.addWidget(self._search_input)
        layout.addWidget(self._table)
        layout.addWidget(self._buttons)
        self.setLayout(layout)

        self._load_suppliers()

    @property
    def selected_supplier(self) -> SupplierPickerItem | None:
        return self._selected_supplier

    def _load_suppliers(self) -> None:
        try:
            session = SessionLocal()
        except Exception as exc:
            QMessageBox.critical(self, t("Could not load suppliers"), str(exc))
            return

        try:
            self._suppliers = ListSupplierPickerOptionsService(session).execute()
            self._apply_filter()
        except Exception as exc:
            QMessageBox.critical(self, t("Could not load suppliers"), str(exc))
        finally:
            session.close()

    def _apply_filter(self) -> None:
        query = self._search_input.text().strip().lower()
        suppliers = [
            supplier for supplier in self._suppliers if self._matches_supplier(supplier, query)
        ]

        self._populate_table(suppliers)

    @staticmethod
    def _matches_supplier(supplier: SupplierPickerItem, query: str) -> bool:
        if not query:
            return True

        fields = [
            supplier.name,
            supplier.tax_id,
            supplier.phone,
            supplier.email,
        ]

        return any(query in (field or "").lower() for field in fields)

    def _populate_table(self, suppliers: list[SupplierPickerItem]) -> None:
        self._table.setRowCount(len(suppliers))

        for row, supplier in enumerate(suppliers):
            status_text = t("Active") if supplier.is_active else t("Inactive")
            items = [
                QTableWidgetItem(str(supplier.id)),
                QTableWidgetItem(supplier.name),
                QTableWidgetItem(supplier.tax_id or ""),
                QTableWidgetItem(supplier.phone or ""),
                QTableWidgetItem(supplier.email or ""),
                QTableWidgetItem(status_text),
            ]

            for item in items:
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setData(Qt.UserRole, supplier)
                if not supplier.is_active:
                    item.setForeground(QColor("#777777"))
                    item.setBackground(QColor("#f2f2f2"))

            for column, item in enumerate(items):
                self._table.setItem(row, column, item)

    def _accept_selected_supplier(self) -> None:
        supplier = self._selected_table_supplier()

        if supplier is None:
            QMessageBox.information(
                self,
                t("No supplier selected"),
                t("Select a supplier."),
            )
            return

        self._selected_supplier = supplier
        self.accept()

    def _selected_table_supplier(self) -> SupplierPickerItem | None:
        selected_items = self._table.selectedItems()

        if not selected_items:
            return None

        return selected_items[0].data(Qt.UserRole)
