from PySide6.QtWidgets import QAbstractSpinBox, QDateEdit

from app.ui.localization import qt_date_format


class AppDateEdit(QDateEdit):
    """Date picker that avoids accidental spinbox stepping near the popup arrow."""

    def __init__(self) -> None:
        super().__init__()
        self.setCalendarPopup(True)
        self.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.refresh_display_format()

    def refresh_display_format(self) -> None:
        self.setDisplayFormat(qt_date_format())

    def stepBy(self, steps: int) -> None:
        return None

    def stepEnabled(self) -> QAbstractSpinBox.StepEnabledFlag:
        return QAbstractSpinBox.StepEnabledFlag.StepNone
