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

from app.application.dto.customers import CreateCustomerInput, CustomerEditItem, UpdateCustomerInput
from app.application.services.customers import (
    CreateCustomerService,
    GetCustomerForEditService,
    UpdateCustomerService,
)
from app.domain.enums import CustomerType
from app.infrastructure.db.session import SessionLocal


class CustomerDialog(QDialog):
    def __init__(self, parent=None, customer_id: int | None = None) -> None:
        super().__init__(parent)

        self._customer_id = customer_id
        self._customer: CustomerEditItem | None = None

        self.setWindowTitle("Edit Customer" if customer_id is not None else "Create Customer")
        self.resize(520, 500)

        self._customer_type_input = QComboBox()
        self._customer_type_input.addItem("Individual", CustomerType.INDIVIDUAL)
        self._customer_type_input.addItem("Company", CustomerType.COMPANY)
        self._name_input = QLineEdit()
        self._company_name_input = QLineEdit()
        self._tax_id_input = QLineEdit()
        self._phone_input = QLineEdit()
        self._email_input = QLineEdit()
        self._address_line_1_input = QLineEdit()
        self._address_line_2_input = QLineEdit()
        self._postal_code_input = QLineEdit()
        self._city_input = QLineEdit()
        self._country_input = QLineEdit()
        self._notes_input = QPlainTextEdit()
        self._notes_input.setFixedHeight(90)
        self._is_active_checkbox = QCheckBox("Active")
        self._is_active_checkbox.setChecked(True)

        form = QFormLayout()
        form.addRow("Type", self._customer_type_input)
        form.addRow("Name", self._name_input)
        form.addRow("Company name", self._company_name_input)
        form.addRow("Tax ID", self._tax_id_input)
        form.addRow("Phone", self._phone_input)
        form.addRow("Email", self._email_input)
        form.addRow("Address line 1", self._address_line_1_input)
        form.addRow("Address line 2", self._address_line_2_input)
        form.addRow("Postal code", self._postal_code_input)
        form.addRow("City", self._city_input)
        form.addRow("Country", self._country_input)
        form.addRow("Notes", self._notes_input)
        form.addRow("", self._is_active_checkbox)

        self._buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self._buttons.accepted.connect(self._on_accept)
        self._buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(self._buttons)
        self.setLayout(layout)

        if self._customer_id is not None:
            self._load_customer()

    def _load_customer(self) -> None:
        if self._customer_id is None:
            return

        try:
            session = SessionLocal()
        except Exception as exc:
            QMessageBox.critical(self, "Could not load customer", str(exc))
            self.reject()
            return

        try:
            self._customer = GetCustomerForEditService(session).execute(self._customer_id)
            self._populate_customer_form(self._customer)
        except Exception as exc:
            QMessageBox.critical(self, "Could not load customer", str(exc))
            self.reject()
        finally:
            session.close()

    def _populate_customer_form(self, customer: CustomerEditItem) -> None:
        self._select_customer_type(customer.customer_type)
        self._name_input.setText(customer.name)
        self._company_name_input.setText(customer.company_name or "")
        self._tax_id_input.setText(customer.tax_id or "")
        self._phone_input.setText(customer.phone or "")
        self._email_input.setText(customer.email or "")
        self._address_line_1_input.setText(customer.address_line_1 or "")
        self._address_line_2_input.setText(customer.address_line_2 or "")
        self._postal_code_input.setText(customer.postal_code or "")
        self._city_input.setText(customer.city or "")
        self._country_input.setText(customer.country or "")
        self._notes_input.setPlainText(customer.notes or "")
        self._is_active_checkbox.setChecked(customer.is_active)

    def _select_customer_type(self, customer_type: CustomerType) -> None:
        for index in range(self._customer_type_input.count()):
            if self._customer_type_input.itemData(index) == customer_type:
                self._customer_type_input.setCurrentIndex(index)
                return

    def _on_accept(self) -> None:
        data = self._build_input()

        try:
            session = SessionLocal()
        except Exception as exc:
            QMessageBox.critical(self, "Could not save customer", str(exc))
            return

        try:
            if self._customer_id is None:
                CreateCustomerService(session).execute(data)
            else:
                UpdateCustomerService(session).execute(self._customer_id, data)

            session.commit()
            self.accept()
        except Exception as exc:
            session.rollback()
            QMessageBox.critical(self, "Could not save customer", str(exc))
        finally:
            session.close()

    def _build_input(self) -> CreateCustomerInput | UpdateCustomerInput:
        input_type = UpdateCustomerInput if self._customer_id is not None else CreateCustomerInput

        return input_type(
            customer_type=self._customer_type_input.currentData(),
            name=self._name_input.text().strip(),
            company_name=self._optional_line_value(self._company_name_input),
            tax_id=self._optional_line_value(self._tax_id_input),
            phone=self._optional_line_value(self._phone_input),
            email=self._optional_line_value(self._email_input),
            address_line_1=self._optional_line_value(self._address_line_1_input),
            address_line_2=self._optional_line_value(self._address_line_2_input),
            postal_code=self._optional_line_value(self._postal_code_input),
            city=self._optional_line_value(self._city_input),
            country=self._optional_line_value(self._country_input),
            notes=self._notes_input.toPlainText().strip() or None,
            is_active=self._is_active_checkbox.isChecked(),
        )

    @staticmethod
    def _optional_line_value(input_widget: QLineEdit) -> str | None:
        return input_widget.text().strip() or None
