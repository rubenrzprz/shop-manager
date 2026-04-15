from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QVBoxLayout,
)

from app.application.dto.suppliers import CreateSupplierInput, SupplierEditItem, UpdateSupplierInput
from app.application.services.suppliers import (
    CreateSupplierService,
    GetSupplierForEditService,
    UpdateSupplierService,
)
from app.infrastructure.db.session import SessionLocal


class SupplierDialog(QDialog):
    def __init__(self, parent=None, supplier_id: int | None = None) -> None:
        super().__init__(parent)

        self._supplier_id = supplier_id
        self._supplier: SupplierEditItem | None = None

        self.setWindowTitle("Edit Supplier" if supplier_id is not None else "Create Supplier")
        self.resize(520, 460)

        self._name_input = QLineEdit()
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
        form.addRow("Name", self._name_input)
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

        if self._supplier_id is not None:
            self._load_supplier()

    def _load_supplier(self) -> None:
        if self._supplier_id is None:
            return

        try:
            session = SessionLocal()
        except Exception as exc:
            QMessageBox.critical(self, "Could not load supplier", str(exc))
            self.reject()
            return

        try:
            self._supplier = GetSupplierForEditService(session).execute(self._supplier_id)
            self._populate_supplier_form(self._supplier)
        except Exception as exc:
            QMessageBox.critical(self, "Could not load supplier", str(exc))
            self.reject()
        finally:
            session.close()

    def _populate_supplier_form(self, supplier: SupplierEditItem) -> None:
        self._name_input.setText(supplier.name)
        self._tax_id_input.setText(supplier.tax_id or "")
        self._phone_input.setText(supplier.phone or "")
        self._email_input.setText(supplier.email or "")
        self._address_line_1_input.setText(supplier.address_line_1 or "")
        self._address_line_2_input.setText(supplier.address_line_2 or "")
        self._postal_code_input.setText(supplier.postal_code or "")
        self._city_input.setText(supplier.city or "")
        self._country_input.setText(supplier.country or "")
        self._notes_input.setPlainText(supplier.notes or "")
        self._is_active_checkbox.setChecked(supplier.is_active)

    def _on_accept(self) -> None:
        data = self._build_input()

        try:
            session = SessionLocal()
        except Exception as exc:
            QMessageBox.critical(self, "Could not save supplier", str(exc))
            return

        try:
            if self._supplier_id is None:
                CreateSupplierService(session).execute(data)
            else:
                UpdateSupplierService(session).execute(self._supplier_id, data)

            session.commit()
            self.accept()
        except Exception as exc:
            session.rollback()
            QMessageBox.critical(self, "Could not save supplier", str(exc))
        finally:
            session.close()

    def _build_input(self) -> CreateSupplierInput | UpdateSupplierInput:
        input_type = UpdateSupplierInput if self._supplier_id is not None else CreateSupplierInput

        return input_type(
            name=self._name_input.text().strip(),
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
