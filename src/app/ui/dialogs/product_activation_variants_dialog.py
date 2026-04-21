from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.application.dto.products import ProductVariantEditItem
from app.ui.dialog_helpers import translate_button_box
from app.ui.localization import t


class ProductActivationVariantsDialog(QDialog):
    def __init__(self, variants: list[ProductVariantEditItem], parent=None) -> None:
        super().__init__(parent)

        self._variants = variants
        self._selected_variant_ids: list[int] = []

        self.setWindowTitle(t("Activate product variants"))
        self.resize(640, 420)

        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels(
            [t("Active"), "SKU", t("Variant"), t("Size"), t("Color"), t("Status")]
        )
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)

        self._select_all_button = QPushButton(t("Select All"))
        self._select_all_button.clicked.connect(lambda: self._set_all_checked(True))
        self._deselect_all_button = QPushButton(t("Deselect All"))
        self._deselect_all_button.clicked.connect(lambda: self._set_all_checked(False))

        actions_layout = QHBoxLayout()
        actions_layout.addWidget(self._select_all_button)
        actions_layout.addWidget(self._deselect_all_button)
        actions_layout.addStretch()

        self._buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        translate_button_box(self._buttons)
        self._buttons.accepted.connect(self._accept_selection)
        self._buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(self._table)
        layout.addLayout(actions_layout)
        layout.addWidget(self._buttons)
        self.setLayout(layout)

        self._populate_table()

    @property
    def selected_variant_ids(self) -> list[int]:
        return self._selected_variant_ids

    def _populate_table(self) -> None:
        self._table.setRowCount(len(self._variants))

        for row, variant in enumerate(self._variants):
            checkbox_item = QTableWidgetItem()
            checkbox_item.setFlags(
                (checkbox_item.flags() | Qt.ItemIsUserCheckable) & ~Qt.ItemIsEditable
            )
            checkbox_item.setCheckState(Qt.Checked if variant.is_active else Qt.Unchecked)
            checkbox_item.setData(Qt.UserRole, variant.id)

            items = [
                checkbox_item,
                QTableWidgetItem(variant.sku),
                QTableWidgetItem(variant.variant_name or ""),
                QTableWidgetItem(variant.size or ""),
                QTableWidgetItem(variant.color or ""),
                QTableWidgetItem(t("Active") if variant.is_active else t("Inactive")),
            ]

            for item in items[1:]:
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setData(Qt.UserRole, variant.id)

            for column, item in enumerate(items):
                self._table.setItem(row, column, item)

    def _set_all_checked(self, checked: bool) -> None:
        check_state = Qt.Checked if checked else Qt.Unchecked
        for row in range(self._table.rowCount()):
            self._table.item(row, 0).setCheckState(check_state)

    def _accept_selection(self) -> None:
        selected_variant_ids = []
        for row in range(self._table.rowCount()):
            item = self._table.item(row, 0)
            if item.checkState() == Qt.Checked:
                selected_variant_ids.append(item.data(Qt.UserRole))

        if not selected_variant_ids:
            QMessageBox.information(
                self,
                t("No product variant selected"),
                t("Select at least one product variant to activate."),
            )
            return

        self._selected_variant_ids = selected_variant_ids
        self.accept()
