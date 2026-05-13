from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.application.dto.products import (
    CreateProductInput,
    CreateProductVariantInput,
    ProductEditItem,
    ProductVariantEditItem,
    UpdateProductInput,
    UpdateProductVariantInput,
)
from app.application.dto.product_categories import ProductCategoryOption
from app.application.services.product_categories import ListProductCategoryOptionsService
from app.application.services.products import (
    CreateProductService,
    CreateProductVariantService,
    GetProductForEditService,
    ProductVariantStatusService,
    UpdateProductService,
    UpdateProductVariantService,
)
from app.infrastructure.db.session import SessionLocal
from app.ui.dialog_helpers import question, translate_button_box
from app.ui.dialogs.product_variant_dialog import ProductVariantDialog
from app.ui.dialogs.supplier_picker_dialog import SupplierPickerDialog
from app.ui.localization import t
from app.ui.window_sizing import resize_to_available_screen


@dataclass
class _VariantDraft:
    id: int | None
    sku: str | None
    size: str | None
    color: str | None
    variant_name: str | None
    description: str | None
    price_override: Decimal | None
    stock_current: int | None
    stock_minimum: int | None
    is_active: bool
    original_is_active: bool | None = None


class ProductDialog(QDialog):
    def __init__(self, parent=None, product_id: int | None = None) -> None:
        super().__init__(parent)

        self._product_id = product_id
        self._product: ProductEditItem | None = None
        self._selected_supplier_id: int | None = None
        self._selected_supplier_name: str | None = None
        self._create_variants: list[CreateProductVariantInput] = []
        self._variant_drafts: list[_VariantDraft] = []
        self._category_options: list[ProductCategoryOption] = []
        self._category_options_loaded = False
        self._selected_category_ids: list[int] = []

        self.setWindowTitle(
            t("Edit Product") if self._product_id is not None else t("Create Product")
        )
        resize_to_available_screen(
            self,
            width_ratio=0.72,
            height_ratio=0.78,
            min_width=820,
            min_height=560,
        )

        self._name_input = QLineEdit()
        self._supplier_display = QLineEdit()
        self._supplier_display.setMinimumWidth(220)
        self._supplier_display.setReadOnly(True)
        self._supplier_display.setPlaceholderText(t("No supplier selected"))
        self._select_supplier_button = QPushButton(t("Select"))
        self._select_supplier_button.clicked.connect(self._open_supplier_picker)
        self._clear_supplier_button = QPushButton(t("Clear"))
        self._clear_supplier_button.clicked.connect(self._clear_supplier)
        self._supplier_widget = self._build_supplier_widget()

        self._description_input = QPlainTextEdit()
        self._description_input.setFixedHeight(110)

        self._base_price_input = QLineEdit()
        self._track_stock_checkbox = QCheckBox(t("Track Stock"))

        product_form = QFormLayout()
        product_form.addRow(t("Name"), self._name_input)
        product_form.addRow(t("Supplier"), self._supplier_widget)
        product_form.addRow(t("Description"), self._description_input)
        product_form.addRow(t("Base price"), self._base_price_input)
        product_form.addRow("", self._track_stock_checkbox)

        product_tab = QWidget()
        product_layout = QVBoxLayout()
        product_layout.addLayout(product_form)
        product_layout.addStretch()
        product_tab.setLayout(product_layout)

        categories_tab = QWidget()
        categories_layout = QVBoxLayout()
        self._selected_categories_label = QLabel(t("Selected Categories"))
        self._selected_categories_list = QListWidget()
        self._selected_categories_list.setDragDropMode(QAbstractItemView.InternalMove)
        self._selected_categories_list.setDefaultDropAction(Qt.MoveAction)
        self._selected_categories_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self._selected_categories_list.setFixedHeight(108)
        self._selected_categories_list.model().rowsMoved.connect(
            lambda *_args: QTimer.singleShot(0, self._handle_selected_categories_reordered)
        )
        self._available_categories_label = QLabel(t("Available Categories"))
        self._categories_table = QTableWidget()
        self._categories_table.setColumnCount(3)
        self._categories_table.setHorizontalHeaderLabels(
            [t("Category"), t("Description"), t("Status")]
        )
        self._categories_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._categories_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._categories_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._categories_table.verticalHeader().setVisible(False)
        self._categories_table.setAlternatingRowColors(True)
        self._categories_table.doubleClicked.connect(self._add_selected_category)
        categories_header = self._categories_table.horizontalHeader()
        categories_header.setSectionResizeMode(0, QHeaderView.Stretch)
        categories_header.setSectionResizeMode(1, QHeaderView.Stretch)
        categories_header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self._add_category_button = QPushButton(t("Add Category"))
        self._add_category_button.clicked.connect(self._add_selected_category)

        categories_layout.addWidget(self._selected_categories_label)
        categories_layout.addWidget(self._selected_categories_list)
        categories_layout.addWidget(self._available_categories_label)
        categories_layout.addWidget(self._categories_table)
        categories_layout.addWidget(self._add_category_button)
        categories_tab.setLayout(categories_layout)

        variants_tab = QWidget()
        variants_layout = QVBoxLayout()
        self._variants_table = QTableWidget()
        self._variants_table.setColumnCount(7)
        self._set_variants_table_headers()
        self._variants_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._variants_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._variants_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._variants_table.verticalHeader().setVisible(False)
        self._variants_table.setAlternatingRowColors(True)
        self._variants_table.doubleClicked.connect(self._edit_selected_variant)
        self._variants_table.setMinimumHeight(260)
        self._variants_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        variants_header = self._variants_table.horizontalHeader()
        variants_header.setSectionResizeMode(0, QHeaderView.Stretch)
        variants_header.setSectionResizeMode(1, QHeaderView.Stretch)
        variants_header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        variants_header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        variants_header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        variants_header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        variants_header.setSectionResizeMode(6, QHeaderView.Fixed)
        variants_header.resizeSection(6, 52)

        self._add_variant_button = QPushButton(t("Add Variant"))
        self._add_variant_button.clicked.connect(self._add_variant)
        self._edit_variant_button = QPushButton(t("Edit Variant"))
        self._edit_variant_button.clicked.connect(self._edit_selected_variant)
        self._activate_variant_button = QPushButton(t("Activate Variant"))
        self._activate_variant_button.clicked.connect(lambda: self._change_variant_status(True))
        self._deactivate_variant_button = QPushButton(t("Deactivate Variant"))
        self._deactivate_variant_button.clicked.connect(lambda: self._change_variant_status(False))

        variant_actions_layout = QHBoxLayout()
        variant_actions_layout.addWidget(self._add_variant_button)
        variant_actions_layout.addWidget(self._edit_variant_button)
        variant_actions_layout.addWidget(self._activate_variant_button)
        variant_actions_layout.addWidget(self._deactivate_variant_button)
        variant_actions_layout.addStretch()

        variants_layout.addWidget(self._variants_table, 1)
        variants_layout.addLayout(variant_actions_layout)
        variants_tab.setLayout(variants_layout)

        self._tabs = QTabWidget()
        self._tabs.addTab(product_tab, t("Product Details"))
        self._tabs.addTab(categories_tab, t("Categories"))
        self._tabs.addTab(variants_tab, t("Variants"))

        self._buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        translate_button_box(self._buttons)
        self._buttons.accepted.connect(self._on_accept)
        self._buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(self._tabs)
        layout.addWidget(self._buttons)
        self.setLayout(layout)

        self._load_category_options()

        if self._product_id is None:
            self._populate_create_variants_table()
        else:
            self._load_product()

    def _build_supplier_widget(self) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._supplier_display, 1)
        layout.addWidget(self._select_supplier_button)
        layout.addWidget(self._clear_supplier_button)
        widget.setLayout(layout)
        return widget

    def _load_product(self) -> None:
        if self._product_id is None:
            return

        try:
            session = SessionLocal()
        except Exception as exc:
            QMessageBox.critical(self, t("Could not load product"), str(exc))
            self.reject()
            return

        try:
            self._product = GetProductForEditService(session).execute(self._product_id)
            self._populate_product_form(self._product)
        except Exception as exc:
            QMessageBox.critical(self, t("Could not load product"), str(exc))
            self.reject()
        finally:
            session.close()

    def _populate_product_form(self, product: ProductEditItem) -> None:
        self._name_input.setText(product.name)
        self._set_supplier(product.supplier_id, product.supplier_name)
        self._description_input.setPlainText(product.description or "")
        self._base_price_input.setText(
            "" if product.base_price is None else str(product.base_price)
        )
        self._track_stock_checkbox.setChecked(product.track_stock)
        self._selected_category_ids = [category.id for category in product.categories]
        self._populate_categories_table()
        self._variant_drafts = [
            _VariantDraft(
                id=variant.id,
                sku=variant.sku,
                size=variant.size,
                color=variant.color,
                variant_name=variant.variant_name,
                description=variant.description,
                price_override=variant.price_override,
                stock_current=variant.stock_current,
                stock_minimum=variant.stock_minimum,
                is_active=variant.is_active,
                original_is_active=variant.is_active,
            )
            for variant in product.variants
        ]
        self._populate_saved_variants_table()

    def _open_supplier_picker(self) -> None:
        dialog = SupplierPickerDialog(self)
        if dialog.exec() and dialog.selected_supplier is not None:
            supplier = dialog.selected_supplier
            self._set_supplier(supplier.id, supplier.name)

    def _clear_supplier(self) -> None:
        self._set_supplier(None, None)

    def _set_supplier(self, supplier_id: int | None, supplier_name: str | None) -> None:
        self._selected_supplier_id = supplier_id
        self._selected_supplier_name = supplier_name
        self._supplier_display.setText(supplier_name or "")

    def _on_accept(self) -> None:
        name = self._name_input.text().strip()
        supplier_id = self._supplier_input_value()
        description = self._description_input.toPlainText().strip() or None
        track_stock = self._track_stock_checkbox.isChecked()

        try:
            base_price = self._parse_decimal(self._base_price_input.text(), t("Base price"))
        except ValueError as exc:
            QMessageBox.critical(self, t("Invalid data"), str(exc))
            return

        try:
            session = SessionLocal()
        except Exception as exc:
            QMessageBox.critical(self, t("Could not create product"), str(exc))
            return

        try:
            if self._product_id is None:
                if not self._create_variants:
                    raise ValueError(t("Add at least one product variant."))

                CreateProductService(session).execute(
                    CreateProductInput(
                        name=name,
                        supplier_id=supplier_id,
                        description=description,
                        base_price=base_price,
                        track_stock=track_stock,
                        category_ids=self._selected_category_ids_from_table(),
                        variants=self._create_variants,
                    )
                )
            else:
                if self._product is None:
                    raise ValueError(t("Product was not loaded."))

                UpdateProductService(session).execute(
                    self._product_id,
                    UpdateProductInput(
                        name=name,
                        supplier_id=supplier_id,
                        description=description,
                        base_price=base_price,
                        track_stock=track_stock,
                        category_ids=self._selected_category_ids_from_table(),
                    ),
                )
                self._apply_pending_variant_changes(session)

            session.commit()
            self.accept()

        except Exception as exc:
            session.rollback()
            action = "update" if self._product_id is not None else "create"
            QMessageBox.critical(self, t(f"Could not {action} product"), t(str(exc)))
        finally:
            session.close()

    def _populate_create_variants_table(self) -> None:
        rows = [
            {
                "sku": variant.sku or "",
                "variant": variant.variant_name or "",
                "size": variant.size or "",
                "color": variant.color or "",
                "price": self._variant_price_text(variant.price_override),
                "price_override": variant.price_override is not None,
                "status": t("Active") if variant.is_active else t("Inactive"),
                "default": index == 0,
                "data": index,
            }
            for index, variant in enumerate(self._create_variants)
        ]
        self._populate_variants_table(rows)

    def _populate_saved_variants_table(self) -> None:
        rows = [
            {
                "sku": variant.sku or "",
                "variant": variant.variant_name or "",
                "size": variant.size or "",
                "color": variant.color or "",
                "price": self._variant_price_text(variant.price_override),
                "price_override": variant.price_override is not None,
                "status": t("Active") if variant.is_active else t("Inactive"),
                "default": index == 0,
                "data": index,
            }
            for index, variant in enumerate(self._variant_drafts)
        ]
        self._populate_variants_table(rows)

    def _populate_variants_table(self, rows: list[dict]) -> None:
        self._variants_table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            items = [
                QTableWidgetItem(row["sku"]),
                QTableWidgetItem(row["variant"]),
                QTableWidgetItem(row["size"]),
                QTableWidgetItem(row["color"]),
                QTableWidgetItem(row["price"]),
                QTableWidgetItem(row["status"]),
                QTableWidgetItem("✓" if row["default"] else ""),
            ]
            items[6].setTextAlignment(Qt.AlignCenter)

            for item in items:
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setData(Qt.UserRole, row["data"])
                if row["default"]:
                    item.setBackground(QColor("#fff4ce"))

            if row["price_override"]:
                items[4].setBackground(QColor("#e8f4ff"))
                font = QFont(items[4].font())
                font.setBold(True)
                items[4].setFont(font)

            for column, item in enumerate(items):
                self._variants_table.setItem(row_index, column, item)

    def _set_variants_table_headers(self) -> None:
        header_labels = [
            t("SKU"),
            t("Variant"),
            t("Size"),
            t("Color"),
            t("Price"),
            t("Status"),
            "✓",
        ]
        self._variants_table.setHorizontalHeaderLabels(header_labels)
        default_header = self._variants_table.horizontalHeaderItem(6)
        if default_header is not None:
            default_header.setToolTip(t("Default"))

    def _load_category_options(self) -> None:
        try:
            session = SessionLocal()
        except Exception as exc:
            QMessageBox.critical(self, t("Could not load categories"), str(exc))
            return

        try:
            self._category_options = ListProductCategoryOptionsService(session).execute()
            self._category_options_loaded = True
            self._populate_categories_table()
        except Exception as exc:
            self._category_options_loaded = False
            QMessageBox.critical(self, t("Could not load categories"), t(str(exc)))
        finally:
            session.close()

    def _populate_categories_table(self) -> None:
        self._categories_table.setHorizontalHeaderLabels(
            [t("Category"), t("Description"), t("Status")]
        )
        available_categories = [
            category
            for category in self._category_options
            if category.id not in self._selected_category_ids
        ]
        self._categories_table.setRowCount(len(available_categories))

        for row, category in enumerate(available_categories):
            name_item = QTableWidgetItem(category.name)
            description_item = QTableWidgetItem(category.description or "")
            status_item = QTableWidgetItem(t("Active") if category.is_active else t("Inactive"))
            name_item.setData(Qt.UserRole, category.id)

            for item in [name_item, description_item, status_item]:
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                if not category.is_active:
                    item.setForeground(QColor("#777777"))
                    item.setBackground(QColor("#f2f2f2"))

            self._categories_table.setItem(row, 0, name_item)
            self._categories_table.setItem(row, 1, description_item)
            self._categories_table.setItem(row, 2, status_item)
        self._populate_selected_categories()

    def _populate_selected_categories(self) -> None:
        self._selected_categories_list.clear()

        selected_options = [
            option
            for category_id in self._selected_category_ids
            for option in self._category_options
            if option.id == category_id
        ]

        if not selected_options:
            item = QListWidgetItem(t("No categories selected"))
            item.setFlags(item.flags() & ~Qt.ItemIsDragEnabled)
            item.setForeground(QColor("#777777"))
            self._selected_categories_list.addItem(item)
            return

        for index, category in enumerate(selected_options):
            item = QListWidgetItem()
            item.setData(Qt.UserRole, category.id)
            item.setSizeHint(self._selected_category_item_widget(category, index == 0).sizeHint())
            self._selected_categories_list.addItem(item)
            self._selected_categories_list.setItemWidget(
                item,
                self._selected_category_item_widget(category, index == 0),
            )

    def _selected_category_ids_from_table(self) -> list[int]:
        self._sync_selected_categories_from_list()
        return list(self._selected_category_ids)

    def _add_selected_category(self) -> None:
        self._sync_selected_categories_from_list()
        category_id = self._selected_available_category_id()
        if category_id is None:
            return

        category = next(
            (option for option in self._category_options if option.id == category_id),
            None,
        )
        if category is None or not category.is_active:
            return

        self._selected_category_ids.append(category_id)
        self._populate_categories_table()

    def _remove_category(self, category_id: int) -> None:
        for row in range(self._selected_categories_list.count()):
            item = self._selected_categories_list.item(row)
            if item.data(Qt.UserRole) == category_id:
                self._selected_categories_list.takeItem(row)
                break
        self._sync_selected_categories_from_list()
        self._populate_categories_table()

    def _selected_available_category_id(self) -> int | None:
        row = self._categories_table.currentRow()
        if row < 0:
            return None

        item = self._categories_table.item(row, 0)
        if item is None:
            return None

        return item.data(Qt.UserRole)

    def _sync_selected_categories_from_list(self) -> None:
        if not self._category_options_loaded and self._selected_category_ids:
            return

        category_ids: list[int] = []
        for row in range(self._selected_categories_list.count()):
            item = self._selected_categories_list.item(row)
            category_id = item.data(Qt.UserRole)
            if category_id is not None:
                category_ids.append(category_id)

        self._selected_category_ids = category_ids

    def _handle_selected_categories_reordered(self) -> None:
        self._sync_selected_categories_from_list()
        self._populate_categories_table()

    def _selected_category_item_widget(
        self,
        category: ProductCategoryOption,
        is_primary: bool,
    ) -> QWidget:
        widget = QWidget()
        widget.setStyleSheet(
            "background: #d9ecff; border: 1px solid #7fb3df; border-radius: 4px;"
            if is_primary
            else "background: #f4f8fc; border: 1px solid #c7d6e4; border-radius: 4px;"
        )
        layout = QHBoxLayout()
        layout.setContentsMargins(8, 2, 6, 2)
        layout.setSpacing(6)
        label = QLabel(category.name)
        if is_primary:
            label.setStyleSheet("font-weight: 600; border: 0; background: transparent;")
        else:
            label.setStyleSheet("border: 0; background: transparent;")
        remove_button = QToolButton()
        remove_button.setText("x")
        remove_button.setAutoRaise(True)
        remove_button.setFixedSize(22, 22)
        remove_button.clicked.connect(
            lambda _checked=False, category_id=category.id: self._remove_category(category_id)
        )
        layout.addWidget(label)
        layout.addStretch()
        layout.addWidget(remove_button)
        widget.setLayout(layout)
        return widget

    def _variant_price_text(self, price_override: Decimal | None) -> str:
        price = price_override
        if price is None:
            try:
                price = self._parse_decimal(self._base_price_input.text(), t("Base price"))
            except ValueError:
                price = None

        return f"{price:.2f}" if price is not None else ""

    def _add_variant(self) -> None:
        dialog = ProductVariantDialog(self)
        if not dialog.exec() or not isinstance(dialog.variant_input, CreateProductVariantInput):
            return

        if self._product_id is None:
            self._create_variants.append(dialog.variant_input)
            self._populate_create_variants_table()
            return

        self._variant_drafts.append(self._draft_from_create_input(dialog.variant_input))
        self._populate_saved_variants_table()

    def _edit_selected_variant(self) -> None:
        if self._product_id is None:
            self._edit_selected_create_variant()
            return

        variant_index = self._selected_saved_variant_index()
        if variant_index is None:
            QMessageBox.information(
                self,
                t("No product variant selected"),
                t("Select a product variant."),
            )
            return

        variant = self._variant_drafts[variant_index]
        if variant.id is None:
            dialog = ProductVariantDialog(
                self, create_variant=self._create_input_from_draft(variant)
            )
            if not dialog.exec() or not isinstance(dialog.variant_input, CreateProductVariantInput):
                return

            self._variant_drafts[variant_index] = self._draft_from_create_input(
                dialog.variant_input
            )
            self._populate_saved_variants_table()
            return

        dialog = ProductVariantDialog(self, variant=self._edit_item_from_draft(variant))
        if not dialog.exec() or not isinstance(dialog.variant_input, UpdateProductVariantInput):
            return

        self._variant_drafts[variant_index] = self._draft_from_update_input(
            variant,
            dialog.variant_input,
        )
        self._populate_saved_variants_table()

    def _edit_selected_create_variant(self) -> None:
        index = self._selected_create_variant_index()
        if index is None:
            QMessageBox.information(
                self,
                t("No product variant selected"),
                t("Select a product variant."),
            )
            return

        dialog = ProductVariantDialog(self, create_variant=self._create_variants[index])
        if not dialog.exec() or not isinstance(dialog.variant_input, CreateProductVariantInput):
            return

        self._create_variants[index] = dialog.variant_input
        self._populate_create_variants_table()

    def _change_variant_status(self, is_active: bool) -> None:
        if self._product_id is None:
            self._change_create_variant_status(is_active)
            return

        variant_index = self._selected_saved_variant_index()
        if variant_index is None:
            QMessageBox.information(
                self,
                t("No product variant selected"),
                t("Select a product variant."),
            )
            return

        variant = self._variant_drafts[variant_index]
        if variant is None:
            QMessageBox.information(
                self,
                t("No product variant selected"),
                t("Select a product variant."),
            )
            return

        if not is_active and self._deactivates_last_active_variant(variant):
            response = question(
                self,
                t("Deactivate variant"),
                t("This is the last active variant. The product will become inactive. Continue?"),
            )
            if response != QMessageBox.Yes:
                return

        variant.is_active = is_active
        self._populate_saved_variants_table()

    def _change_create_variant_status(self, is_active: bool) -> None:
        index = self._selected_create_variant_index()
        if index is None:
            QMessageBox.information(
                self,
                t("No product variant selected"),
                t("Select a product variant."),
            )
            return

        variant = self._create_variants[index]
        if not is_active and variant.is_active and self._is_last_active_create_variant(index):
            response = question(
                self,
                t("Deactivate variant"),
                t("This is the last active variant. The product will become inactive. Continue?"),
            )
            if response != QMessageBox.Yes:
                return

        self._create_variants[index] = CreateProductVariantInput(
            sku=variant.sku,
            variant_name=variant.variant_name,
            size=variant.size,
            color=variant.color,
            description=variant.description,
            price_override=variant.price_override,
            stock_current=variant.stock_current,
            stock_minimum=variant.stock_minimum,
            is_active=is_active,
        )
        self._populate_create_variants_table()

    def _selected_saved_variant_index(self) -> int | None:
        selected_items = self._variants_table.selectedItems()
        if not selected_items:
            return None

        return selected_items[0].data(Qt.UserRole)

    def _selected_create_variant_index(self) -> int | None:
        selected_items = self._variants_table.selectedItems()
        if not selected_items:
            return None

        return selected_items[0].data(Qt.UserRole)

    def _is_last_active_create_variant(self, selected_index: int) -> bool:
        active_indexes = [
            index for index, variant in enumerate(self._create_variants) if variant.is_active
        ]
        return active_indexes == [selected_index]

    def _deactivates_last_active_variant(self, selected_variant: _VariantDraft) -> bool:
        if not selected_variant.is_active:
            return False

        active_variants = [variant for variant in self._variant_drafts if variant.is_active]
        return len(active_variants) == 1 and active_variants[0] is selected_variant

    def _apply_pending_variant_changes(self, session) -> None:
        if self._product_id is None:
            return

        existing_variants = [variant for variant in self._variant_drafts if variant.id is not None]
        new_variants = [variant for variant in self._variant_drafts if variant.id is None]

        for variant in existing_variants:
            if variant.id is None:
                continue

            UpdateProductVariantService(session).execute(
                variant.id,
                UpdateProductVariantInput(
                    variant_id=variant.id,
                    size=variant.size,
                    color=variant.color,
                    variant_name=variant.variant_name,
                    description=variant.description,
                    price_override=variant.price_override,
                    stock_current=variant.stock_current,
                    stock_minimum=variant.stock_minimum,
                ),
            )

        for variant in existing_variants:
            if (
                variant.id is not None
                and variant.original_is_active is False
                and variant.is_active is True
            ):
                ProductVariantStatusService(session).execute(variant.id, True)

        for variant in new_variants:
            if variant.id is None:
                CreateProductVariantService(session).execute(
                    self._product_id,
                    self._create_input_from_draft(variant),
                )

        for variant in existing_variants:
            if (
                variant.id is not None
                and variant.original_is_active is True
                and variant.is_active is False
            ):
                ProductVariantStatusService(session).execute(variant.id, False)

    @staticmethod
    def _draft_from_create_input(data: CreateProductVariantInput) -> _VariantDraft:
        return _VariantDraft(
            id=None,
            sku=data.sku,
            size=data.size,
            color=data.color,
            variant_name=data.variant_name,
            description=data.description,
            price_override=data.price_override,
            stock_current=data.stock_current,
            stock_minimum=data.stock_minimum,
            is_active=data.is_active,
        )

    @staticmethod
    def _draft_from_update_input(
        draft: _VariantDraft,
        data: UpdateProductVariantInput,
    ) -> _VariantDraft:
        return _VariantDraft(
            id=draft.id,
            sku=draft.sku,
            size=data.size,
            color=data.color,
            variant_name=data.variant_name,
            description=data.description,
            price_override=data.price_override,
            stock_current=data.stock_current,
            stock_minimum=data.stock_minimum,
            is_active=draft.is_active,
            original_is_active=draft.original_is_active,
        )

    @staticmethod
    def _create_input_from_draft(draft: _VariantDraft) -> CreateProductVariantInput:
        return CreateProductVariantInput(
            sku=draft.sku,
            size=draft.size,
            color=draft.color,
            variant_name=draft.variant_name,
            description=draft.description,
            price_override=draft.price_override,
            stock_current=draft.stock_current,
            stock_minimum=draft.stock_minimum,
            is_active=draft.is_active,
        )

    @staticmethod
    def _edit_item_from_draft(draft: _VariantDraft) -> ProductVariantEditItem:
        if draft.id is None:
            raise ValueError("Product variant was not saved.")

        return ProductVariantEditItem(
            id=draft.id,
            sku=draft.sku or "",
            size=draft.size,
            color=draft.color,
            variant_name=draft.variant_name,
            description=draft.description,
            price_override=draft.price_override,
            stock_current=draft.stock_current,
            stock_minimum=draft.stock_minimum,
            is_active=draft.is_active,
        )

    @staticmethod
    def _parse_decimal(raw_value: str, field_label: str = "Base price") -> Decimal | None:
        value = raw_value.strip()
        if not value:
            return None

        try:
            parsed = Decimal(value.replace(",", "."))
        except InvalidOperation as exc:
            raise ValueError(
                t("{field_label} must be a valid number.").format(field_label=field_label)
            ) from exc

        if not parsed.is_finite():
            raise ValueError(
                t("{field_label} must be a finite number.").format(field_label=field_label)
            )

        return parsed

    def _supplier_input_value(self):
        return self._selected_supplier_id
