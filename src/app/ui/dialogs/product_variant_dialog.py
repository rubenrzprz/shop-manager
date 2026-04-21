from decimal import Decimal, InvalidOperation

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.application.dto.products import (
    CreateProductVariantInput,
    ProductVariantEditItem,
    UpdateProductVariantInput,
)
from app.ui.dialog_helpers import translate_button_box
from app.ui.localization import t


class ProductVariantDialog(QDialog):
    def __init__(
        self,
        parent=None,
        variant: ProductVariantEditItem | None = None,
        create_variant: CreateProductVariantInput | None = None,
    ) -> None:
        super().__init__(parent)

        self._variant = variant
        self._create_variant = create_variant
        self._variant_input: CreateProductVariantInput | UpdateProductVariantInput | None = None

        self.setWindowTitle(
            t("Edit Variant")
            if variant is not None or create_variant is not None
            else t("Add Variant")
        )
        self.resize(420, 360)

        self._variant_name_input = QLineEdit()
        self._size_input = QLineEdit()
        self._color_input = QLineEdit()
        self._price_override_input = QLineEdit()
        self._stock_current_input = QLineEdit()
        self._stock_minimum_input = QLineEdit()
        self._is_active_checkbox = QCheckBox(t("Active"))
        self._description_input = QPlainTextEdit()
        self._description_input.setFixedHeight(70)
        self._manual_sku_checkbox = QCheckBox(t("Manual SKU"))
        self._manual_sku_checkbox.toggled.connect(self._sync_sku_input_state)
        self._sku_input = QLineEdit()

        form = QFormLayout()
        form.addRow(t("Variant"), self._variant_name_input)
        form.addRow(t("Size"), self._size_input)
        form.addRow(t("Color"), self._color_input)
        form.addRow(t("Price override"), self._price_override_input)
        form.addRow(t("Current stock"), self._stock_current_input)
        form.addRow(t("Minimum stock"), self._stock_minimum_input)
        if variant is None:
            form.addRow("", self._is_active_checkbox)
        form.addRow(t("Description"), self._description_input)
        sku_widget = QWidget()
        sku_layout = QHBoxLayout()
        sku_layout.setContentsMargins(0, 0, 0, 0)
        sku_layout.addWidget(self._manual_sku_checkbox)
        sku_layout.addWidget(self._sku_input, 1)
        sku_widget.setLayout(sku_layout)
        form.addRow("", sku_widget)

        self._buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        translate_button_box(self._buttons)
        self._buttons.accepted.connect(self._on_accept)
        self._buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(self._buttons)
        self.setLayout(layout)

        if variant is not None:
            self._populate_variant(variant)
        elif create_variant is not None:
            self._populate_create_variant(create_variant)
        else:
            self._is_active_checkbox.setChecked(True)
            self._sync_sku_input_state()

    @property
    def variant_input(self) -> CreateProductVariantInput | UpdateProductVariantInput | None:
        return self._variant_input

    def _populate_variant(self, variant: ProductVariantEditItem) -> None:
        self._sku_input.setText(variant.sku)
        self._sku_input.setReadOnly(True)
        self._manual_sku_checkbox.setChecked(True)
        self._manual_sku_checkbox.setEnabled(False)
        self._variant_name_input.setText(variant.variant_name or "")
        self._size_input.setText(variant.size or "")
        self._color_input.setText(variant.color or "")
        self._price_override_input.setText(
            "" if variant.price_override is None else str(variant.price_override)
        )
        self._stock_current_input.setText(
            "" if variant.stock_current is None else str(variant.stock_current)
        )
        self._stock_minimum_input.setText(
            "" if variant.stock_minimum is None else str(variant.stock_minimum)
        )
        self._is_active_checkbox.setChecked(variant.is_active)
        self._description_input.setPlainText(variant.description or "")

    def _populate_create_variant(self, variant: CreateProductVariantInput) -> None:
        self._sku_input.setText(variant.sku or "")
        self._manual_sku_checkbox.setChecked(variant.sku is not None)
        self._variant_name_input.setText(variant.variant_name or "")
        self._size_input.setText(variant.size or "")
        self._color_input.setText(variant.color or "")
        self._price_override_input.setText(
            "" if variant.price_override is None else str(variant.price_override)
        )
        self._stock_current_input.setText(
            "" if variant.stock_current is None else str(variant.stock_current)
        )
        self._stock_minimum_input.setText(
            "" if variant.stock_minimum is None else str(variant.stock_minimum)
        )
        self._is_active_checkbox.setChecked(variant.is_active)
        self._description_input.setPlainText(variant.description or "")
        self._sync_sku_input_state()

    def _on_accept(self) -> None:
        try:
            price_override = self._parse_decimal(
                self._price_override_input.text(),
                t("Price override"),
            )
            stock_current = self._parse_int(self._stock_current_input.text(), t("Current stock"))
            stock_minimum = self._parse_int(self._stock_minimum_input.text(), t("Minimum stock"))
        except ValueError as exc:
            QMessageBox.critical(self, t("Invalid data"), str(exc))
            return

        variant_name = self._variant_name_input.text().strip() or None
        size = self._size_input.text().strip() or None
        color = self._color_input.text().strip() or None
        description = self._description_input.toPlainText().strip() or None

        if self._variant is None:
            self._variant_input = CreateProductVariantInput(
                sku=(
                    self._sku_input.text().strip() or None
                    if self._manual_sku_checkbox.isChecked()
                    else None
                ),
                variant_name=variant_name,
                size=size,
                color=color,
                description=description,
                price_override=price_override,
                stock_current=stock_current,
                stock_minimum=stock_minimum,
                is_active=self._is_active_checkbox.isChecked(),
            )
        else:
            self._variant_input = UpdateProductVariantInput(
                variant_id=self._variant.id,
                variant_name=variant_name,
                size=size,
                color=color,
                description=description,
                price_override=price_override,
                stock_current=stock_current,
                stock_minimum=stock_minimum,
            )

        self.accept()

    def _sync_sku_input_state(self) -> None:
        manual_sku = self._manual_sku_checkbox.isChecked()
        self._sku_input.setEnabled(manual_sku)
        if not manual_sku:
            self._sku_input.clear()

    @staticmethod
    def _parse_decimal(raw_value: str, field_label: str) -> Decimal | None:
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

    @staticmethod
    def _parse_int(raw_value: str, field_label: str) -> int | None:
        value = raw_value.strip()
        if not value:
            return None

        try:
            return int(value)
        except ValueError as exc:
            raise ValueError(
                t("{field_label} must be a valid number.").format(field_label=field_label)
            ) from exc
