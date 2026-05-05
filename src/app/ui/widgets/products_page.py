from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.application.dto.product_categories import ProductCategoryOption
from app.application.dto.products import ProductListFilters, ProductListItem
from app.application.services.product_categories import ListProductCategoryOptionsService
from app.application.services.products import (
    GetProductForEditService,
    ListProductsService,
    ProductStatusService,
)
from app.infrastructure.db.session import SessionLocal
from app.ui.dialog_helpers import question
from app.ui.dialogs.product_activation_variants_dialog import ProductActivationVariantsDialog
from app.ui.dialogs.product_dialog import ProductDialog
from app.ui.localization import t
from app.ui.widgets.category_summary_widget import CategorySummaryWidget, category_summary


_UNCATEGORIZED_FILTER = "__uncategorized__"


class ProductsPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self._category_options: list[ProductCategoryOption] = []

        self._title_label = QLabel()
        self._title_label.setObjectName("pageTitle")

        self._search_input = QLineEdit()
        self._search_input.textChanged.connect(self.load_products)

        self._category_filter = QComboBox()
        self._category_filter.currentIndexChanged.connect(self.load_products)

        self._create_button = QPushButton()
        self._create_button.clicked.connect(self.open_create_dialog)

        self._edit_button = QPushButton()
        self._edit_button.clicked.connect(self.open_edit_dialog)

        self._activate_button = QPushButton()
        self._activate_button.clicked.connect(self.activate_selected_product)

        self._deactivate_button = QPushButton()
        self._deactivate_button.clicked.connect(self.deactivate_selected_product)

        self._refresh_button = QPushButton()
        self._refresh_button.clicked.connect(self.refresh_products)

        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.Stretch)

        layout = QVBoxLayout()
        layout.addWidget(self._title_label)

        filters_layout = QHBoxLayout()
        filters_layout.addWidget(self._search_input, 1)
        filters_layout.addWidget(self._category_filter)

        actions_layout = QHBoxLayout()
        actions_layout.addWidget(self._create_button)
        actions_layout.addWidget(self._edit_button)
        actions_layout.addWidget(self._activate_button)
        actions_layout.addWidget(self._deactivate_button)
        actions_layout.addWidget(self._refresh_button)
        actions_layout.addStretch()

        layout.addLayout(filters_layout)
        layout.addLayout(actions_layout)
        layout.addWidget(self._table)

        self.setLayout(layout)

        self.retranslate_ui()
        self._load_category_filter_options()
        self.load_products()

    def retranslate_ui(self) -> None:
        self._title_label.setText(t("Products"))
        self._search_input.setPlaceholderText(
            t("Search by product, category, supplier, SKU, variant, size, or color")
        )
        self._create_button.setText(t("New Product"))
        self._edit_button.setText(t("Edit Product"))
        self._activate_button.setText(t("Activate Product"))
        self._deactivate_button.setText(t("Deactivate Product"))
        self._refresh_button.setText(t("Refresh"))
        self._table.setHorizontalHeaderLabels(
            [
                t("Name"),
                t("Categories"),
                t("Supplier"),
                t("Base Price"),
                t("Track Stock"),
                t("Status"),
                t("Variant Summary"),
            ]
        )
        self._populate_category_filter(preserve_selection=True)
        self._refresh_table_text()

    def open_create_dialog(self) -> None:
        dialog = ProductDialog(self)
        if dialog.exec():
            self.load_products()

    def open_edit_dialog(self) -> None:
        product_id = self._selected_product_id()

        if product_id is None:
            QMessageBox.information(
                self,
                t("No product selected"),
                t("Select a product to edit."),
            )
            return

        dialog = ProductDialog(self, product_id=product_id)
        if dialog.exec():
            self.load_products()

    def activate_selected_product(self) -> None:
        self._change_selected_product_status(
            should_be_active=True,
            action_label="activate",
        )

    def deactivate_selected_product(self) -> None:
        self._change_selected_product_status(
            should_be_active=False,
            action_label="deactivate",
        )

    def _change_selected_product_status(
        self,
        should_be_active: bool,
        action_label: str,
    ) -> None:
        product_id = self._selected_product_id()

        if product_id is None:
            QMessageBox.information(
                self,
                t("No product selected"),
                t(f"Select a product to {action_label}."),
            )
            return

        is_active = self._selected_product_is_active()
        if is_active == should_be_active:
            status = "active" if is_active else "inactive"
            QMessageBox.information(
                self,
                t(f"Product already {status}"),
                t(f"The selected product is already {status}."),
            )
            return

        active_variant_ids = None
        if should_be_active:
            active_variant_ids = self._select_variants_for_activation(product_id)
            if active_variant_ids is None:
                return
        else:
            confirmed = question(
                self,
                t(f"{action_label.title()} product"),
                t(f"{action_label.title()} the selected product?"),
            )

            if confirmed != QMessageBox.Yes:
                return

        try:
            session = SessionLocal()
        except Exception as exc:
            QMessageBox.critical(self, t(f"Could not {action_label} product"), str(exc))
            return

        try:
            service = ProductStatusService(session)
            service.execute(
                product_id,
                is_active=should_be_active,
                active_variant_ids=active_variant_ids,
            )
            session.commit()
            self.load_products()
        except Exception as exc:
            session.rollback()
            QMessageBox.critical(self, t(f"Could not {action_label} product"), t(str(exc)))
        finally:
            session.close()

    def _select_variants_for_activation(self, product_id: int) -> list[int] | None:
        try:
            session = SessionLocal()
        except Exception as exc:
            QMessageBox.critical(self, t("Could not activate product"), str(exc))
            return None

        try:
            product = GetProductForEditService(session).execute(product_id)
        except Exception as exc:
            QMessageBox.critical(self, t("Could not activate product"), t(str(exc)))
            return None
        finally:
            session.close()

        dialog = ProductActivationVariantsDialog(product.variants, self)
        if not dialog.exec():
            return None

        return dialog.selected_variant_ids

    def refresh_products(self, *_args) -> None:
        self._load_category_filter_options()
        self.load_products()

    def load_products(self, *_args) -> None:
        try:
            session = SessionLocal()
        except Exception as exc:
            self._handle_load_products_error(exc)
            return

        try:
            service = ListProductsService(session)
            products = service.execute(self._product_list_filters())
            self._populate_table(products)
        except Exception as exc:
            self._handle_load_products_error(exc)
        finally:
            session.close()

    def _load_category_filter_options(self) -> None:
        try:
            session = SessionLocal()
        except Exception as exc:
            QMessageBox.critical(self, t("Could not load categories"), str(exc))
            self._populate_category_filter(preserve_selection=True)
            return

        try:
            self._category_options = ListProductCategoryOptionsService(session).execute()
            self._populate_category_filter(preserve_selection=True)
        except Exception as exc:
            QMessageBox.critical(self, t("Could not load categories"), t(str(exc)))
            self._populate_category_filter(preserve_selection=True)
        finally:
            session.close()

    def _populate_category_filter(self, preserve_selection: bool) -> None:
        selected_filter = self._selected_category_filter() if preserve_selection else None

        self._category_filter.blockSignals(True)
        self._category_filter.clear()
        self._category_filter.addItem(t("All Categories"), None)
        self._category_filter.addItem(t("Uncategorized"), _UNCATEGORIZED_FILTER)
        for category in self._category_options:
            self._category_filter.addItem(category.name, category.id)

        if selected_filter is not None:
            index = self._category_filter.findData(selected_filter)
            if index >= 0:
                self._category_filter.setCurrentIndex(index)

        self._category_filter.blockSignals(False)

    def _selected_category_filter(self) -> int | str | None:
        return self._category_filter.currentData()

    def _product_list_filters(self) -> ProductListFilters:
        selected_category = self._selected_category_filter()
        return ProductListFilters(
            search_text=self._search_input.text(),
            category_id=selected_category if isinstance(selected_category, int) else None,
            uncategorized_only=selected_category == _UNCATEGORIZED_FILTER,
        )

    def _handle_load_products_error(self, exc: Exception) -> None:
        self._table.setRowCount(0)
        QMessageBox.critical(
            self,
            t("Could not load products"),
            str(exc),
        )

    def _build_variant_summary(self, product: ProductListItem) -> str:
        if not product.variants:
            return t("No variants")

        summaries: list[str] = []

        for variant in product.variants:
            label = variant.variant_name

            if not label:
                parts = [part for part in [variant.size, variant.color] if part]
                label = " / ".join(parts) if parts else t("Default")

            summaries.append(label)

        return ", ".join(summaries)

    def _build_category_summary(self, product: ProductListItem) -> str:
        return self._category_summary(self._product_category_names(product))

    @staticmethod
    def _category_summary(category_names: list[str]) -> str:
        return category_summary(category_names)

    def _populate_table(self, products: list[ProductListItem]) -> None:
        self._table.setRowCount(len(products))

        for row, product in enumerate(products):
            self._table.removeCellWidget(row, 1)
            base_price_text = "" if product.base_price is None else str(product.base_price)
            supplier_text = product.supplier_name or ""
            category_names = self._product_category_names(product)
            categories_text = "" if category_names else self._category_summary(category_names)
            track_stock_text = t("Yes") if product.track_stock else t("No")
            status_text = t("Active") if product.is_active else t("Inactive")
            variant_summary_text = self._build_variant_summary(product)

            items = [
                QTableWidgetItem(product.name),
                QTableWidgetItem(categories_text),
                QTableWidgetItem(supplier_text),
                QTableWidgetItem(base_price_text),
                QTableWidgetItem(track_stock_text),
                QTableWidgetItem(status_text),
                QTableWidgetItem(variant_summary_text),
            ]

            for item in items:
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                if not product.is_active:
                    item.setForeground(QColor("#777777"))
                    item.setBackground(QColor("#f2f2f2"))

            items[0].setData(Qt.UserRole, product.id)
            items[5].setData(Qt.UserRole, product.is_active)

            for column, item in enumerate(items):
                self._table.setItem(row, column, item)

            if category_names:
                self._table.setCellWidget(row, 1, CategorySummaryWidget(category_names, self._table))

    def _refresh_table_text(self) -> None:
        if self._table.rowCount() > 0:
            self.load_products()

    def _selected_product_id(self) -> int | None:
        selected_items = self._table.selectedItems()

        if not selected_items:
            return None

        row = selected_items[0].row()
        id_item = self._table.item(row, 0)

        if id_item is None:
            return None

        return id_item.data(Qt.UserRole)

    def _selected_product_is_active(self) -> bool:
        selected_items = self._table.selectedItems()

        if not selected_items:
            return False

        row = selected_items[0].row()
        status_item = self._table.item(row, 5)

        if status_item is None:
            return False

        return bool(status_item.data(Qt.UserRole))

    @staticmethod
    def _product_category_names(product: ProductListItem) -> list[str]:
        return [category.name for category in product.categories]
