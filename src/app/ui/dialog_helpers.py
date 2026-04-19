from PySide6.QtWidgets import QDialogButtonBox, QMessageBox, QWidget

from app.ui.localization import t


def translate_button_box(button_box: QDialogButtonBox) -> None:
    labels = {
        QDialogButtonBox.Save: "Save",
        QDialogButtonBox.Cancel: "Cancel",
        QDialogButtonBox.Ok: "OK",
    }

    for standard_button, label in labels.items():
        button = button_box.button(standard_button)
        if button is not None:
            button.setText(t(label))


def question(
    parent: QWidget,
    title: str,
    text: str,
    *,
    default_button: QMessageBox.StandardButton = QMessageBox.No,
) -> QMessageBox.StandardButton:
    message_box = QMessageBox(parent)
    message_box.setIcon(QMessageBox.Question)
    message_box.setWindowTitle(title)
    message_box.setText(text)
    message_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    message_box.setDefaultButton(default_button)
    _translate_message_box_buttons(message_box)

    return QMessageBox.StandardButton(message_box.exec())


def _translate_message_box_buttons(message_box: QMessageBox) -> None:
    labels = {
        QMessageBox.Yes: "Yes",
        QMessageBox.No: "No",
        QMessageBox.Ok: "OK",
        QMessageBox.Cancel: "Cancel",
    }

    for standard_button, label in labels.items():
        button = message_box.button(standard_button)
        if button is not None:
            button.setText(t(label))
