from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.application.services.products import ListProductsService
from app.infrastructure.db.session import SessionLocal
from app.ui.dialogs.product_dialog import ProductDialog


class ProductsPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self._title_label = QLabel("Products")
        self._title_label.setObjectName("pageTitle")

        self._create_button = QPushButton("New Product")
        self._create_button.clicked.connect(self.open_create_dialog)

        self._refresh_button = QPushButton("Refresh")
        self._refresh_button.clicked.connect(self.load_products)

        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels(
            ["ID", "Name", "Base Price", "Track Stock", "Active", "Variants"]
        )
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)

        layout = QVBoxLayout()
        layout.addWidget(self._title_label)

        actions_layout = QHBoxLayout()
        actions_layout.addWidget(self._create_button)
        actions_layout.addWidget(self._refresh_button)
        actions_layout.addStretch()

        layout.addLayout(actions_layout)
        layout.addWidget(self._table)

        self.setLayout(layout)

        self.load_products()

    def open_create_dialog(self) -> None:
        dialog = ProductDialog(self)
        if dialog.exec():
            self.load_products()

    def load_products(self) -> None:
        session = SessionLocal()

        try:
            service = ListProductsService(session)
            products = service.execute()
            self._populate_table(products)
        finally:
            session.close()

    def _populate_table(self, products) -> None:
        self._table.setRowCount(len(products))

        for row, product in enumerate(products):
            base_price_text = "" if product.base_price is None else str(product.base_price)
            track_stock_text = "Yes" if product.track_stock else "No"
            is_active_text = "Yes" if product.is_active else "No"
            variants_count_text = str(len(product.variants))

            items = [
                QTableWidgetItem(str(product.id)),
                QTableWidgetItem(product.name),
                QTableWidgetItem(base_price_text),
                QTableWidgetItem(track_stock_text),
                QTableWidgetItem(is_active_text),
                QTableWidgetItem(variants_count_text),
            ]

            for item in items:
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)

            for column, item in enumerate(items):
                self._table.setItem(row, column, item)