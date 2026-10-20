"""The right-hand side of the report pages: tips card plus a live list of reports from the other side."""
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from dashboard import graphics
from dashboard.theme import Theme
from logic.labels import category_label
from logic.timeago import ago


def make_tip_card(scene, title, tips):
    card = QFrame(objectName="tipCard")
    lay = QVBoxLayout(card)
    lay.setContentsMargins(24, 20, 24, 24)
    lay.setSpacing(10)
    lay.addWidget(graphics.picture(scene, 200, 167), 0, Qt.AlignmentFlag.AlignHCenter)
    lay.addWidget(QLabel(title, objectName="sideTitle"))
    for tip in tips:
        row = QHBoxLayout()
        row.setSpacing(10)
        mark = QLabel()
        mark.setPixmap(graphics.icon_pixmap("check", Theme.TAG, 16))
        mark.setFixedSize(16, 16)
        text = QLabel(tip, objectName="sideTip")
        text.setWordWrap(True)
        row.addWidget(mark, 0, Qt.AlignmentFlag.AlignTop)
        row.addWidget(text, 1)
        lay.addLayout(row)
    return card


class ClickableFrame(QFrame):
    clicked = pyqtSignal()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()


class ReportSide(QScrollArea):
    """Tips card and a list of open reports of the opposite kind (a lost item may already have been found)."""
    open_item = pyqtSignal(int)
    see_all = pyqtSignal()

    def __init__(self, db, kind, scene, tips_title, tips, list_title, list_hint):
        super().__init__()
        self.db = db
        self.other_kind = "Found" if kind == "Lost" else "Lost"
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet(Theme.TRANSPARENT_SCROLL)

        holder = QWidget()
        column = QVBoxLayout(holder)
        column.setContentsMargins(0, 0, 8, 0)
        column.setSpacing(16)
        column.addWidget(make_tip_card(scene, tips_title, tips))

        panel = QFrame(objectName="panel")
        pl = QVBoxLayout(panel)
        pl.setContentsMargins(18, 16, 18, 16)
        pl.setSpacing(8)
        pl.addWidget(QLabel(list_title, objectName="h2"))
        hint = QLabel(list_hint, objectName="hint")
        hint.setWordWrap(True)
        pl.addWidget(hint)
        self.rows = QVBoxLayout()
        self.rows.setSpacing(6)
        pl.addLayout(self.rows)
        more = QPushButton("See all items", objectName="ghost")
        more.setCursor(Qt.CursorShape.PointingHandCursor)
        more.clicked.connect(self.see_all.emit)
        pl.addWidget(more)
        column.addWidget(panel)
        column.addStretch()
        self.setWidget(holder)
        self.refresh()

    def refresh(self):
        while self.rows.count():
            item = self.rows.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        records = self.db.get_items("", self.other_kind)[:4]  # open reports, newest first
        if not records:
            empty = QLabel(f"No open {self.other_kind.lower()} reports yet.", objectName="hint")
            self.rows.addWidget(empty)
            return
        for record in records:
            self.rows.addWidget(self._row(record))

    def _row(self, r):
        color, tint = (Theme.LOST, Theme.LOST_TINT) if r["type"] == "Lost" else (Theme.FOUND, Theme.FOUND_TINT)
        row = ClickableFrame(objectName="recentRow")
        row.setCursor(Qt.CursorShape.PointingHandCursor)
        lay = QHBoxLayout(row)
        lay.setContentsMargins(10, 8, 12, 8)
        lay.setSpacing(12)
        icon = QLabel()
        icon.setFixedSize(40, 40)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setPixmap(graphics.category_pixmap(r["category"], color, 26))
        icon.setStyleSheet(f"background: {tint}; border-radius: 10px;")
        text = QVBoxLayout()
        text.setSpacing(0)
        name = r["name"] if len(r["name"]) <= 28 else r["name"][:25] + "..."
        meta = " - ".join(part for part in (r["location"], ago(r["date"])) if part)
        text.addWidget(QLabel(name, objectName="rowName"))
        text.addWidget(QLabel(meta, objectName="rowMeta"))
        lay.addWidget(icon)
        lay.addLayout(text, 1)
        for label in row.findChildren(QLabel):  # after the layout is attached, so they are children of row
            label.setTextFormat(Qt.TextFormat.PlainText)  # show user text exactly as typed
        row.setToolTip(f"{category_label(r)}. Click to open in View items.")
        row.clicked.connect(lambda item_id=r["id"]: self.open_item.emit(item_id))
        return row
