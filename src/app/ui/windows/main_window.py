from PySide6.QtWidgets import QMainWindow, QTabWidget

from app.application.services.settings import ApplicationSettingsService
from app.infrastructure.db.session import SessionLocal
from app.ui.localization import set_language, t
from app.ui.widgets.customers_page import CustomersPage
from app.ui.widgets.orders_page import OrdersPage
from app.ui.widgets.products_page import ProductsPage
from app.ui.widgets.settings_page import SettingsPage
from app.ui.widgets.suppliers_page import SuppliersPage


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self._load_language()
        self.setWindowTitle(t("Shop Manager"))
        self.resize(1000, 600)

        self._tabs = QTabWidget()
        self._products_page = ProductsPage()
        self._suppliers_page = SuppliersPage()
        self._customers_page = CustomersPage()
        self._orders_page = OrdersPage()
        self._settings_page = SettingsPage()
        self._settings_page.language_changed.connect(lambda _language: self.retranslate_ui())

        self._tabs.addTab(self._products_page, "")
        self._tabs.addTab(self._suppliers_page, "")
        self._tabs.addTab(self._customers_page, "")
        self._tabs.addTab(self._orders_page, "")
        self._tabs.addTab(self._settings_page, "")

        self.setCentralWidget(self._tabs)
        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        self.setWindowTitle(t("Shop Manager"))
        self._products_page.retranslate_ui()
        self._suppliers_page.retranslate_ui()
        self._customers_page.retranslate_ui()
        self._orders_page.retranslate_ui()
        self._settings_page.retranslate_ui()
        self._tabs.setTabText(0, t("Products"))
        self._tabs.setTabText(1, t("Suppliers"))
        self._tabs.setTabText(2, t("Customers"))
        self._tabs.setTabText(3, t("Orders"))
        self._tabs.setTabText(4, t("Settings"))

    def _load_language(self) -> None:
        try:
            session = SessionLocal()
        except Exception:
            return

        try:
            set_language(ApplicationSettingsService(session).app_language())
        except Exception:
            set_language("en")
        finally:
            session.close()
