from datetime import date
from decimal import Decimal

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QCheckBox,
    QSpinBox,
    QVBoxLayout,
)

from app.application.dto.customers import CustomerPickerItem
from app.application.dto.orders import CreateOrderInput, CreateOrderLineInput
from app.application.dto.products import ProductVariantPickerItem
from app.application.services.orders import CreateOrderService
from app.domain.enums import DiscountType
from app.infrastructure.db.session import SessionLocal
from app.ui.dialogs.customer_picker_dialog import CustomerPickerDialog
from app.ui.dialogs.product_variant_picker_dialog import ProductVariantPickerDialog


class OrderDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._selected_customer: CustomerPickerItem | None = None
        self._selected_variant: ProductVariantPickerItem | None = None

        self.setWindowTitle("Create Order")
        self.resize(620, 460)

        self._customer_display = QLineEdit()
        self._customer_display.setReadOnly(True)
        self._customer_display.setPlaceholderText("No customer selected")
        self._select_customer_button = QPushButton("Select Customer")
        self._select_customer_button.clicked.connect(self._open_customer_picker)

        customer_layout = QHBoxLayout()
        customer_layout.addWidget(self._customer_display)
        customer_layout.addWidget(self._select_customer_button)

        self._order_date_input = QDateEdit()
        self._order_date_input.setCalendarPopup(True)
        self._order_date_input.setDate(QDate.currentDate())
        self._order_date_input.dateChanged.connect(self._sync_deadline_constraints)

        self._has_deadline_checkbox = QCheckBox("Set deadline")
        self._has_deadline_checkbox.toggled.connect(self._sync_deadline_constraints)
        self._deadline_input = QDateEdit()
        self._deadline_input.setCalendarPopup(True)
        self._deadline_input.setEnabled(False)

        deadline_layout = QHBoxLayout()
        deadline_layout.addWidget(self._has_deadline_checkbox)
        deadline_layout.addWidget(self._deadline_input)

        self._variant_display = QLineEdit()
        self._variant_display.setReadOnly(True)
        self._variant_display.setPlaceholderText("No product variant selected")
        self._select_variant_button = QPushButton("Select Variant")
        self._select_variant_button.clicked.connect(self._open_variant_picker)

        variant_layout = QHBoxLayout()
        variant_layout.addWidget(self._variant_display)
        variant_layout.addWidget(self._select_variant_button)

        self._quantity_input = QSpinBox()
        self._quantity_input.setMinimum(1)
        self._quantity_input.setMaximum(999999)
        self._quantity_input.setValue(1)

        self._unit_price_input = QDoubleSpinBox()
        self._unit_price_input.setMinimum(0)
        self._unit_price_input.setMaximum(999999.99)
        self._unit_price_input.setDecimals(2)
        self._unit_price_input.setPrefix("")
        self._unit_price_input.valueChanged.connect(self._sync_discount_input_state)
        self._quantity_input.valueChanged.connect(self._sync_discount_input_state)

        self._discount_type_input = QComboBox()
        self._discount_type_input.addItem("None", DiscountType.NONE)
        self._discount_type_input.addItem("Fixed", DiscountType.FIXED)
        self._discount_type_input.addItem("Percentage", DiscountType.PERCENTAGE)
        self._discount_type_input.currentIndexChanged.connect(self._sync_discount_input_state)

        self._discount_value_input = QDoubleSpinBox()
        self._discount_value_input.setMinimum(0)
        self._discount_value_input.setMaximum(999999.99)
        self._discount_value_input.setDecimals(2)

        self._notes_input = QPlainTextEdit()
        self._notes_input.setFixedHeight(90)

        form = QFormLayout()
        form.addRow("Customer", customer_layout)
        form.addRow("Order date", self._order_date_input)
        form.addRow("Deadline", deadline_layout)
        form.addRow(QLabel("<b>Line</b>"))
        form.addRow("Product variant", variant_layout)
        form.addRow("Quantity", self._quantity_input)
        form.addRow("Unit price", self._unit_price_input)
        form.addRow("Discount type", self._discount_type_input)
        form.addRow("Discount value", self._discount_value_input)
        form.addRow("Notes", self._notes_input)

        self._buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self._buttons.accepted.connect(self._on_accept)
        self._buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(self._buttons)
        self.setLayout(layout)

        self._sync_discount_input_state()
        self._sync_deadline_constraints()

    def _open_customer_picker(self) -> None:
        dialog = CustomerPickerDialog(self)
        if dialog.exec() and dialog.selected_customer is not None:
            self._selected_customer = dialog.selected_customer
            self._customer_display.setText(self._selected_customer.name)

    def _open_variant_picker(self) -> None:
        dialog = ProductVariantPickerDialog(self)
        if dialog.exec() and dialog.selected_variant is not None:
            self._selected_variant = dialog.selected_variant
            self._variant_display.setText(
                f"{self._selected_variant.product_name} / {self._selected_variant.sku}"
            )
            self._unit_price_input.setValue(float(self._selected_variant.price))

    def _sync_discount_input_state(self) -> None:
        discount_type = self._discount_type_input.currentData()
        is_discounted = discount_type != DiscountType.NONE
        self._discount_value_input.setEnabled(is_discounted)

        if not is_discounted:
            self._discount_value_input.setValue(0)
            return

        if discount_type == DiscountType.PERCENTAGE:
            self._discount_value_input.setMaximum(100)
            return

        subtotal = self._line_subtotal()
        self._discount_value_input.setMaximum(float(subtotal))

    def _sync_deadline_constraints(self) -> None:
        order_date = self._order_date_input.date()
        self._deadline_input.setMinimumDate(order_date)
        self._deadline_input.setEnabled(self._has_deadline_checkbox.isChecked())

        if self._has_deadline_checkbox.isChecked() and self._deadline_input.date() < order_date:
            self._deadline_input.setDate(order_date)

    def _on_accept(self) -> None:
        if self._selected_customer is None:
            QMessageBox.information(self, "Missing customer", "Select a customer.")
            return

        if self._selected_variant is None:
            QMessageBox.information(self, "Missing product variant", "Select a product variant.")
            return

        data = self._build_input()

        try:
            session = SessionLocal()
        except Exception as exc:
            QMessageBox.critical(self, "Could not save order", str(exc))
            return

        try:
            CreateOrderService(session).execute(data)
            session.commit()
            self.accept()
        except Exception as exc:
            session.rollback()
            QMessageBox.critical(self, "Could not save order", str(exc))
        finally:
            session.close()

    def _build_input(self) -> CreateOrderInput:
        if self._selected_customer is None or self._selected_variant is None:
            raise ValueError("Customer and product variant are required.")

        return CreateOrderInput(
            customer_id=self._selected_customer.id,
            order_date=self._to_date(self._order_date_input.date()),
            deadline=self._deadline_value(),
            discount_type=self._discount_type_input.currentData(),
            discount_value=Decimal(str(self._discount_value_input.value())),
            notes=self._notes_input.toPlainText().strip() or None,
            lines=[
                CreateOrderLineInput(
                    product_variant_id=self._selected_variant.id,
                    quantity=self._quantity_input.value(),
                    unit_price=Decimal(str(self._unit_price_input.value())),
                )
            ],
        )

    def _deadline_value(self) -> date | None:
        if not self._has_deadline_checkbox.isChecked():
            return None

        return self._to_date(self._deadline_input.date())

    def _line_subtotal(self) -> Decimal:
        return Decimal(str(self._unit_price_input.value())) * self._quantity_input.value()

    @staticmethod
    def _to_date(value: QDate) -> date:
        return date(value.year(), value.month(), value.day())
