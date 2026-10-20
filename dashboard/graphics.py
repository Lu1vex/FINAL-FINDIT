from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import QLabel

ART_DIR = Path(__file__).resolve().parent.parent / "asset" / "art"

CATEGORY_FILES = {
    "Bags": "bags",
    "Electronics": "electronics",
    "ID & Cards": "id_cards",
    "Keys": "keys",
    "Clothing": "clothing",
    "Books": "books",
}


def load(name, width, height=None, color=None):
    """Load a PNG from asset/art, scaled to width x height. A color repaints a one-color icon."""
    if height is None:
        height = width

    pixmap = QPixmap(str(ART_DIR / name))
    pixmap = pixmap.scaled(width * 2, height * 2, Qt.AspectRatioMode.KeepAspectRatio,
                           Qt.TransformationMode.SmoothTransformation)

    if color is not None:
        painter = QPainter(pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), QColor(color))
        painter.end()

    pixmap.setDevicePixelRatio(2)  # twice as many pixels, so it stays sharp
    return pixmap


def icon_pixmap(name, color, size=20):
    return load(f"icons/{name}.png", size, color=color)


def make_icon(name, color, size=20):
    return QIcon(icon_pixmap(name, color, size))


def checked_icon(name, off_color, on_color, size=20):
    icon = QIcon()
    icon.addPixmap(icon_pixmap(name, off_color, size), QIcon.Mode.Normal, QIcon.State.Off)
    icon.addPixmap(icon_pixmap(name, on_color, size), QIcon.Mode.Normal, QIcon.State.On)
    return icon


def category_pixmap(category, color, size=64):
    name = CATEGORY_FILES.get(category, "other")
    return icon_pixmap(name, color, size)


def picture(name, width, height=None):
    """A QLabel that shows an image from asset/art."""
    if height is None:
        height = width

    label = QLabel()
    label.setPixmap(load(name, width, height))
    label.setFixedSize(width, height)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return label
