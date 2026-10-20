"""Photo upload: copies chosen images into asset/image."""
import os
import shutil
import uuid
from pathlib import Path

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QPushButton, QWidget

from dashboard import graphics
from dashboard.theme import Theme

IMAGE_DIR = Path(__file__).resolve().parent.parent / "asset" / "image"


def save_image(source):
    """Copy a photo into asset/image and return its new file name."""
    if not source:
        return ""
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    dest = IMAGE_DIR / f"{uuid.uuid4().hex}{Path(source).suffix.lower()}"
    shutil.copy(source, dest)
    return dest.name


def image_path(name):
    return str(IMAGE_DIR / name) if name else ""


def remove_image(name):
    """Delete a stored photo (ignores a missing file)."""
    if name:
        try:
            os.remove(image_path(name))
        except OSError:
            pass


class ImagePicker(QWidget):
    def __init__(self):
        super().__init__()
        self.path = ""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        button = QPushButton("Choose photo", objectName="ghost")
        button.setIcon(graphics.make_icon("photo", Theme.SPRUCE))
        button.setIconSize(QSize(18, 18))
        button.clicked.connect(self.choose)
        self.thumb = QLabel()
        self.thumb.setFixedSize(44, 44)
        self.thumb.setStyleSheet("border-radius: 6px;")
        self.thumb.hide()
        self.label = QLabel("No photo chosen", objectName="hint")
        layout.addWidget(button)
        layout.addWidget(self.thumb)
        layout.addWidget(self.label, 1)

    def choose(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose photo", "", "Images (*.png *.jpg *.jpeg *.webp)")
        if path:
            self.path = path
            self.label.setText(Path(path).name)
            preview = QPixmap(path)
            if not preview.isNull():
                self.thumb.setPixmap(preview.scaled(
                    44, 44, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation))
                self.thumb.show()

    def clear(self):
        self.path = ""
        self.thumb.clear()
        self.thumb.hide()
        self.label.setText("No photo chosen")

