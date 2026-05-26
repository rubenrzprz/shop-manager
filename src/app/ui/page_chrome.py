from PySide6.QtWidgets import (
    QAbstractItemView,
    QBoxLayout,
    QFrame,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QVBoxLayout,
)


def apply_page_chrome(layout: QBoxLayout) -> None:
    layout.setContentsMargins(24, 20, 24, 24)
    layout.setSpacing(14)
    parent = layout.parentWidget()
    if parent is not None:
        parent.setAutoFillBackground(True)
        parent.setStyleSheet("background: #eef2f7;")


def apply_toolbar_chrome(layout: QBoxLayout) -> None:
    layout.setSpacing(8)


def configure_table_chrome(table: QTableWidget) -> None:
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setSelectionMode(QAbstractItemView.SingleSelection)
    table.setAlternatingRowColors(True)
    table.setShowGrid(False)
    table.verticalHeader().setVisible(False)
    table.verticalHeader().setDefaultSectionSize(38)


def mark_primary_button(button: QPushButton) -> None:
    button.setObjectName("primaryButton")


def mark_danger_button(button: QPushButton) -> None:
    button.setObjectName("dangerButton")


def build_selection_action_panel(
    title_label: QLabel,
    hint_label: QLabel,
    buttons: list[QPushButton],
) -> QFrame:
    panel = QFrame()
    panel.setObjectName("selectionActionPanel")
    panel.setMinimumWidth(190)
    panel.setMaximumWidth(240)
    panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

    title_label.setObjectName("selectionActionTitle")
    hint_label.setObjectName("selectionActionHint")
    hint_label.setWordWrap(True)

    layout = QVBoxLayout()
    layout.setContentsMargins(14, 14, 14, 14)
    layout.setSpacing(8)
    layout.addWidget(title_label)
    layout.addWidget(hint_label)
    layout.addSpacing(6)
    for button in buttons:
        layout.addWidget(button)
    layout.addStretch()
    panel.setLayout(layout)
    return panel


def set_selection_actions_enabled(buttons: list[QPushButton], enabled: bool) -> None:
    for button in buttons:
        button.setEnabled(enabled)
