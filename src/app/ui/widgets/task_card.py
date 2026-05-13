from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtGui import QFontMetrics, QPaintEvent, QPainter
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.application.dto.tasks import TaskListItem
from app.ui.localization import format_date
from app.ui.task_colors import task_background


class ElidedLabel(QLabel):
    def __init__(self, text: str = "") -> None:
        super().__init__(text)
        self._full_text = text
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

    def setText(self, text: str) -> None:
        self._full_text = text
        super().setText(text)
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        metrics = QFontMetrics(self.font())
        elided_text = metrics.elidedText(self._full_text, Qt.ElideRight, self.width())
        painter.drawText(self.rect(), self.alignment(), elided_text)

class MultiLineElidedLabel(QLabel):
    def __init__(self, text: str = "", max_lines: int = 2) -> None:
        super().__init__(text)
        self._full_text = text
        self._max_lines = max_lines
        self.setWordWrap(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        line_height = self.fontMetrics().lineSpacing()
        self.setFixedHeight(line_height * max_lines + 4)

    def setText(self, text: str) -> None:
        self._full_text = text
        super().setText(text)
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        if not self._full_text:
            return

        painter = QPainter(self)
        metrics = QFontMetrics(self.font())

        line_height = metrics.lineSpacing()
        available_width = self.width()
        y = metrics.ascent()

        words = self._full_text.split()
        lines: list[str] = []
        current_line = ""

        for word in words:
            candidate = f"{current_line} {word}".strip()

            if metrics.horizontalAdvance(candidate) <= available_width:
                current_line = candidate
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

            if len(lines) == self._max_lines:
                break

        if current_line and len(lines) < self._max_lines:
            lines.append(current_line)

        if len(lines) == self._max_lines:
            remaining_text = " ".join(words)
            rendered_text = " ".join(lines)

            if len(rendered_text) < len(remaining_text):
                lines[-1] = metrics.elidedText(lines[-1], Qt.ElideRight, available_width)

        for line in lines[: self._max_lines]:
            painter.drawText(0, y, line)
            y += line_height

@dataclass(frozen=True)
class TaskCardStyle:
    background: str
    border: str
    accent: str
    icon: str
    icon_color: str
    action_background: str
    action_color: str
    completed: bool = False


class TaskCard(QFrame):
    def __init__(
        self,
        *,
        task: TaskListItem,
        title: str,
        description: str | None,
        state: str,
        action_label: str,
        action_icon: str,
        action: Callable[[int], None],
        register_click_target: Callable[[QWidget, TaskListItem], None],
    ) -> None:
        super().__init__()
        style = self._style_for(task, state)
        self.setObjectName("taskCard")
        self.setStyleSheet(
            f"QFrame#taskCard {{ background: {style.background}; "
            f"border: 1px solid {style.border}; border-radius: 18px; }}"
            "QFrame#taskCard QLabel { background: transparent; }"
        )
        register_click_target(self, task)

        icon_label = QLabel(style.icon)
        icon_label.setFixedWidth(28)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(f"font-size: 19px; font-weight: 800; color: {style.icon_color};")
        register_click_target(icon_label, task)

        title_label = ElidedLabel(title)
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title_decoration = "text-decoration: line-through;" if style.completed else ""
        title_label.setStyleSheet(f"font-weight: 700; color: #111827; {title_decoration}")
        if style.completed:
            title_font = title_label.font()
            title_font.setStrikeOut(True)
            title_label.setFont(title_font)
        register_click_target(title_label, task)

        date_label = QLabel(format_date(task.due_date))
        date_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        date_label.setWordWrap(False)
        date_label.setStyleSheet(
            f"color: #64748b; font-size: 13px; white-space: nowrap; {title_decoration}"
        )
        date_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        date_label.setMinimumWidth(date_label.fontMetrics().horizontalAdvance(format_date(task.due_date)) + 8)
        register_click_target(date_label, task)

        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(10)
        title_row.addWidget(title_label, 1)
        title_row.addSpacing(12)
        title_row.addWidget(date_label, 0, Qt.AlignRight | Qt.AlignVCenter)

        description_label = MultiLineElidedLabel(description or "", max_lines=2)
        description_label.setStyleSheet(
            f"color: #64748b; font-size: 13px; {title_decoration}"
        )
        if style.completed:
            description_font = description_label.font()
            description_font.setStrikeOut(True)
            description_label.setFont(description_font)
        description_label.setVisible(bool(description))
        register_click_target(description_label, task)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)
        main_layout.addLayout(title_row)
        main_layout.addWidget(description_label)

        action_button = QPushButton(action_icon)
        action_button.setAccessibleName(action_label)
        action_button.setFixedSize(44, 44)
        action_button.setMinimumSize(44, 44)
        action_button.setMaximumSize(44, 44)
        action_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        action_button.setCursor(Qt.PointingHandCursor)
        action_button.setStyleSheet(
            "QPushButton { "
            f"background-color: {style.action_background}; "
            f"color: {style.action_color}; "
            f"border: 1px solid {style.accent}; "
            "border-radius: 22px; "
            "font-size: 18px; "
            "font-weight: 800; "
            "padding: 0px; "
            "margin: 0px; "
            "min-width: 44px; "
            "max-width: 44px; "
            "min-height: 44px; "
            "max-height: 44px; "
            "}"
            "QPushButton:hover { "
            "background-color: rgba(255, 255, 255, 180); "
            "}"
        )
        action_button.clicked.connect(lambda _checked=False, task_id=task.id: action(task_id))

        layout = QHBoxLayout()
        layout.setContentsMargins(20, 14, 16, 14)
        layout.setSpacing(14)
        layout.addWidget(icon_label, 0, Qt.AlignVCenter)
        layout.addLayout(main_layout, 1)
        layout.addWidget(action_button, 0, Qt.AlignVCenter)
        self.setLayout(layout)

    @staticmethod
    def _style_for(task: TaskListItem, state: str) -> TaskCardStyle:
        if state == "completed":
            return TaskCardStyle(
                background="#ecfdf3",
                border="#bbf7d0",
                accent="#86efac",
                icon="✓",
                icon_color="#15803d",
                action_background="#dcfce7",
                action_color="#166534",
                completed=True,
            )
        if state == "overdue":
            return TaskCardStyle(
                background="#fff1f2",
                border="#fecdd3",
                accent="#fb7185",
                icon="!",
                icon_color="#be123c",
                action_background="#ffe4e6",
                action_color="#be123c",
            )
        if task.is_auto_order_follow_up:
            return TaskCardStyle(
                background="#ede9fe",
                border="#c4b5fd",
                accent="#7c3aed",
                icon="○",
                icon_color="#5b21b6",
                action_background="#ddd6fe",
                action_color="#4c1d95",
            )

        return TaskCardStyle(
            background=task_background(task.color_hex),
            border=task.color_hex,
            accent=task.color_hex,
            icon="○",
            icon_color=task.color_hex,
            action_background=task_background(task.color_hex),
            action_color="#111827",
        )


def task_card_state(task: TaskListItem, section: str | None = None) -> str:
    if task.completed_at is not None or section == "completed":
        return "completed"
    if section == "overdue" or task.due_date < date.today():
        return "overdue"
    return "pending"
