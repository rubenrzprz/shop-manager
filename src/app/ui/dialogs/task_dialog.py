from datetime import date

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QVBoxLayout,
)

from app.application.dto.tasks import CreateTaskInput
from app.application.services.tasks import CreateTaskService
from app.infrastructure.db.session import SessionLocal
from app.ui.dialog_helpers import translate_button_box
from app.ui.localization import t


class TaskDialog(QDialog):
    def __init__(
        self,
        parent=None,
        default_due_date: date | None = None,
        default_order_id: int | None = None,
        default_order_label: str | None = None,
    ) -> None:
        super().__init__(parent)

        self._order_id = default_order_id
        self.setWindowTitle(t("Create Order Reminder") if self._order_id else t("Create Task"))
        self.resize(420, 280)

        self._title_input = QLineEdit()
        self._due_date_input = QDateEdit()
        self._due_date_input.setCalendarPopup(True)
        due_date = default_due_date or date.today()
        self._due_date_input.setDate(QDate(due_date.year, due_date.month, due_date.day))
        self._notes_input = QPlainTextEdit()
        self._notes_input.setFixedHeight(100)

        form = QFormLayout()
        if self._order_id is not None:
            order_label = QLabel(default_order_label or str(self._order_id))
            order_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            order_label.setMinimumHeight(self._title_input.sizeHint().height())
            form.addRow(t("Order"), order_label)
        form.addRow(t("Title"), self._title_input)
        form.addRow(t("Due date"), self._due_date_input)
        form.addRow(t("Notes"), self._notes_input)

        self._buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        translate_button_box(self._buttons)
        self._buttons.accepted.connect(self._on_accept)
        self._buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(self._buttons)
        self.setLayout(layout)

    def _on_accept(self) -> None:
        data = CreateTaskInput(
            title=self._title_input.text(),
            due_date=self._due_date_input.date().toPython(),
            notes=self._notes_input.toPlainText().strip() or None,
            order_id=self._order_id,
        )

        try:
            session = SessionLocal()
        except Exception as exc:
            QMessageBox.critical(self, t("Could not create task"), str(exc))
            return

        try:
            CreateTaskService(session).execute(data)
            session.commit()
            self.accept()
        except Exception as exc:
            session.rollback()
            QMessageBox.critical(self, t("Could not create task"), t(str(exc)))
        finally:
            session.close()
