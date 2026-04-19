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

from app.application.dto.products import ProductVariantPickerItem
from app.application.services.products import ListProductVariantPickerOptionsService
from app.infrastructure.db.session import SessionLocal
from app.ui.dialog_helpers import translate_button_box
from app.ui.localization import t


class ProductVariantPickerDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._variants: list[ProductVariantPickerItem] = []
        self._selected_variant: ProductVariantPickerItem | None = None

        self.setWindowTitle(t("Select Product Variant"))
        self.resize(840, 460)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText(t("Search by product, SKU, variant, size, or color"))
        self._search_input.textChanged.connect(self._apply_filter)

        self._table = QTableWidget()
        self._table.setColumnCount(8)
        self._table.setHorizontalHeaderLabels(
            [
                t("ID"),
                t("Product"),
                "SKU",
                t("Variant"),
                t("Size"),
                t("Color"),
                t("Price"),
                t("Status"),
            ]
        )
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        self._table.doubleClicked.connect(self._accept_selected_variant)

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)

        self._buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        translate_button_box(self._buttons)
        self._buttons.accepted.connect(self._accept_selected_variant)
        self._buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(QLabel(t("Product Variant")))
        layout.addWidget(self._search_input)
        layout.addWidget(self._table)
        layout.addWidget(self._buttons)
        self.setLayout(layout)

        self._load_variants()

    @property
    def selected_variant(self) -> ProductVariantPickerItem | None:
        return self._selected_variant

    def _load_variants(self) -> None:
        try:
            session = SessionLocal()
        except Exception as exc:
            QMessageBox.critical(self, t("Could not load product variants"), str(exc))
            return

        try:
            self._variants = ListProductVariantPickerOptionsService(session).execute()
            self._apply_filter()
        except Exception as exc:
            QMessageBox.critical(self, t("Could not load product variants"), str(exc))
        finally:
            session.close()

    def _apply_filter(self) -> None:
        query = self._search_input.text().strip().lower()
        variants = [variant for variant in self._variants if self._matches_variant(variant, query)]

        self._populate_table(variants)

    @staticmethod
    def _matches_variant(variant: ProductVariantPickerItem, query: str) -> bool:
        if not query:
            return True

        fields = [
            variant.product_name,
            variant.sku,
            variant.variant_name,
            variant.size,
            variant.color,
        ]

        return any(query in (field or "").lower() for field in fields)

    def _populate_table(self, variants: list[ProductVariantPickerItem]) -> None:
        self._table.setRowCount(len(variants))

        for row, variant in enumerate(variants):
            is_active = variant.product_is_active and variant.variant_is_active
            status_text = t("Active") if is_active else t("Inactive")
            items = [
                QTableWidgetItem(str(variant.id)),
                QTableWidgetItem(variant.product_name),
                QTableWidgetItem(variant.sku),
                QTableWidgetItem(variant.variant_name or ""),
                QTableWidgetItem(variant.size or ""),
                QTableWidgetItem(variant.color or ""),
                QTableWidgetItem(f"{variant.price:.2f}" if variant.price is not None else ""),
                QTableWidgetItem(status_text),
            ]

            for item in items:
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setData(Qt.UserRole, variant)
                if not is_active:
                    item.setForeground(QColor("#777777"))
                    item.setBackground(QColor("#f2f2f2"))

            for column, item in enumerate(items):
                self._table.setItem(row, column, item)

    def _accept_selected_variant(self) -> None:
        variant = self._selected_table_variant()

        if variant is None:
            QMessageBox.information(
                self, t("No product variant selected"), t("Select a product variant.")
            )
            return

        if not variant.product_is_active or not variant.variant_is_active:
            QMessageBox.information(
                self,
                t("Inactive product variant"),
                t("Select an active product variant from an active product."),
            )
            return

        self._selected_variant = variant
        self.accept()

    def _selected_table_variant(self) -> ProductVariantPickerItem | None:
        selected_items = self._table.selectedItems()

        if not selected_items:
            return None

        return selected_items[0].data(Qt.UserRole)
