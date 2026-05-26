from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QWidget


def resize_to_available_screen(
    widget: QWidget,
    *,
    width_ratio: float,
    height_ratio: float,
    min_width: int,
    min_height: int,
) -> None:
    screen = widget.screen() or QGuiApplication.primaryScreen()
    if screen is None:
        widget.resize(min_width, min_height)
        return

    available_geometry = screen.availableGeometry()
    width = min(
        available_geometry.width(),
        max(min_width, int(available_geometry.width() * width_ratio)),
    )
    height = min(
        available_geometry.height(),
        max(min_height, int(available_geometry.height() * height_ratio)),
    )
    widget.resize(width, height)
