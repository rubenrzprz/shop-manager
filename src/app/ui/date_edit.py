from PySide6.QtWidgets import QAbstractSpinBox, QDateEdit


class AppDateEdit(QDateEdit):
    """Date picker that avoids accidental spinbox stepping near the popup arrow."""

    def __init__(self) -> None:
        super().__init__()
        self.setCalendarPopup(True)

    def stepBy(self, steps: int) -> None:
        return None

    def stepEnabled(self) -> QAbstractSpinBox.StepEnabledFlag:
        return QAbstractSpinBox.StepEnabledFlag.StepNone
