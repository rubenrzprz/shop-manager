from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QTabWidget

from app.application.services.settings import ApplicationSettingsService
from app.infrastructure.db.session import SessionLocal
from app.ui.localization import set_language, t
from app.ui.widgets.calendar_page import CalendarPage
from app.ui.widgets.customers_page import CustomersPage
from app.ui.widgets.dashboard_page import DashboardPage
from app.ui.widgets.product_categories_page import ProductCategoriesPage
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
        self.setWindowState(self.windowState() | Qt.WindowMaximized)

        self._tabs = QTabWidget()
        self._dashboard_page = DashboardPage()
        self._calendar_page = CalendarPage()
        self._products_page = ProductsPage()
        self._product_categories_page = ProductCategoriesPage()
        self._suppliers_page = SuppliersPage()
        self._customers_page = CustomersPage()
        self._orders_page = OrdersPage()
        self._settings_page = SettingsPage()
        self._dashboard_page.action_requested.connect(self._run_dashboard_action)
        self._dashboard_page.order_requested.connect(self._open_order_from_dashboard)
        self._dashboard_page.task_changed.connect(self._calendar_page.load_calendar)
        self._calendar_page.task_changed.connect(self._dashboard_page.load_tasks)
        self._settings_page.language_changed.connect(lambda _language: self.retranslate_ui())
        self._orders_page.order_changed.connect(self._dashboard_page.reload_dashboard)
        self._orders_page.task_changed.connect(self._dashboard_page.load_tasks)
        self._orders_page.task_changed.connect(self._calendar_page.load_calendar)
        self._settings_page.task_changed.connect(self._dashboard_page.load_tasks)
        self._settings_page.task_changed.connect(self._calendar_page.load_calendar)

        self._tabs.addTab(self._dashboard_page, "")
        self._tabs.addTab(self._calendar_page, "")
        self._tabs.addTab(self._products_page, "")
        self._tabs.addTab(self._product_categories_page, "")
        self._tabs.addTab(self._suppliers_page, "")
        self._tabs.addTab(self._customers_page, "")
        self._tabs.addTab(self._orders_page, "")
        self._tabs.addTab(self._settings_page, "")

        self.setCentralWidget(self._tabs)
        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        self.setWindowTitle(t("Shop Manager"))
        self._dashboard_page.retranslate_ui()
        self._calendar_page.retranslate_ui()
        self._products_page.retranslate_ui()
        self._product_categories_page.retranslate_ui()
        self._suppliers_page.retranslate_ui()
        self._customers_page.retranslate_ui()
        self._orders_page.retranslate_ui()
        self._settings_page.retranslate_ui()
        self._tabs.setTabText(0, t("Dashboard"))
        self._tabs.setTabText(1, t("Calendar"))
        self._tabs.setTabText(2, t("Products"))
        self._tabs.setTabText(3, t("Categories"))
        self._tabs.setTabText(4, t("Suppliers"))
        self._tabs.setTabText(5, t("Customers"))
        self._tabs.setTabText(6, t("Orders"))
        self._tabs.setTabText(7, t("Settings"))

    def _run_dashboard_action(self, action: str) -> None:
        modal_actions = {
            "new_product": self._products_page.open_create_dialog,
            "new_supplier": self._suppliers_page.open_create_dialog,
            "new_customer": self._customers_page.open_create_dialog,
            "new_order": self._orders_page.open_create_dialog,
        }
        modal_action = modal_actions.get(action)
        if modal_action is not None:
            modal_action()
            return

        tab_actions = {
            "calendar": 1,
            "settings": 7,
        }
        tab_index = tab_actions.get(action)
        if tab_index is None:
            return
        self._tabs.setCurrentIndex(tab_index)

    def _open_order_from_dashboard(self, order_id: int) -> None:
        self._orders_page.open_order_for_edit(order_id)

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
