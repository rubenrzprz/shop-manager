from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.application.dto.products import ProductListItem
from app.application.services.products import ListProductsService
from app.infrastructure.db.models import Product
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
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels(
            ["ID", "Name", "Supplier", "Base Price", "Track Stock", "Active", "Variant Summary"]
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
        header.setSectionResizeMode(6, QHeaderView.Stretch)

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
        try:
            session = SessionLocal()
        except Exception as exc:
            self._handle_load_products_error(exc)
            return

        try:
            service = ListProductsService(session)
            products = service.execute()
            self._populate_table(products)
        except Exception as exc:
            self._handle_load_products_error(exc)
        finally:
            session.close()

    def _handle_load_products_error(self, exc: Exception) -> None:
        self._table.setRowCount(0)
        QMessageBox.critical(
            self,
            "Could not load products",
            str(exc),
        )

    def _build_variant_summary(self, product: ProductListItem) -> str:
        if not product.variants:
            return "No variants"

        summaries: list[str] = []

        for variant in product.variants:
            label = variant.variant_name

            if not label:
                parts = [part for part in [variant.size, variant.color] if part]
                label = " / ".join(parts) if parts else "Default"

            summaries.append(label)

        return ", ".join(summaries)

    def _populate_table(self, products: list[ProductListItem]) -> None:
        self._table.setRowCount(len(products))

        for row, product in enumerate(products):
            base_price_text = "" if product.base_price is None else str(product.base_price)
            supplier_text = product.supplier_name or ""
            track_stock_text = "Yes" if product.track_stock else "No"
            is_active_text = "Yes" if product.is_active else "No"
            variant_summary_text = self._build_variant_summary(product)

            items = [
                QTableWidgetItem(str(product.id)),
                QTableWidgetItem(product.name),
                QTableWidgetItem(supplier_text),
                QTableWidgetItem(base_price_text),
                QTableWidgetItem(track_stock_text),
                QTableWidgetItem(is_active_text),
                QTableWidgetItem(variant_summary_text),
            ]

            for item in items:
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)

            for column, item in enumerate(items):
                self._table.setItem(row, column, item)
