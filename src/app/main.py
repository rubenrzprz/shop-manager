import sys

from PySide6.QtWidgets import QApplication

from app.ui.windows.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)

    app.setStyleSheet("""
        QWidget {
            font-size: 13px;
        }

        QLabel#pageTitle {
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 8px;
        }

        QTableWidget {
            gridline-color: #d0d0d0;
        }

        QPushButton {
            min-height: 30px;
            padding: 4px 10px;
        }
    """)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()