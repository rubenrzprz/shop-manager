APP_STYLESHEET = """
QWidget {
    font-size: 13px;
    color: #172033;
}

QMainWindow,
QTabWidget::pane {
    background: #f7f8fb;
}

QTabWidget::pane {
    border: 0;
}

QTabBar::tab {
    background: transparent;
    border: 0;
    border-bottom: 2px solid transparent;
    color: #526070;
    font-weight: 600;
    min-height: 34px;
    padding: 8px 14px;
}

QTabBar::tab:selected {
    color: #172033;
    border-bottom-color: #2563eb;
}

QTabBar::tab:hover {
    color: #172033;
    background: #eef2f7;
    border-radius: 10px;
}

QLabel#pageTitle {
    color: #111827;
    font-size: 22px;
    font-weight: 700;
    margin-bottom: 4px;
}

QLineEdit,
QPlainTextEdit,
QComboBox,
QSpinBox,
QDoubleSpinBox,
QDateEdit {
    background: #ffffff;
    border: 1px solid #d8dee8;
    border-radius: 10px;
    min-height: 32px;
    padding: 4px 9px;
}

QPlainTextEdit {
    padding: 8px 9px;
}

QLineEdit:focus,
QPlainTextEdit:focus,
QComboBox:focus,
QSpinBox:focus,
QDoubleSpinBox:focus,
QDateEdit:focus {
    border-color: #2563eb;
}

QLineEdit:disabled,
QPlainTextEdit:disabled,
QComboBox:disabled,
QSpinBox:disabled,
QDoubleSpinBox:disabled,
QDateEdit:disabled {
    background: #eef2f7;
    border-color: #d5dce7;
    color: #8793a3;
}

QLineEdit[readOnly="true"],
QPlainTextEdit[readOnly="true"] {
    background: #f3f6fa;
    color: #64748b;
}

QPushButton:disabled {
    background: #eef2f7;
    border-color: #d8dee8;
    color: #9aa6b2;
}

QCheckBox:disabled {
    color: #9aa6b2;
}

QTableWidget:disabled {
    background: #f3f6fa;
    color: #8793a3;
}

QComboBox::drop-down,
QSpinBox::up-button,
QSpinBox::down-button,
QDoubleSpinBox::up-button,
QDoubleSpinBox::down-button,
QDateEdit::drop-down,
QDateEdit::up-button,
QDateEdit::down-button {
    border: 0;
    width: 24px;
}

QPushButton {
    background: #ffffff;
    border: 1px solid #d8dee8;
    border-radius: 14px;
    color: #172033;
    font-weight: 600;
    min-height: 34px;
    padding: 5px 14px;
}

QPushButton:hover {
    background: #f1f5f9;
    border-color: #c7d0dd;
}

QPushButton:pressed {
    background: #e7edf5;
}

QPushButton#primaryButton {
    background: #2563eb;
    border-color: #2563eb;
    color: #ffffff;
}

QPushButton#primaryButton:hover {
    background: #1d4ed8;
    border-color: #1d4ed8;
}

QPushButton#dangerButton {
    color: #b42318;
}

QFrame#selectionActionPanel {
    background: #ffffff;
    border: 1px solid #e1e7ef;
    border-radius: 16px;
}

QLabel#selectionActionTitle {
    color: #111827;
    font-size: 15px;
    font-weight: 700;
}

QLabel#selectionActionHint {
    color: #64748b;
}

QTableWidget {
    alternate-background-color: #f8fafc;
    background: #ffffff;
    border: 1px solid #e1e7ef;
    border-radius: 14px;
    gridline-color: transparent;
    selection-background-color: #dbeafe;
    selection-color: #111827;
}

QTableWidget::item {
    border: 0;
    padding: 7px 8px;
}

QHeaderView::section {
    background-color: #f3f6fa;
    border: 0;
    border-bottom: 1px solid #d8dee8;
    color: #526070;
    font-weight: 700;
    padding: 8px 9px;
}

QGroupBox {
    border: 0;
    color: #111827;
    font-weight: 700;
    margin-top: 14px;
    padding-top: 12px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 0;
}

QCheckBox {
    min-height: 28px;
}
"""
