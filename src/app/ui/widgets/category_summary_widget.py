from PySide6.QtWidgets import QHBoxLayout, QLabel, QMenu, QToolButton, QWidget


def category_summary(category_names: list[str]) -> str:
    if not category_names:
        return ""

    if len(category_names) == 1:
        return category_names[0]

    return f"{category_names[0]} +{len(category_names) - 1}"


class CategorySummaryWidget(QWidget):
    def __init__(self, category_names: list[str], parent=None) -> None:
        super().__init__(parent)

        self._category_names = category_names

        layout = QHBoxLayout()
        layout.setContentsMargins(6, 0, 6, 0)
        layout.setSpacing(4)

        primary_label = QLabel(category_names[0] if category_names else "")
        layout.addWidget(primary_label)

        if len(category_names) > 1:
            details_button = QToolButton()
            details_button.setText(f"+{len(category_names) - 1}")
            details_button.setAutoRaise(True)
            details_button.setFixedSize(30, 20)
            details_button.clicked.connect(self._show_categories)
            layout.addWidget(details_button)

        layout.addStretch()
        self.setLayout(layout)

    def _show_categories(self) -> None:
        menu = QMenu(self)
        for category_name in self._category_names[1:]:
            action = menu.addAction(category_name)
            action.triggered.connect(lambda _checked=False: None)

        sender = self.sender()
        if isinstance(sender, QToolButton):
            menu.exec(sender.mapToGlobal(sender.rect().bottomLeft()))
            return

        menu.exec(self.mapToGlobal(self.rect().bottomLeft()))
