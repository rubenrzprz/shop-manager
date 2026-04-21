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

from app.application.dto.product_categories import (
    CreateProductCategoryInput,
    ProductCategoryEditItem,
    UpdateProductCategoryInput,
)
from app.application.services.product_categories import (
    CreateProductCategoryService,
    GetProductCategoryForEditService,
    UpdateProductCategoryService,
)
from app.infrastructure.db.session import SessionLocal
from app.ui.dialog_helpers import translate_button_box
from app.ui.localization import t


class ProductCategoryDialog(QDialog):
    def __init__(self, parent=None, category_id: int | None = None) -> None:
        super().__init__(parent)

        self._category_id = category_id
        self._category: ProductCategoryEditItem | None = None

        self.setWindowTitle(
            t("Edit Category") if category_id is not None else t("Create Category")
        )
        self.resize(460, 300)

        self._name_input = QLineEdit()
        self._description_input = QPlainTextEdit()
        self._description_input.setFixedHeight(100)
        self._is_active_checkbox = QCheckBox(t("Active"))
        self._is_active_checkbox.setChecked(True)

        form = QFormLayout()
        form.addRow(t("Name"), self._name_input)
        form.addRow(t("Description"), self._description_input)
        form.addRow("", self._is_active_checkbox)

        self._buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        translate_button_box(self._buttons)
        self._buttons.accepted.connect(self._on_accept)
        self._buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(self._buttons)
        self.setLayout(layout)

        if self._category_id is not None:
            self._load_category()

    def _load_category(self) -> None:
        if self._category_id is None:
            return

        try:
            session = SessionLocal()
        except Exception as exc:
            QMessageBox.critical(self, t("Could not load category"), str(exc))
            self.reject()
            return

        try:
            self._category = GetProductCategoryForEditService(session).execute(
                self._category_id
            )
            self._populate_category_form(self._category)
        except Exception as exc:
            QMessageBox.critical(self, t("Could not load category"), t(str(exc)))
            self.reject()
        finally:
            session.close()

    def _populate_category_form(self, category: ProductCategoryEditItem) -> None:
        self._name_input.setText(category.name)
        self._description_input.setPlainText(category.description or "")
        self._is_active_checkbox.setChecked(category.is_active)

    def _on_accept(self) -> None:
        data = self._build_input()

        try:
            session = SessionLocal()
        except Exception as exc:
            QMessageBox.critical(self, t("Could not save category"), str(exc))
            return

        try:
            if self._category_id is None:
                CreateProductCategoryService(session).execute(data)
            else:
                UpdateProductCategoryService(session).execute(self._category_id, data)

            session.commit()
            self.accept()
        except Exception as exc:
            session.rollback()
            QMessageBox.critical(self, t("Could not save category"), t(str(exc)))
        finally:
            session.close()

    def _build_input(self) -> CreateProductCategoryInput | UpdateProductCategoryInput:
        input_type = (
            UpdateProductCategoryInput
            if self._category_id is not None
            else CreateProductCategoryInput
        )

        return input_type(
            name=self._name_input.text().strip(),
            description=self._description_input.toPlainText().strip() or None,
            is_active=self._is_active_checkbox.isChecked(),
        )
