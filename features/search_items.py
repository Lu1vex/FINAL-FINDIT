"""Search Items: a search-engine style page with filters and result cards."""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QScrollArea, QVBoxLayout, QWidget,
)

from dashboard import graphics
from dashboard.theme import Theme
from logic.labels import category_label, contact_label
from features.upload_items import image_path

BADGE_COLORS = {"Lost": Theme.LOST, "Found": Theme.FOUND, "Claimed": Theme.CLAIMED}
TINTS = {"Lost": Theme.LOST_TINT, "Found": Theme.FOUND_TINT, "Claimed": Theme.CLAIMED_TINT}
MAX_RESULTS = 50



class SearchItems(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        hero = QFrame(objectName="hero")
        hero_row = QHBoxLayout(hero)
        hero_row.setContentsMargins(30, 26, 12, 24)
        hl = QVBoxLayout()
        hl.addWidget(QLabel("Search lost and found", objectName="heroTitle"))
        hl.addWidget(QLabel("Type a name, place, or description.", objectName="heroSub"))
        hl.addSpacing(8)
        self.query = QLineEdit(objectName="bigSearch")
        self.query.setPlaceholderText("Search for a lost or found item...")
        self.query.setClearButtonEnabled(True)
        hl.addWidget(self.query)

        filters = QHBoxLayout()
        self.type_box = QComboBox()
        self.type_box.addItems(["All types", "Lost", "Found"])
        self.cat_box = QComboBox()
        self.count = QLabel("", objectName="heroCount")
        filters.addWidget(self.type_box)
        filters.addWidget(self.cat_box)
        filters.addStretch()
        filters.addWidget(self.count)
        hl.addLayout(filters)
        hero_row.addLayout(hl, 1)
        hero_row.addWidget(graphics.picture("hero.png", 250, 163))
        layout.addWidget(hero)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(Theme.TRANSPARENT_SCROLL)
        holder = QWidget()
        self.results = QVBoxLayout(holder)
        self.results.setContentsMargins(0, 0, 6, 0)
        self.results.setSpacing(10)
        self.results.addStretch()
        scroll.setWidget(holder)
        layout.addWidget(scroll, 1)

        self._reload_categories()
        self.query.textChanged.connect(self.refresh)
        self.type_box.currentTextChanged.connect(self.refresh)
        self.cat_box.currentTextChanged.connect(self.refresh)
        self.refresh()

    def _reload_categories(self):
        names = ["All categories"] + self.db.category_names()
        if names == [self.cat_box.itemText(i) for i in range(self.cat_box.count())]:
            return
        current = self.cat_box.currentText()
        self.cat_box.blockSignals(True)
        self.cat_box.clear()
        self.cat_box.addItems(names)
        self.cat_box.setCurrentText(current)
        self.cat_box.blockSignals(False)

    def refresh(self):
        self._reload_categories()
        kind, cat = self.type_box.currentText(), self.cat_box.currentText()
        rows = [r for r in self.db.get_items(self.query.text().strip(), "All")
                if kind in ("All types", r["type"]) and cat in ("All categories", r["category"])]

        while self.results.count() > 1:
            item = self.results.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not rows:
            self.results.insertWidget(0, self._empty_state())
            self.count.setText("0 results")
            return
        for i, record in enumerate(rows[:MAX_RESULTS]):
            self.results.insertWidget(i, self._card(record))
        shown = min(len(rows), MAX_RESULTS)
        self.count.setText(f"{shown} result{'s' if shown != 1 else ''}"
                           + ("" if self.query.text().strip() else " (latest reports)"))

    def _empty_state(self):
        box = QWidget()
        lay = QVBoxLayout(box)
        lay.setContentsMargins(0, 30, 0, 30)
        lay.setSpacing(6)
        lay.addWidget(graphics.picture("empty_search.png", 160, 120), 0, Qt.AlignmentFlag.AlignHCenter)
        title = QLabel("Nothing matches your search", objectName="emptyTitle")
        hint = QLabel("Try a different word, or report the item on the Report lost page.", objectName="hint")
        for label in (title, hint):
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(label)
        return box

    def _card(self, r):
        status = "Claimed" if r["status"] == "Claimed" else r["type"]
        color = BADGE_COLORS[status]
        card = QFrame(objectName="resultCard")
        lay = QHBoxLayout(card)
        lay.setContentsMargins(14, 12, 16, 12)
        lay.setSpacing(14)

        photo = QLabel()
        photo.setFixedSize(96, 96)
        photo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = QPixmap(image_path(r["image"]))
        if pixmap.isNull():  # no photo: draw an icon for the category on a tinted tile
            photo.setPixmap(graphics.category_pixmap(r["category"], color, 52))
            photo.setStyleSheet(f"background: {TINTS[status]}; border-radius: 8px;")
        else:
            photo.setPixmap(pixmap.scaled(96, 96, Qt.AspectRatioMode.KeepAspectRatio,
                                          Qt.TransformationMode.SmoothTransformation))
        lay.addWidget(photo)

        body = QVBoxLayout()
        body.setSpacing(4)
        top = QHBoxLayout()
        top.setSpacing(8)
        name = QLabel(r["name"], objectName="cardName")
        chip = QLabel(category_label(r) or "Other", objectName="chip")
        badge = QLabel(status)
        badge.setStyleSheet(f"background: {color}; color: white; border-radius: 10px;"
                            "padding: 3px 12px; font-size: 12px; font-weight: 700;")
        top.addWidget(name)
        top.addWidget(chip)
        top.addStretch()
        top.addWidget(badge)
        body.addLayout(top)
        verb = "Lost" if r["type"] == "Lost" else "Found"
        body.addWidget(QLabel(f"{verb} at {r['location']} on {r['date']}", objectName="cardMeta"))
        if r["description"]:
            desc = r["description"]
            body.addWidget(QLabel(desc if len(desc) <= 140 else desc[:137] + "..."))
        claim = self.db.get_claim(r["id"]) if status == "Claimed" else None
        if claim:
            body.addWidget(QLabel(f"Claimed by {claim['claimed_by']} on {claim['date']}", objectName="cardMeta"))
        else:
            body.addWidget(QLabel(f"Contact: {contact_label(r)}", objectName="cardMeta"))
        lay.addLayout(body, 1)
        for label in card.findChildren(QLabel):
            if label is not photo:
                label.setTextFormat(Qt.TextFormat.PlainText)  # show user text as typed
                label.setWordWrap(label not in (badge, name, chip))
        card.setStyleSheet(f"QFrame#resultCard {{ border-left: 6px solid {color}; }}"
                           f"QFrame#resultCard:hover {{ border: 1px solid {Theme.SPRUCE}; border-left: 6px solid {color}; }}")
        return card
