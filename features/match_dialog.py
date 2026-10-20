"""Shows the reports that look like a given report, with the reasons they were suggested."""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from dashboard import graphics
from dashboard.theme import Theme
from logic.labels import contact_label
from logic.matching import STRONG_SCORE
from features.upload_items import image_path


class MatchesDialog(QDialog):
    def __init__(self, parent, item, matches, intro=""):
        super().__init__(parent)
        self.setWindowTitle("Possible matches")
        self.setModal(True)
        self.setMinimumSize(580, 480)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        other = "found" if item["type"] == "Lost" else "lost"
        header = QFrame()
        header.setStyleSheet(f"background: {Theme.LOST_TINT if item['type'] == 'Lost' else Theme.FOUND_TINT}; border: none;")
        hl = QVBoxLayout(header)
        hl.setContentsMargins(24, 18, 24, 16)
        hl.setSpacing(3)
        count = len(matches)
        hl.addWidget(QLabel(f"{count} possible match{'es' if count != 1 else ''}", objectName="formTitle"))
        sub = QLabel(f"{intro + ' ' if intro else ''}These open {other} reports look similar to "
                     f"{item['name']}. Contact the person to check.", objectName="hint")
        sub.setTextFormat(Qt.TextFormat.PlainText)
        sub.setWordWrap(True)
        hl.addWidget(sub)
        outer.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(Theme.TRANSPARENT_SCROLL)
        holder = QWidget()
        column = QVBoxLayout(holder)
        column.setContentsMargins(20, 16, 20, 8)
        column.setSpacing(10)
        for match in matches:
            column.addWidget(self._card(match))
        column.addStretch()
        scroll.setWidget(holder)
        outer.addWidget(scroll, 1)

        footer = QHBoxLayout()
        footer.setContentsMargins(20, 6, 20, 16)
        footer.addStretch()
        close = QPushButton("Close")
        close.setCursor(Qt.CursorShape.PointingHandCursor)
        close.clicked.connect(self.accept)
        footer.addWidget(close)
        outer.addLayout(footer)

    @staticmethod
    def _card(match):
        r = match.row
        color = Theme.FOUND if r["type"] == "Found" else Theme.LOST
        card = QFrame(objectName="matchCard")
        card.setStyleSheet(f"QFrame#matchCard {{ background: white; border: 1px solid {Theme.LINE};"
                           f"border-left: 6px solid {color}; border-radius: 10px; }}")
        lay = QHBoxLayout(card)
        lay.setContentsMargins(14, 12, 16, 12)
        lay.setSpacing(14)

        photo = QLabel()
        photo.setFixedSize(76, 76)
        photo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = QPixmap(image_path(r["image"]))
        if pixmap.isNull():
            photo.setPixmap(graphics.category_pixmap(r["category"], color, 44))
            photo.setStyleSheet(f"background: {Theme.FOUND_TINT if r['type'] == 'Found' else Theme.LOST_TINT}; border-radius: 8px;")
        else:
            photo.setPixmap(pixmap.scaled(76, 76, Qt.AspectRatioMode.KeepAspectRatio,
                                          Qt.TransformationMode.SmoothTransformation))
        lay.addWidget(photo)

        body = QVBoxLayout()
        body.setSpacing(3)
        top = QHBoxLayout()
        name = QLabel(r["name"])
        name.setStyleSheet("font-size: 15px; font-weight: 700;")
        strong = match.score >= STRONG_SCORE
        badge = QLabel(match.label)
        badge.setStyleSheet(f"background: {Theme.TAG if strong else '#E3EAE6'}; color: {Theme.SPRUCE if strong else Theme.MUTED};"
                            "border-radius: 10px; padding: 3px 12px; font-size: 12px; font-weight: 700;")
        top.addWidget(name)
        top.addStretch()
        top.addWidget(badge)
        body.addLayout(top)
        body.addWidget(QLabel(f"{r['type']} at {r['location']} on {r['date']}"))
        body.addWidget(QLabel("Why: " + "; ".join(match.reasons)))
        body.addWidget(QLabel(f"Contact: {contact_label(r)}"))
        lay.addLayout(body, 1)
        for label in card.findChildren(QLabel):
            if label is not photo:
                label.setTextFormat(Qt.TextFormat.PlainText)
                label.setWordWrap(label not in (name, badge))
                if label not in (name, badge):
                    label.setStyleSheet(f"color: {Theme.MUTED};")
        return card
