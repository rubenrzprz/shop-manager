from PySide6.QtWidgets import QMainWindow, QTabWidget

from app.ui.widgets.customers_page import CustomersPage
from app.ui.widgets.orders_page import OrdersPage
from app.ui.widgets.products_page import ProductsPage
from app.ui.widgets.suppliers_page import SuppliersPage


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Shop Manager")
        self.resize(1000, 600)

        self._tabs = QTabWidget()
        self._products_page = ProductsPage()
        self._suppliers_page = SuppliersPage()
        self._customers_page = CustomersPage()
        self._orders_page = OrdersPage()

        self._tabs.addTab(self._products_page, "Products")
        self._tabs.addTab(self._suppliers_page, "Suppliers")
        self._tabs.addTab(self._customers_page, "Customers")
        self._tabs.addTab(self._orders_page, "Orders")

        self.setCentralWidget(self._tabs)
