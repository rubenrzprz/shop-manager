from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
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
from app.ui.page_chrome import (
    apply_page_chrome,
    apply_toolbar_chrome,
    build_selection_action_panel,
    configure_table_chrome,
    mark_primary_button,
    set_selection_actions_enabled,
)


class ProductCategoriesPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self._title_label = QLabel()
        self._title_label.setObjectName("pageTitle")

        self._create_button = QPushButton()
        mark_primary_button(self._create_button)
        self._create_button.clicked.connect(self.open_create_dialog)

        self._edit_button = QPushButton()
        self._edit_button.clicked.connect(self.open_edit_dialog)

        self._refresh_button = QPushButton()
        self._refresh_button.clicked.connect(self.load_categories)

        self._table = QTableWidget()
        self._table.setColumnCount(3)
        configure_table_chrome(self._table)
        self._table.itemSelectionChanged.connect(self._sync_action_state)

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)

        layout = QVBoxLayout()
        apply_page_chrome(layout)
        layout.addWidget(self._title_label)

        actions_layout = QHBoxLayout()
        apply_toolbar_chrome(actions_layout)
        actions_layout.addWidget(self._create_button)
        actions_layout.addWidget(self._refresh_button)
        actions_layout.addStretch()

        self._selection_panel_title = QLabel()
        self._selection_panel_hint = QLabel()
        self._selection_actions = [self._edit_button]
        selection_panel = build_selection_action_panel(
            self._selection_panel_title,
            self._selection_panel_hint,
            self._selection_actions,
        )

        content_layout = QHBoxLayout()
        content_layout.setSpacing(14)
        content_layout.addWidget(self._table, 1)
        content_layout.addWidget(selection_panel)

        layout.addLayout(actions_layout)
        layout.addLayout(content_layout, 1)
        self.setLayout(layout)

        self.retranslate_ui()
        self.load_categories()

    def retranslate_ui(self) -> None:
        self._title_label.setText(t("Product Categories"))
        self._create_button.setText(t("New Category"))
        self._edit_button.setText(t("Edit Category"))
        self._refresh_button.setText(t("Refresh"))
        self._selection_panel_title.setText(t("Selected category"))
        self._selection_panel_hint.setText(t("Select a category to use these actions."))
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
            self._sync_action_state()
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

    def _sync_action_state(self) -> None:
        set_selection_actions_enabled(
            self._selection_actions,
            self._selected_category_id() is not None,
        )
