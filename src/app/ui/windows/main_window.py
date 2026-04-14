from PySide6.QtWidgets import QMainWindow

from app.ui.widgets.products_page import ProductsPage


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Shop Manager")
        self.resize(1000, 600)

        self._products_page = ProductsPage()
        self.setCentralWidget(self._products_page)