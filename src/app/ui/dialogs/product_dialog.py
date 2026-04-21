from decimal import Decimal, InvalidOperation

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
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


class ProductDialog(QDialog):
    def __init__(self, parent=None, product_id: int | None = None) -> None:
        super().__init__(parent)

        self._product_id = product_id
        self._product: ProductEditItem | None = None
        self._selected_supplier_id: int | None = None
        self._selected_supplier_name: str | None = None
        self._create_variants: list[CreateProductVariantInput] = []

        self.setWindowTitle(
            t("Edit Product") if self._product_id is not None else t("Create Product")
        )
        self.resize(760, 520)

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

        variants_tab = QWidget()
        variants_layout = QVBoxLayout()
        self._variants_table = QTableWidget()
        self._variants_table.setColumnCount(7)
        self._variants_table.setHorizontalHeaderLabels(
            [
                t("SKU"),
                t("Variant"),
                t("Size"),
                t("Color"),
                t("Price"),
                t("Status"),
                t("Default"),
            ]
        )
        self._variants_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._variants_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._variants_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._variants_table.verticalHeader().setVisible(False)
        self._variants_table.setAlternatingRowColors(True)
        self._variants_table.doubleClicked.connect(self._edit_selected_variant)
        self._variants_table.setMinimumHeight(260)

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

        variants_layout.addWidget(self._variants_table)
        variants_layout.addLayout(variant_actions_layout)
        variants_tab.setLayout(variants_layout)

        self._tabs = QTabWidget()
        self._tabs.addTab(product_tab, t("Product Details"))
        self._tabs.addTab(variants_tab, t("Variants"))

        self._buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        translate_button_box(self._buttons)
        self._buttons.accepted.connect(self._on_accept)
        self._buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(self._tabs)
        layout.addWidget(self._buttons)
        self.setLayout(layout)

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
        self._populate_saved_variants_table(product.variants)

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
                    ),
                )

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

    def _populate_saved_variants_table(self, variants: list[ProductVariantEditItem]) -> None:
        rows = [
            {
                "sku": variant.sku,
                "variant": variant.variant_name or "",
                "size": variant.size or "",
                "color": variant.color or "",
                "price": self._variant_price_text(variant.price_override),
                "price_override": variant.price_override is not None,
                "status": t("Active") if variant.is_active else t("Inactive"),
                "default": index == 0,
                "data": variant.id,
            }
            for index, variant in enumerate(variants)
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

        try:
            session = SessionLocal()
        except Exception as exc:
            QMessageBox.critical(self, t("Could not create product variant"), str(exc))
            return

        try:
            CreateProductVariantService(session).execute(self._product_id, dialog.variant_input)
            session.commit()
            self._load_product()
        except Exception as exc:
            session.rollback()
            QMessageBox.critical(self, t("Could not create product variant"), t(str(exc)))
        finally:
            session.close()

    def _edit_selected_variant(self) -> None:
        if self._product_id is None:
            self._edit_selected_create_variant()
            return

        variant = self._selected_saved_variant()
        if variant is None:
            QMessageBox.information(
                self,
                t("No product variant selected"),
                t("Select a product variant."),
            )
            return

        dialog = ProductVariantDialog(self, variant=variant)
        if not dialog.exec() or not isinstance(dialog.variant_input, UpdateProductVariantInput):
            return

        try:
            session = SessionLocal()
        except Exception as exc:
            QMessageBox.critical(self, t("Could not update product variant"), str(exc))
            return

        try:
            UpdateProductVariantService(session).execute(variant.id, dialog.variant_input)
            session.commit()
            self._load_product()
        except Exception as exc:
            session.rollback()
            QMessageBox.critical(self, t("Could not update product variant"), t(str(exc)))
        finally:
            session.close()

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

        variant = self._selected_saved_variant()
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

        try:
            session = SessionLocal()
        except Exception as exc:
            QMessageBox.critical(self, t("Could not update product variant"), str(exc))
            return

        try:
            ProductVariantStatusService(session).execute(variant.id, is_active)
            session.commit()
            self._load_product()
        except Exception as exc:
            session.rollback()
            QMessageBox.critical(self, t("Could not update product variant"), t(str(exc)))
        finally:
            session.close()

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

    def _selected_saved_variant(self) -> ProductVariantEditItem | None:
        if self._product is None:
            return None

        selected_items = self._variants_table.selectedItems()
        if not selected_items:
            return None

        variant_id = selected_items[0].data(Qt.UserRole)
        for variant in self._product.variants:
            if variant.id == variant_id:
                return variant

        return None

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

    def _deactivates_last_active_variant(self, selected_variant: ProductVariantEditItem) -> bool:
        if self._product is None or not selected_variant.is_active:
            return False

        active_variants = [variant for variant in self._product.variants if variant.is_active]
        return len(active_variants) == 1 and active_variants[0].id == selected_variant.id

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
