from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QCheckBox,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.application.dto.orders import (
    CreateOrderInput,
    CreateOrderLineInput,
    UpdateOrderInput,
    UpdateOrderLineInput,
)
from app.application.dto.products import ProductVariantPickerItem
from app.application.services.orders import (
    CreateOrderService,
    GetOrderForEditService,
    OrderEditCapability,
    UpdateOrderService,
)
from app.domain.enums import DiscountType
from app.infrastructure.db.session import SessionLocal
from app.ui.date_edit import AppDateEdit
from app.ui.dialog_helpers import translate_button_box
from app.ui.dialogs.customer_picker_dialog import CustomerPickerDialog
from app.ui.dialogs.product_variant_picker_dialog import ProductVariantPickerDialog
from app.ui.localization import t
from app.ui.window_sizing import resize_to_available_screen


class OrderDialog(QDialog):
    _UNSET_UNIT_PRICE = -0.01
    _MAX_MONEY_AMOUNT = Decimal("99999999.99")
    _MAX_QUANTITY = 999999

    def __init__(self, parent=None, order_id: int | None = None) -> None:
        super().__init__(parent)

        self._order_id = order_id
        self._selected_customer_id: int | None = None
        self._selected_customer_name: str | None = None
        self._selected_line_variant: ProductVariantPickerItem | None = None
        self._line_items: list[_OrderLineItem] = []
        self._edit_capability = OrderEditCapability.FULL

        self.setWindowTitle(t("Edit Order") if self._order_id is not None else t("Create Order"))
        resize_to_available_screen(
            self,
            width_ratio=0.86,
            height_ratio=0.74,
            min_width=920,
            min_height=560,
        )

        self._customer_display = QLineEdit()
        self._customer_display.setReadOnly(True)
        self._customer_display.setPlaceholderText(t("No customer selected"))
        self._select_customer_button = QPushButton(t("Select Customer"))
        self._select_customer_button.clicked.connect(self._open_customer_picker)

        customer_layout = QHBoxLayout()
        customer_layout.addWidget(self._customer_display)
        customer_layout.addWidget(self._select_customer_button)

        self._order_date_input = AppDateEdit()
        self._order_date_input.setDate(QDate.currentDate())
        self._order_date_input.dateChanged.connect(self._sync_deadline_constraints)

        self._has_deadline_checkbox = QCheckBox(t("Set deadline"))
        self._has_deadline_checkbox.toggled.connect(self._sync_deadline_constraints)
        self._deadline_input = AppDateEdit()
        self._deadline_input.setEnabled(False)

        deadline_layout = QHBoxLayout()
        deadline_layout.addWidget(self._has_deadline_checkbox)
        deadline_layout.addWidget(self._deadline_input)

        self._variant_display = QLineEdit()
        self._variant_display.setReadOnly(True)
        self._variant_display.setPlaceholderText(t("No product variant selected"))
        self._select_variant_button = QPushButton(t("Select Variant"))
        self._select_variant_button.clicked.connect(self._open_variant_picker)

        variant_layout = QHBoxLayout()
        variant_layout.addWidget(self._variant_display)
        variant_layout.addWidget(self._select_variant_button)

        self._quantity_input = QSpinBox()
        self._quantity_input.setMinimum(1)
        self._quantity_input.setMaximum(self._MAX_QUANTITY)
        self._quantity_input.setValue(1)
        self._quantity_input.valueChanged.connect(self._sync_composer_quantity_limit)

        self._unit_price_input = QDoubleSpinBox()
        self._unit_price_input.setMinimum(0)
        self._unit_price_input.setMaximum(float(self._MAX_MONEY_AMOUNT))
        self._unit_price_input.setDecimals(2)
        self._unit_price_input.setSingleStep(0.01)
        self._unit_price_input.valueChanged.connect(self._sync_composer_quantity_limit)

        self._add_line_button = QPushButton(t("Add Line"))
        self._add_line_button.clicked.connect(self._add_line_from_composer)

        composer_fields_layout = QHBoxLayout()
        composer_fields_layout.addWidget(QLabel(t("Quantity")))
        composer_fields_layout.addWidget(self._quantity_input)
        composer_fields_layout.addWidget(QLabel(t("Unit price")))
        composer_fields_layout.addWidget(self._unit_price_input)
        composer_fields_layout.addStretch()
        composer_fields_layout.addWidget(self._add_line_button)

        self._line_composer = QWidget()
        composer_layout = QVBoxLayout()
        composer_layout.setContentsMargins(0, 0, 0, 0)
        composer_layout.addLayout(variant_layout)
        composer_layout.addLayout(composer_fields_layout)
        self._line_composer.setLayout(composer_layout)

        self._lines_table = QTableWidget()
        self._lines_table.setColumnCount(7)
        self._lines_table.setHorizontalHeaderLabels(
            [t("Product"), t("Variant"), "SKU", t("Qty"), t("Unit Price"), t("Line Total"), ""]
        )
        self._lines_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._lines_table.setSelectionMode(QAbstractItemView.NoSelection)
        self._lines_table.verticalHeader().setVisible(False)
        self._lines_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self._lines_table.setAlternatingRowColors(True)
        self._lines_table.setMinimumHeight(120)

        lines_header = self._lines_table.horizontalHeader()
        lines_header.setSectionResizeMode(0, QHeaderView.Stretch)
        lines_header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        lines_header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        lines_header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        lines_header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        lines_header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        lines_header.setSectionResizeMode(6, QHeaderView.Fixed)
        self._lines_table.setColumnWidth(6, 92)

        self._discount_type_input = QComboBox()
        self._discount_type_input.addItem(t("None"), DiscountType.NONE)
        self._discount_type_input.addItem(t("Fixed"), DiscountType.FIXED)
        self._discount_type_input.addItem(t("Percentage"), DiscountType.PERCENTAGE)
        self._discount_type_input.currentIndexChanged.connect(self._sync_discount_input_state)

        self._discount_value_input = QDoubleSpinBox()
        self._discount_value_input.setMinimum(0)
        self._discount_value_input.setMaximum(99999999.99)
        self._discount_value_input.setDecimals(2)
        self._discount_value_input.valueChanged.connect(self._sync_total_preview)

        self._subtotal_value_label = QLabel("0.00")
        self._discount_amount_value_label = QLabel("0.00")
        self._total_value_label = QLabel("0.00")

        summary_layout = QFormLayout()
        summary_layout.addRow(t("Subtotal"), self._subtotal_value_label)
        summary_layout.addRow(t("Discount"), self._discount_amount_value_label)
        summary_layout.addRow(t("Total"), self._total_value_label)

        self._summary_widget = QWidget()
        self._summary_widget.setLayout(summary_layout)

        self._notes_input = QPlainTextEdit()
        self._notes_input.setFixedHeight(68)

        details_form = QFormLayout()
        details_form.addRow(t("Customer"), customer_layout)
        details_form.addRow(t("Order date"), self._order_date_input)
        details_form.addRow(t("Deadline"), deadline_layout)
        details_form.addRow(t("Notes"), self._notes_input)
        details_tab = QWidget()
        details_tab.setLayout(details_form)

        lines_layout = QVBoxLayout()
        lines_layout.addWidget(QLabel(f"<b>{t('Add line')}</b>"))
        lines_layout.addWidget(self._line_composer)
        lines_layout.addWidget(QLabel(f"<b>{t('Lines')}</b>"))
        lines_layout.addWidget(self._lines_table, 1)
        lines_tab = QWidget()
        lines_tab.setLayout(lines_layout)

        totals_form = QFormLayout()
        totals_form.addRow(t("Discount type"), self._discount_type_input)
        totals_form.addRow(t("Discount value"), self._discount_value_input)
        totals_form.addRow(QLabel(f"<b>{t('Total preview')}</b>"))
        totals_form.addRow(self._summary_widget)
        totals_tab = QWidget()
        totals_tab.setLayout(totals_form)

        self._tabs = QTabWidget()
        self._tabs.addTab(details_tab, t("Order Details"))
        self._tabs.addTab(lines_tab, t("Lines"))
        self._tabs.addTab(totals_tab, t("Totals"))

        self._buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        translate_button_box(self._buttons)
        self._buttons.accepted.connect(self._on_accept)
        self._buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(self._tabs, 1)
        layout.addWidget(self._buttons)
        self.setLayout(layout)

        self._refresh_lines_table()
        self._sync_discount_input_state()
        self._sync_deadline_constraints()

        if self._order_id is not None:
            self._load_order()

    def _open_customer_picker(self) -> None:
        if self._edit_capability != OrderEditCapability.FULL:
            return

        dialog = CustomerPickerDialog(self)
        if dialog.exec() and dialog.selected_customer is not None:
            customer = dialog.selected_customer
            self._set_customer(customer.id, customer.name)

    def _set_customer(self, customer_id: int, customer_name: str) -> None:
        self._selected_customer_id = customer_id
        self._selected_customer_name = customer_name
        self._customer_display.setText(customer_name)

    def _load_order(self) -> None:
        if self._order_id is None:
            return

        try:
            session = SessionLocal()
        except Exception as exc:
            QMessageBox.critical(self, t("Could not load order"), str(exc))
            self.reject()
            return

        try:
            order = GetOrderForEditService(session).execute(self._order_id)
            update_service = UpdateOrderService(session)
            edit_rejection_message = update_service.order_edit_rejection_message(order.status)
            if edit_rejection_message is not None:
                raise ValueError(t(edit_rejection_message))
            self._edit_capability = update_service.order_edit_capability(order.status)

            self._set_customer(order.customer_id, order.customer_name)
            self._order_date_input.setDate(
                QDate(order.order_date.year, order.order_date.month, order.order_date.day)
            )
            self._has_deadline_checkbox.setChecked(order.deadline is not None)
            if order.deadline is not None:
                self._deadline_input.setDate(
                    QDate(order.deadline.year, order.deadline.month, order.deadline.day)
                )
            self._notes_input.setPlainText(order.notes or "")
            self._line_items = [
                _OrderLineItem(
                    order_line_id=line.id,
                    product_variant_id=line.product_variant_id,
                    product_name=line.product_name,
                    sku=line.sku,
                    variant_name=line.variant_name,
                    size=line.size,
                    color=line.color,
                    quantity=line.quantity,
                    unit_price=line.unit_price,
                    notes=line.notes,
                )
                for line in order.lines
            ]
            self._refresh_lines_table()
            self._set_discount_type(order.discount_type)
            self._discount_value_input.setValue(float(order.discount_value))
            self._sync_deadline_constraints()
            self._sync_discount_input_state()
            self._sync_total_preview()
            self._apply_edit_capability()
        except Exception as exc:
            QMessageBox.critical(self, t("Could not load order"), str(exc))
            self.reject()
        finally:
            session.close()

    def _set_discount_type(self, discount_type: DiscountType) -> None:
        index = self._discount_type_input.findData(discount_type)
        if index >= 0:
            self._discount_type_input.setCurrentIndex(index)

    def _open_variant_picker(self) -> None:
        if self._edit_capability != OrderEditCapability.FULL:
            return

        dialog = ProductVariantPickerDialog(self)
        if dialog.exec() and dialog.selected_variant is not None:
            self._selected_line_variant = dialog.selected_variant
            self._variant_display.setText(
                f"{self._selected_line_variant.product_name} / {self._selected_line_variant.sku}"
            )
            self._unit_price_input.blockSignals(True)
            if self._selected_line_variant.price is not None:
                self._unit_price_input.setMinimum(0)
                self._unit_price_input.setSpecialValueText("")
                self._unit_price_input.setValue(float(self._selected_line_variant.price))
            else:
                self._unit_price_input.setMinimum(self._UNSET_UNIT_PRICE)
                self._unit_price_input.setSpecialValueText(t("Enter price"))
                self._unit_price_input.setValue(self._UNSET_UNIT_PRICE)
            self._unit_price_input.blockSignals(False)
            self._sync_composer_quantity_limit()

    def _add_line_from_composer(self) -> None:
        if self._edit_capability != OrderEditCapability.FULL:
            return

        if self._selected_line_variant is None:
            QMessageBox.information(
                self, t("Missing product variant"), t("Select a product variant.")
            )
            return

        self._line_items.append(
            _OrderLineItem(
                order_line_id=None,
                product_variant_id=self._selected_line_variant.id,
                product_name=self._selected_line_variant.product_name,
                sku=self._selected_line_variant.sku,
                variant_name=self._selected_line_variant.variant_name,
                size=self._selected_line_variant.size,
                color=self._selected_line_variant.color,
                quantity=self._quantity_input.value(),
                unit_price=self._unit_price_value(),
                notes=None,
            )
        )
        self._clear_line_composer()
        self._refresh_lines_table()
        self._sync_discount_input_state()
        self._sync_total_preview()

    def _remove_line_item(self, line_item: "_OrderLineItem") -> None:
        if self._edit_capability != OrderEditCapability.FULL:
            return

        self._line_items = [item for item in self._line_items if item is not line_item]
        self._refresh_lines_table()
        self._sync_discount_input_state()
        self._sync_total_preview()

    def _refresh_lines_table(self) -> None:
        can_edit_full_order = self._edit_capability == OrderEditCapability.FULL
        self._lines_table.clearContents()
        self._lines_table.setColumnHidden(6, not can_edit_full_order)
        self._lines_table.setRowCount(len(self._line_items))

        for row, line_item in enumerate(self._line_items):
            items = [
                QTableWidgetItem(line_item.product_name),
                QTableWidgetItem(line_item.variant_label()),
                QTableWidgetItem(line_item.sku),
                QTableWidgetItem(str(line_item.quantity)),
                QTableWidgetItem(
                    "" if line_item.unit_price is None else f"{line_item.unit_price:.2f}"
                ),
                QTableWidgetItem(f"{line_item.subtotal():.2f}"),
            ]

            for item in items:
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)

            for column, item in enumerate(items):
                self._lines_table.setItem(row, column, item)

            if can_edit_full_order:
                remove_button = QPushButton(t("Remove"))
                remove_button.setMinimumWidth(76)
                remove_button.clicked.connect(
                    lambda _checked=False, item=line_item: self._remove_line_item(item)
                )
                self._lines_table.setCellWidget(row, 6, remove_button)
            else:
                self._lines_table.setItem(row, 6, QTableWidgetItem(""))

        self._lines_table.resizeRowsToContents()

    def _clear_line_composer(self) -> None:
        self._selected_line_variant = None
        self._variant_display.clear()
        self._unit_price_input.blockSignals(True)
        self._unit_price_input.setMinimum(0)
        self._unit_price_input.setSpecialValueText("")
        self._unit_price_input.setValue(0)
        self._unit_price_input.blockSignals(False)
        self._quantity_input.setValue(1)
        self._sync_composer_quantity_limit()

    def _sync_discount_input_state(self, *_args) -> None:
        discount_type = self._discount_type_input.currentData()
        is_discounted = discount_type != DiscountType.NONE
        edit_capability = getattr(self, "_edit_capability", OrderEditCapability.FULL)
        discount_editable = edit_capability != OrderEditCapability.NOTES_ONLY
        if hasattr(self._discount_type_input, "setEnabled"):
            self._discount_type_input.setEnabled(discount_editable)
        self._discount_value_input.setEnabled(is_discounted and discount_editable)

        if not is_discounted:
            self._discount_value_input.setValue(0)
            self._sync_total_preview()
            return

        if discount_type == DiscountType.PERCENTAGE:
            self._discount_value_input.setMaximum(100)
            self._sync_total_preview()
            return

        subtotal = self._line_subtotal()
        self._discount_value_input.setMaximum(float(subtotal))
        self._sync_total_preview()

    def _sync_total_preview(self, *_args) -> None:
        preview = self._calculate_total_preview(
            subtotal=self._line_subtotal(),
            discount_type=self._discount_type_input.currentData(),
            discount_value=Decimal(str(self._discount_value_input.value())),
        )
        self._subtotal_value_label.setText(f"{preview.subtotal:.2f}")
        self._discount_amount_value_label.setText(f"{preview.discount_amount:.2f}")
        self._total_value_label.setText(f"{preview.total:.2f}")

    def _sync_deadline_constraints(self, *_args) -> None:
        order_date = self._order_date_input.date()
        self._deadline_input.setMinimumDate(order_date)
        edit_capability = getattr(self, "_edit_capability", OrderEditCapability.FULL)
        deadline_editable = edit_capability != OrderEditCapability.NOTES_ONLY
        self._has_deadline_checkbox.setEnabled(deadline_editable)
        self._deadline_input.setEnabled(
            self._has_deadline_checkbox.isChecked() and deadline_editable
        )

        if self._has_deadline_checkbox.isChecked() and self._deadline_input.date() < order_date:
            self._deadline_input.setDate(order_date)

    def _on_accept(self) -> None:
        if self._selected_customer_id is None:
            QMessageBox.information(self, t("Missing customer"), t("Select a customer."))
            return

        try:
            data = self._build_input() if self._order_id is None else self._build_update_input()
        except ValueError as exc:
            QMessageBox.information(self, t("Missing order data"), str(exc))
            return

        try:
            session = SessionLocal()
        except Exception as exc:
            QMessageBox.critical(self, t("Could not save order"), str(exc))
            return

        try:
            if self._order_id is None:
                CreateOrderService(session).execute(data)
            else:
                UpdateOrderService(session).execute(self._order_id, data)
            session.commit()
            self.accept()
        except Exception as exc:
            session.rollback()
            QMessageBox.critical(self, t("Could not save order"), str(exc))
        finally:
            session.close()

    def _apply_edit_capability(self) -> None:
        can_edit_full_order = self._edit_capability == OrderEditCapability.FULL
        can_edit_ready_fields = self._edit_capability in {
            OrderEditCapability.FULL,
            OrderEditCapability.READY_LIMITED,
        }

        self._select_customer_button.setEnabled(can_edit_full_order)
        self._order_date_input.setEnabled(can_edit_full_order)
        self._line_composer.setEnabled(can_edit_full_order)
        self._lines_table.setEnabled(True)
        self._has_deadline_checkbox.setEnabled(can_edit_ready_fields)
        self._discount_type_input.setEnabled(can_edit_ready_fields)
        self._discount_value_input.setEnabled(can_edit_ready_fields)
        self._notes_input.setEnabled(True)
        self._refresh_lines_table()
        self._sync_deadline_constraints()
        self._sync_discount_input_state()

    def _build_input(self) -> CreateOrderInput:
        if self._selected_customer_id is None:
            raise ValueError(t("Select a customer."))

        return CreateOrderInput(
            customer_id=self._selected_customer_id,
            order_date=self._to_date(self._order_date_input.date()),
            deadline=self._deadline_value(),
            discount_type=self._discount_type_input.currentData(),
            discount_value=Decimal(str(self._discount_value_input.value())),
            notes=self._notes_input.toPlainText().strip() or None,
            lines=self._build_line_inputs(),
        )

    def _build_update_input(self) -> UpdateOrderInput:
        if self._selected_customer_id is None:
            raise ValueError(t("Select a customer."))

        return UpdateOrderInput(
            customer_id=self._selected_customer_id,
            order_date=self._to_date(self._order_date_input.date()),
            deadline=self._deadline_value(),
            discount_type=self._discount_type_input.currentData(),
            discount_value=Decimal(str(self._discount_value_input.value())),
            notes=self._notes_input.toPlainText().strip() or None,
            lines=self._build_update_line_inputs(),
        )

    def _build_line_inputs(self) -> list[CreateOrderLineInput]:
        if not self._line_items:
            raise ValueError(t("Add at least one order line."))

        return [line_item.to_input() for line_item in self._line_items]

    def _build_update_line_inputs(self) -> list[UpdateOrderLineInput]:
        if not self._line_items:
            raise ValueError(t("Add at least one order line."))

        return [line_item.to_update_input() for line_item in self._line_items]

    def _deadline_value(self) -> date | None:
        if not self._has_deadline_checkbox.isChecked():
            return None

        return self._to_date(self._deadline_input.date())

    def _line_subtotal(self) -> Decimal:
        return sum(
            (line_item.subtotal() for line_item in self._line_items),
            Decimal("0.00"),
        )

    def _sync_composer_quantity_limit(self, *_args) -> None:
        self._quantity_input.setMaximum(self._quantity_max_for_unit_price(self._unit_price_value()))

    @classmethod
    def _quantity_max_for_unit_price(cls, unit_price: Decimal | None) -> int:
        if unit_price is None or unit_price == Decimal("0"):
            return cls._MAX_QUANTITY

        return max(1, min(cls._MAX_QUANTITY, int(cls._MAX_MONEY_AMOUNT // unit_price)))

    @staticmethod
    def _unit_price_value_from_input(unit_price_input) -> Decimal | None:
        if unit_price_input.value() < 0:
            return None

        return Decimal(str(unit_price_input.value()))

    def _unit_price_value(self) -> Decimal | None:
        return self._unit_price_value_from_input(self._unit_price_input)

    @staticmethod
    def _calculate_total_preview(
        *,
        subtotal: Decimal,
        discount_type: DiscountType,
        discount_value: Decimal,
    ) -> "_OrderTotalPreview":
        subtotal = OrderDialog._money(subtotal)
        discount_value = OrderDialog._money(discount_value)

        if discount_type == DiscountType.FIXED:
            discount_amount = min(discount_value, subtotal)
        elif discount_type == DiscountType.PERCENTAGE:
            discount_amount = OrderDialog._money(subtotal * (discount_value / Decimal("100")))
        else:
            discount_amount = Decimal("0.00")

        discount_amount = OrderDialog._money(min(discount_amount, subtotal))
        total = OrderDialog._money(subtotal - discount_amount)

        return _OrderTotalPreview(
            subtotal=subtotal,
            discount_amount=discount_amount,
            total=total,
        )

    @staticmethod
    def _money(value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def _to_date(value: QDate) -> date:
        return date(value.year(), value.month(), value.day())


@dataclass(frozen=True)
class _OrderLineItem:
    order_line_id: int | None
    product_variant_id: int
    product_name: str
    sku: str
    quantity: int
    unit_price: Decimal | None
    notes: str | None
    variant_name: str | None = None
    size: str | None = None
    color: str | None = None

    def to_input(self) -> CreateOrderLineInput:
        return CreateOrderLineInput(
            product_variant_id=self.product_variant_id,
            quantity=self.quantity,
            unit_price=self.unit_price,
            notes=self.notes,
        )

    def to_update_input(self) -> UpdateOrderLineInput:
        return UpdateOrderLineInput(
            order_line_id=self.order_line_id,
            product_variant_id=self.product_variant_id,
            quantity=self.quantity,
            unit_price=self.unit_price,
            notes=self.notes,
        )

    def subtotal(self) -> Decimal:
        if self.unit_price is None:
            return Decimal("0.00")

        return self.unit_price * self.quantity

    def variant_label(self) -> str:
        parts = [self.variant_name, self.size, self.color]
        return " / ".join(part for part in parts if part)


@dataclass(frozen=True)
class _OrderTotalPreview:
    subtotal: Decimal
    discount_amount: Decimal
    total: Decimal
