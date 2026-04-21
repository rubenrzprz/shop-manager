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

from app.application.dto.product_categories import ProductCategoryListItem
from app.application.services.product_categories import ListProductCategoriesService
from app.infrastructure.db.session import SessionLocal
from app.ui.dialogs.product_category_dialog import ProductCategoryDialog
from app.ui.localization import t


class ProductCategoriesPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self._title_label = QLabel()
        self._title_label.setObjectName("pageTitle")

        self._create_button = QPushButton()
        self._create_button.clicked.connect(self.open_create_dialog)

        self._edit_button = QPushButton()
        self._edit_button.clicked.connect(self.open_edit_dialog)

        self._refresh_button = QPushButton()
        self._refresh_button.clicked.connect(self.load_categories)

        self._table = QTableWidget()
        self._table.setColumnCount(3)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)

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
        self.load_categories()

    def retranslate_ui(self) -> None:
        self._title_label.setText(t("Product Categories"))
        self._create_button.setText(t("New Category"))
        self._edit_button.setText(t("Edit Category"))
        self._refresh_button.setText(t("Refresh"))
        self._table.setHorizontalHeaderLabels(
            [
                t("Name"),
                t("Description"),
                t("Status"),
            ]
        )
        if self._table.rowCount() > 0:
            self.load_categories()

    def open_create_dialog(self) -> None:
        dialog = ProductCategoryDialog(self)
        if dialog.exec():
            self.load_categories()

    def open_edit_dialog(self) -> None:
        category_id = self._selected_category_id()
        if category_id is None:
            QMessageBox.information(
                self,
                t("No category selected"),
                t("Select a category to edit."),
            )
            return

        dialog = ProductCategoryDialog(self, category_id=category_id)
        if dialog.exec():
            self.load_categories()

    def load_categories(self) -> None:
        try:
            session = SessionLocal()
        except Exception as exc:
            self._handle_load_categories_error(exc)
            return

        try:
            categories = ListProductCategoriesService(session).execute()
            self._populate_table(categories)
        except Exception as exc:
            self._handle_load_categories_error(exc)
        finally:
            session.close()

    def _handle_load_categories_error(self, exc: Exception) -> None:
        self._table.setRowCount(0)
        QMessageBox.critical(self, t("Could not load categories"), str(exc))

    def _populate_table(self, categories: list[ProductCategoryListItem]) -> None:
        self._table.setRowCount(len(categories))

        for row, category in enumerate(categories):
            status_text = t("Active") if category.is_active else t("Inactive")
            items = [
                QTableWidgetItem(category.name),
                QTableWidgetItem(category.description or ""),
                QTableWidgetItem(status_text),
            ]

            for item in items:
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                if not category.is_active:
                    item.setForeground(QColor("#777777"))
                    item.setBackground(QColor("#f2f2f2"))

            items[0].setData(Qt.UserRole, category.id)

            for column, item in enumerate(items):
                self._table.setItem(row, column, item)

    def _selected_category_id(self) -> int | None:
        selected_items = self._table.selectedItems()
        if not selected_items:
            return None

        row = selected_items[0].row()
        id_item = self._table.item(row, 0)
        if id_item is None:
            return None

        return id_item.data(Qt.UserRole)
