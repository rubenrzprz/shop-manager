from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.ui.localization import t


class DashboardPage(QWidget):
    action_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__()

        self._title_label = QLabel()
        self._title_label.setObjectName("pageTitle")

        self._shortcuts_group = QGroupBox()
        self._products_button = QPushButton()
        self._suppliers_button = QPushButton()
        self._customers_button = QPushButton()
        self._orders_button = QPushButton()
        self._settings_button = QPushButton()

        self._products_button.clicked.connect(lambda: self.action_requested.emit("new_product"))
        self._suppliers_button.clicked.connect(lambda: self.action_requested.emit("new_supplier"))
        self._customers_button.clicked.connect(lambda: self.action_requested.emit("new_customer"))
        self._orders_button.clicked.connect(lambda: self.action_requested.emit("new_order"))
        self._settings_button.clicked.connect(lambda: self.action_requested.emit("settings"))

        shortcuts_layout = QGridLayout()
        shortcuts_layout.addWidget(self._products_button, 0, 0)
        shortcuts_layout.addWidget(self._suppliers_button, 0, 1)
        shortcuts_layout.addWidget(self._customers_button, 0, 2)
        shortcuts_layout.addWidget(self._orders_button, 1, 0)
        shortcuts_layout.addWidget(self._settings_button, 1, 1)
        self._shortcuts_group.setLayout(shortcuts_layout)

        self._daily_tasks_group = QGroupBox()
        self._overdue_label = QLabel()
        self._pending_label = QLabel()
        self._completed_label = QLabel()
        self._overdue_empty_label = QLabel()
        self._pending_empty_label = QLabel()
        self._completed_empty_label = QLabel()

        tasks_layout = QVBoxLayout()
        tasks_layout.addWidget(self._overdue_label)
        tasks_layout.addWidget(self._overdue_empty_label)
        tasks_layout.addWidget(self._pending_label)
        tasks_layout.addWidget(self._pending_empty_label)
        tasks_layout.addWidget(self._completed_label)
        tasks_layout.addWidget(self._completed_empty_label)
        self._daily_tasks_group.setLayout(tasks_layout)

        layout = QVBoxLayout()
        layout.addWidget(self._title_label)
        layout.addWidget(self._shortcuts_group)
        layout.addWidget(self._daily_tasks_group)
        layout.addStretch()
        self.setLayout(layout)

        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        self._title_label.setText(t("Dashboard"))
        self._shortcuts_group.setTitle(t("Quick Actions"))
        self._products_button.setText(t("Create Product"))
        self._suppliers_button.setText(t("Create Supplier"))
        self._customers_button.setText(t("Create Customer"))
        self._orders_button.setText(t("Create Order"))
        self._settings_button.setText(t("Settings"))

        self._daily_tasks_group.setTitle(t("Daily Tasks"))
        self._overdue_label.setText(t("Overdue"))
        self._pending_label.setText(t("Pending Today"))
        self._completed_label.setText(t("Completed Today"))
        self._overdue_empty_label.setText(t("No overdue tasks."))
        self._pending_empty_label.setText(t("No pending tasks for today."))
        self._completed_empty_label.setText(t("No completed tasks for today."))
