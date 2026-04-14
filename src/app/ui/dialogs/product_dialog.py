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

from app.application.dto.products import CreateProductInput, CreateProductVariantInput
from app.application.services.products import CreateProductService
from app.infrastructure.db.models import Supplier
from app.infrastructure.db.session import SessionLocal


class ProductDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Create Product")
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
        self._variant_description_input = QPlainTextEdit()
        self._variant_description_input.setFixedHeight(70)

        form = QFormLayout()
        form.addRow("Name", self._name_input)
        form.addRow("Supplier", self._supplier_combo)
        form.addRow("Description", self._description_input)
        form.addRow("Base price", self._base_price_input)
        form.addRow("", self._track_stock_checkbox)
        form.addRow("Default variant name", self._variant_name_input)
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

    def _load_suppliers(self) -> None:
        try:
            session = SessionLocal()
        except Exception as exc:
            QMessageBox.critical(self, "Could not load suppliers", str(exc))
            self._supplier_combo.setEnabled(False)
            return

        try:
            suppliers = session.query(Supplier).order_by(Supplier.name).all()
            for supplier in suppliers:
                self._supplier_combo.addItem(supplier.name, supplier.id)
        except Exception as exc:
            QMessageBox.critical(self, "Could not load suppliers", str(exc))
            self._supplier_combo.setEnabled(False)
        finally:
            session.close()

    def _on_accept(self) -> None:
        name = self._name_input.text().strip()
        supplier_id = self._supplier_combo.currentData()
        description = self._description_input.toPlainText().strip() or None
        track_stock = self._track_stock_checkbox.isChecked()
        variant_name = self._variant_name_input.text().strip() or "Default"
        variant_description = self._variant_description_input.toPlainText().strip() or None

        try:
            base_price = self._parse_decimal(self._base_price_input.text())
        except ValueError as exc:
            QMessageBox.critical(self, "Invalid data", str(exc))
            return

        try:
            session = SessionLocal()
        except Exception as exc:
            QMessageBox.critical(self, "Could not create product", str(exc))
            return

        try:
            service = CreateProductService(session)

            data = CreateProductInput(
                name=name,
                supplier_id=supplier_id,
                description=description,
                base_price=base_price,
                track_stock=track_stock,
                variants=[
                    CreateProductVariantInput(
                        variant_name=variant_name,
                        description=variant_description,
                    )
                ],
            )

            service.execute(data)
            session.commit()
            self.accept()

        except Exception as exc:
            session.rollback()
            QMessageBox.critical(self, "Could not create product", str(exc))
        finally:
            session.close()

    @staticmethod
    def _parse_decimal(raw_value: str) -> Decimal | None:
        value = raw_value.strip()
        if not value:
            return None

        normalized = value.replace(",", ".")
        try:
            parsed = Decimal(normalized)
        except InvalidOperation as exc:
            raise ValueError("Base price must be a valid number.") from exc

        return parsed
