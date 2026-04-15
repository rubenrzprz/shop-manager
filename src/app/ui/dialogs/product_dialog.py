from decimal import Decimal, InvalidOperation

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QVBoxLayout,
)

from app.application.dto.products import (
    CreateProductInput,
    CreateProductVariantInput,
    ProductEditItem,
    UNSET,
    UpdateProductInput,
    UpdateProductVariantInput,
)
from app.application.services.products import (
    CreateProductService,
    GetProductForEditService,
    ListProductFormSuppliersService,
    UpdateProductService,
)
from app.infrastructure.db.session import SessionLocal


class ProductDialog(QDialog):
    def __init__(self, parent=None, product_id: int | None = None) -> None:
        super().__init__(parent)

        self._product_id = product_id
        self._product: ProductEditItem | None = None

        self.setWindowTitle("Edit Product" if self._product_id is not None else "Create Product")
        self.resize(500, 420)

        self._name_input = QLineEdit()
        self._supplier_combo = QComboBox()
        self._supplier_combo.addItem("No supplier", None)

        self._description_input = QPlainTextEdit()
        self._description_input.setFixedHeight(90)

        self._base_price_input = QLineEdit()
        self._track_stock_checkbox = QCheckBox("Track stock")

        self._variant_name_input = QLineEdit()
        self._variant_name_input.setPlaceholderText("Default")
        self._variant_size_input = QLineEdit()
        self._variant_color_input = QLineEdit()
        self._variant_price_override_input = QLineEdit()
        self._variant_description_input = QPlainTextEdit()
        self._variant_description_input.setFixedHeight(70)

        form = QFormLayout()
        form.addRow("Name", self._name_input)
        form.addRow("Supplier", self._supplier_combo)
        form.addRow("Description", self._description_input)
        form.addRow("Base price", self._base_price_input)
        form.addRow("", self._track_stock_checkbox)
        form.addRow("Default variant name", self._variant_name_input)
        form.addRow("Default variant size", self._variant_size_input)
        form.addRow("Default variant color", self._variant_color_input)
        form.addRow("Default variant price override", self._variant_price_override_input)
        form.addRow("Default variant description", self._variant_description_input)

        self._buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        self._buttons.accepted.connect(self._on_accept)
        self._buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(self._buttons)
        self.setLayout(layout)

        self._load_suppliers()
        if self._product_id is not None:
            self._load_product()

    def _load_suppliers(self) -> None:
        try:
            session = SessionLocal()
        except Exception as exc:
            QMessageBox.critical(self, "Could not load suppliers", str(exc))
            self._supplier_combo.setEnabled(False)
            return

        try:
            suppliers = ListProductFormSuppliersService(session).execute()
            for supplier in suppliers:
                self._supplier_combo.addItem(supplier.name, supplier.id)
        except Exception as exc:
            QMessageBox.critical(self, "Could not load suppliers", str(exc))
            self._supplier_combo.setEnabled(False)
        finally:
            session.close()

    def _load_product(self) -> None:
        if self._product_id is None:
            return

        try:
            session = SessionLocal()
        except Exception as exc:
            QMessageBox.critical(self, "Could not load product", str(exc))
            self.reject()
            return

        try:
            self._product = GetProductForEditService(session).execute(self._product_id)
            self._populate_product_form(self._product)
        except Exception as exc:
            QMessageBox.critical(self, "Could not load product", str(exc))
            self.reject()
        finally:
            session.close()

    def _populate_product_form(self, product: ProductEditItem) -> None:
        self._name_input.setText(product.name)
        self._select_supplier(product.supplier_id)
        self._description_input.setPlainText(product.description or "")
        self._base_price_input.setText("" if product.base_price is None else str(product.base_price))
        self._track_stock_checkbox.setChecked(product.track_stock)

        variant = product.default_variant
        self._variant_name_input.setText(variant.variant_name or "")
        self._variant_size_input.setText(variant.size or "")
        self._variant_color_input.setText(variant.color or "")
        self._variant_price_override_input.setText(
            "" if variant.price_override is None else str(variant.price_override)
        )
        self._variant_description_input.setPlainText(variant.description or "")

    def _select_supplier(self, supplier_id: int | None) -> None:
        index = self._supplier_combo.findData(supplier_id)
        if index >= 0:
            self._supplier_combo.setCurrentIndex(index)

    def _on_accept(self) -> None:
        name = self._name_input.text().strip()
        supplier_id = self._supplier_input_value()
        description = self._description_input.toPlainText().strip() or None
        track_stock = self._track_stock_checkbox.isChecked()
        raw_variant_name = self._variant_name_input.text().strip()
        variant_name = raw_variant_name or ("Default" if self._product_id is None else None)
        variant_size = self._variant_size_input.text().strip() or None
        variant_color = self._variant_color_input.text().strip() or None
        variant_description = self._variant_description_input.toPlainText().strip() or None

        try:
            base_price = self._parse_decimal(self._base_price_input.text())
            variant_price_override = self._parse_decimal(
                self._variant_price_override_input.text(),
                "Default variant price override",
            )
        except ValueError as exc:
            QMessageBox.critical(self, "Invalid data", str(exc))
            return

        try:
            session = SessionLocal()
        except Exception as exc:
            QMessageBox.critical(self, "Could not create product", str(exc))
            return

        try:
            if self._product_id is None:
                data = CreateProductInput(
                    name=name,
                    supplier_id=supplier_id,
                    description=description,
                    base_price=base_price,
                    track_stock=track_stock,
                    variants=[
                        CreateProductVariantInput(
                            size=variant_size,
                            color=variant_color,
                            variant_name=variant_name,
                            description=variant_description,
                            price_override=variant_price_override,
                        )
                    ],
                )
                CreateProductService(session).execute(data)
            else:
                if self._product is None:
                    raise ValueError("Product was not loaded.")

                data = UpdateProductInput(
                    name=name,
                    supplier_id=supplier_id,
                    description=description,
                    base_price=base_price,
                    track_stock=track_stock,
                    default_variant=UpdateProductVariantInput(
                        variant_id=self._product.default_variant.id,
                        size=variant_size,
                        color=variant_color,
                        variant_name=variant_name,
                        description=variant_description,
                        price_override=variant_price_override,
                    ),
                )
                UpdateProductService(session).execute(self._product_id, data)

            session.commit()
            self.accept()

        except Exception as exc:
            session.rollback()
            action = "update" if self._product_id is not None else "create"
            QMessageBox.critical(self, f"Could not {action} product", str(exc))
        finally:
            session.close()

    @staticmethod
    def _parse_decimal(raw_value: str, field_label: str = "Base price") -> Decimal | None:
        value = raw_value.strip()
        if not value:
            return None

        normalized = value.replace(",", ".")
        try:
            parsed = Decimal(normalized)
        except InvalidOperation as exc:
            raise ValueError(f"{field_label} must be a valid number.") from exc

        if not parsed.is_finite():
            raise ValueError(f"{field_label} must be a finite number.")

        return parsed

    def _supplier_input_value(self):
        if self._product_id is not None and not self._supplier_combo.isEnabled():
            return UNSET

        return self._supplier_combo.currentData()
