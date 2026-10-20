"""FINDIT main window: sidebar, page header, claim-tag counters, and footer."""
from PyQt6.QtCore import (
    QEasingCurve, QPointF, QPropertyAnimation, QRectF, QSize, QVariantAnimation, Qt, pyqtSignal,
)
from PyQt6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import (
    QButtonGroup, QFrame, QGraphicsOpacityEffect, QHBoxLayout, QLabel, QMainWindow,
    QMessageBox, QPushButton, QStackedWidget, QVBoxLayout, QWidget,
)

from dashboard import graphics
from dashboard.theme import Theme
from features.activity_log import ActivityLog
from features.browse_items import BrowseItems
from features.found_items import FoundItemForm
from features.lost_items import LostItemForm
from features.match_dialog import MatchesDialog
from logic.matching import matches_for
from features.search_items import SearchItems
from features.side_panel import ReportSide, make_tip_card

# (icon, name in the sidebar, one line under the page title)
NAV = [
    ("tag_alert", "Report lost", "Tell us what you lost and where."),
    ("tag_check", "Report found", "Tell us what you found so its owner can get it back."),
    ("list", "View items", "Every report in one place. Click a tag to filter."),
    ("search", "Search items", "Look for an item by name, place, or description."),
    ("check", "Activity log", "Every report, edit, claim and delete. Use the filters to narrow it down."),
    ("book", "Instructions", "How FINDIT works, in six steps."),
    ("people", "About us", "Who built FINDIT and why."),
]

STEPS = [
    ("Lost something?", "Open Report lost. Describe the item, where and when you lost it, add a photo "
                        "if you have one, and leave a way to contact you."),
    ("Found something?", "Open Report found. Describe the item and where you found it, and leave your "
                         "contact so the owner can reach you."),
    ("See every report.", "View items lists all reports. Click a tag at the top to filter by lost, found, "
                          "or claimed items. Select a row to see its photo and description, or press "
                          "Edit report to fix a mistake."),
    ("Check for matches.", "After you save a report, FINDIT suggests similar reports from the other side. "
                           "You can also select an open item and press Possible matches."),
    ("Look for a specific item.", "Search items finds reports by name, category, place, or description."),
    ("Item returned?", "Select it in the table and press Mark as claimed. Fill in who is taking it, what "
                       "proof they showed, and the ID number if it was an ID. Press Reopen report "
                       "later if it was a mistake. The Activity log keeps a record of every change."),
]

TEAM = "Luiella Jane C. Mentes, Computer Science student."
CONTACT = "luiellamentes@gmail.com"
ABOUT = ("FINDIT is a lost and found system. It helps people report items they have lost, list items "
         "they have found, and bring belongings back to their owners quickly.")
GOAL = "Make it easy to report, search, and claim lost items in one place."


class TagCard(QFrame):
    """A counter drawn like a claim tag: punched hole, colored edge, faint artwork."""
    clicked = pyqtSignal()

    def __init__(self, caption, color, art, art_opacity, art_angle):
        super().__init__()
        self.color, self.art, self.art_opacity, self.art_angle = color, art, art_opacity, art_angle
        self._hover = False
        self._target = -1
        self._anim = None
        self.setMinimumHeight(104)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(f"Show {caption.lower()}")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(60, 14, 20, 14)
        lay.setSpacing(0)
        self.value = QLabel("0", objectName="tagValue")
        lay.addWidget(self.value)
        lay.addWidget(QLabel(caption, objectName="tagCaption"))

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        shape = QPainterPath()
        shape.addRoundedRect(r, 12, 12)
        p.fillPath(shape, QColor(Theme.CARD))

        p.save()  # colored edge and artwork stay inside the tag outline
        p.setClipPath(shape)
        p.fillRect(QRectF(r.left(), r.top(), 9, r.height()), QColor(self.color))
        w = self.art.width() / self.art.devicePixelRatio()
        h = self.art.height() / self.art.devicePixelRatio()
        p.translate(r.right() - w / 2 - 22, r.center().y())
        p.rotate(self.art_angle)
        p.setOpacity(self.art_opacity)
        p.drawPixmap(int(-w / 2), int(-h / 2), self.art)
        p.restore()

        p.setPen(QPen(QColor(Theme.LINE), 1.5))  # the punched hole
        p.setBrush(QColor(Theme.PAPER))
        p.drawEllipse(QPointF(r.left() + 32, r.center().y()), 9, 9)

        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(self.color if self._hover else Theme.LINE), 2 if self._hover else 1.2))
        p.drawPath(shape)

    def enterEvent(self, event):
        self._hover = True
        self.update()

    def leaveEvent(self, event):
        self._hover = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

    def set_value(self, total):
        """Count up to the new number (only animates when the number changes)."""
        if total == self._target:
            return
        start, self._target = max(self._target, 0), total
        self._anim = QVariantAnimation()
        self._anim.setDuration(600)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.setStartValue(start)
        self._anim.setEndValue(total)
        self._anim.valueChanged.connect(lambda v: self.value.setText(f"{int(v):,}"))
        self._anim.start()


class Dashboard(QMainWindow):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("FINDIT - Find what matters.")
        self.setWindowIcon(QIcon(graphics.load("logo.png", 64)))
        self.resize(1280, 760)

        root = QWidget(objectName="root")
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_sidebar())
        right = QVBoxLayout()
        right.setSpacing(0)
        right.addWidget(self._build_topbar())
        right.addLayout(self._build_content(), 1)
        right.addWidget(self._build_footer())
        layout.addLayout(right, 1)
        self.go(2)

    # ---------- layout pieces ----------
    def _build_sidebar(self):
        self.sidebar = QFrame(objectName="sidebar")
        self.sidebar.setFixedWidth(250)
        self._sidebar_open = True
        lay = QVBoxLayout(self.sidebar)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        head = QFrame(objectName="sideHeader")
        hl = QHBoxLayout(head)
        hl.setContentsMargins(18, 22, 16, 14)
        hl.setSpacing(12)
        brand = QVBoxLayout()
        brand.setSpacing(0)
        brand.addWidget(QLabel("FINDIT", objectName="brand"))
        brand.addWidget(QLabel("Find what matters.", objectName="tagline"))
        hl.addWidget(graphics.picture("logo.png", 46))
        hl.addLayout(brand, 1)
        lay.addWidget(head)

        nav = QVBoxLayout()
        nav.setContentsMargins(10, 12, 10, 8)
        nav.setSpacing(4)
        self.nav_group = QButtonGroup(self)
        self.nav_buttons = []
        for i, (icon, text, _sub) in enumerate(NAV):
            btn = QPushButton(f"   {text}", objectName="nav")
            btn.setIcon(graphics.checked_icon(icon, "#C9D8D3", Theme.SPRUCE))
            btn.setIconSize(QSize(20, 20))
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _checked, i=i: self.go(i))
            self.nav_group.addButton(btn)
            self.nav_buttons.append(btn)
            nav.addWidget(btn)
        nav.addStretch()
        lay.addLayout(nav, 1)
        lay.addWidget(graphics.picture("sidebar_items.png", 210, 70), 0, Qt.AlignmentFlag.AlignHCenter)
        lay.addSpacing(14)
        return self.sidebar

    def _build_topbar(self):
        bar = QFrame(objectName="topbar")
        bar.setFixedHeight(48)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(12, 6, 16, 0)
        menu = QPushButton(objectName="icon")
        menu.setIcon(graphics.make_icon("menu", Theme.SPRUCE, 22))
        menu.setIconSize(QSize(22, 22))
        menu.setToolTip("Show or hide the sidebar")
        menu.clicked.connect(self.toggle_sidebar)
        full = QPushButton(objectName="icon")
        full.setIcon(graphics.make_icon("expand", Theme.SPRUCE, 20))
        full.setIconSize(QSize(20, 20))
        full.setToolTip("Full screen")
        full.clicked.connect(lambda: self.showNormal() if self.isFullScreen() else self.showFullScreen())
        lay.addWidget(menu)
        lay.addStretch()
        lay.addWidget(full)
        return bar

    def _build_footer(self):
        bar = QFrame(objectName="footer")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(24, 10, 24, 10)
        left = QLabel("<b>FINDIT.</b> Find what matters.")
        right = QLabel("Version 1.0")
        for label in (left, right):
            label.setStyleSheet(f"color: {Theme.MUTED}; font-size: 12px;")
        lay.addWidget(left)
        lay.addStretch()
        lay.addWidget(right)
        return bar

    def _build_content(self):
        content = QVBoxLayout()
        content.setContentsMargins(24, 0, 24, 14)
        content.setSpacing(14)
        head = QVBoxLayout()
        head.setSpacing(2)
        self.title = QLabel("", objectName="pageTitle")
        self.subtitle = QLabel("", objectName="pageSub")
        head.addWidget(self.title)
        head.addWidget(self.subtitle)
        content.addLayout(head)

        db = self.db
        self.lost_form, self.found_form = LostItemForm(db), FoundItemForm(db)
        self.browse = BrowseItems(db, searchable=False)
        self.search_page = SearchItems(db)
        self.activity_log = ActivityLog(db)
        self.stack = QStackedWidget()
        lost_tips = ("Name it the way a stranger would describe it.",
                     "Mention color, brand, stickers, scratches, or what was inside.",
                     "A photo helps a lot. Add one if you have it.")
        found_tips = ("Say exactly where you found it and where it is now.",
                      "Keep one detail to yourself so the owner can prove it is theirs.",
                      "Leave a contact the owner can actually reach.")
        self.lost_side = ReportSide(db, "Lost", "lost_scene.png", "A good report gets it back faster", lost_tips,
                                    "Maybe it is already here", "The latest items people have handed in. Click one to see it.")
        self.found_side = ReportSide(db, "Found", "found_scene.png", "Helping it get home", found_tips,
                                     "Maybe someone is looking", "The latest lost reports. Click one to see it.")
        for side in (self.lost_side, self.found_side):
            side.open_item.connect(self.open_item)
            side.see_all.connect(lambda: self.go(2))
        for page in (self._form_page(self.lost_form, self.lost_side), self._form_page(self.found_form, self.found_side),
                     self._items_page(), self.search_page, self.activity_log, self._instructions_page(), self._about_page()):
            self.stack.addWidget(page)
        content.addWidget(self.stack, 1)

        self.browse.changed.connect(self.refresh_all)
        self.lost_form.saved.connect(self.on_saved)
        self.found_form.saved.connect(self.on_saved)
        return content

    def _items_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(14)
        row = QHBoxLayout()
        row.setSpacing(16)
        self.cards = [
            TagCard("Total lost items", Theme.LOST, graphics.icon_pixmap("tag_alert", Theme.LOST, 76), 0.16, 12),
            TagCard("Total found items", Theme.FOUND, graphics.icon_pixmap("tag_check", Theme.FOUND, 76), 0.16, 12),
            TagCard("Claimed items", Theme.CLAIMED, graphics.load("stamp.png", 136, 37), 0.55, -9),
        ]
        for card, view in zip(self.cards, ("Lost", "Found", "Claimed")):
            card.clicked.connect(lambda v=view: self.browse.view.setCurrentText(v))
            row.addWidget(card, 1)
        lay.addLayout(row)
        lay.addWidget(self.browse, 1)
        return page

    @staticmethod
    def _form_page(form, side):
        """The form fills the left; tips and a live list of the other side's reports fill the right."""
        page = QWidget()
        lay = QHBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(24)
        side.setMinimumWidth(340)
        side.setMaximumWidth(460)
        lay.addWidget(form, 3)
        lay.addWidget(side, 2)
        return page

    @staticmethod
    def _instructions_page():
        page = QWidget()
        outer = QHBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(24)
        panel = QFrame(objectName="panel")
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(30, 26, 30, 26)
        lay.setSpacing(22)
        for number, (title, text) in enumerate(STEPS, 1):  # these really are a sequence
            row = QHBoxLayout()
            row.setSpacing(16)
            badge = QLabel(str(number), objectName="stepNum")
            badge.setFixedSize(34, 34)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            col = QVBoxLayout()
            col.setSpacing(2)
            body = QLabel(text, objectName="hint")
            body.setWordWrap(True)
            col.addWidget(QLabel(title, objectName="stepTitle"))
            col.addWidget(body)
            row.addWidget(badge, 0, Qt.AlignmentFlag.AlignTop)
            row.addLayout(col, 1)
            lay.addLayout(row)
        lay.addStretch()
        outer.addWidget(panel, 3)
        card = make_tip_card("found_scene.png", "Quick tips", (
            "Search before you report. Your item may already be here.",
            "Add a photo and keep one detail to yourself to prove ownership.",
            "Mark an item as claimed as soon as it is returned."))
        card.setMinimumWidth(340)
        card.setMaximumWidth(460)
        column = QVBoxLayout()
        column.addWidget(card)
        column.addStretch()
        outer.addLayout(column, 2)
        return page

    @staticmethod
    def _about_page():
        page = QWidget()
        outer = QHBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(24)
        panel = QFrame(objectName="panel")
        row = QHBoxLayout(panel)
        row.setContentsMargins(32, 28, 32, 28)
        row.setSpacing(28)
        col = QVBoxLayout()
        col.setSpacing(12)
        col.addWidget(QLabel("FINDIT", objectName="h1"))
        for text in (ABOUT, f"<b>Our goal.</b> {GOAL}", f"<b>Built by.</b> {TEAM}", f"<b>Contact.</b> {CONTACT}"):
            label = QLabel(text)
            label.setTextFormat(Qt.TextFormat.RichText)
            label.setWordWrap(True)
            label.setStyleSheet("font-size: 15px;")
            col.addWidget(label)
        chips = QHBoxLayout()
        chips.setSpacing(8)
        for name in ("Python", "PyQt6", "SQLite"):
            chips.addWidget(QLabel(name, objectName="techChip"))
        chips.addStretch()
        col.addSpacing(6)
        col.addLayout(chips)
        col.addStretch()
        row.addWidget(graphics.picture("logo.png", 110), 0, Qt.AlignmentFlag.AlignTop)
        row.addLayout(col, 1)
        outer.addWidget(panel, 3)
        card = make_tip_card("lost_scene.png", "What FINDIT does", (
            "Takes lost and found reports in under a minute.",
            "Suggests matches between lost and found items.",
            "Records who claimed an item and what proof they showed."))
        card.setMinimumWidth(340)
        card.setMaximumWidth(460)
        column = QVBoxLayout()
        column.addWidget(card)
        column.addStretch()
        outer.addLayout(column, 2)
        return page

    # ---------- behavior ----------
    def toggle_sidebar(self):
        """Slide the sidebar closed or open."""
        self._sidebar_open = opening = not self._sidebar_open
        anim = QVariantAnimation(self)
        anim.setDuration(220)
        anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        anim.setStartValue(self.sidebar.width() if self.sidebar.isVisible() else 1)
        anim.setEndValue(250 if opening else 1)
        anim.valueChanged.connect(lambda v: self.sidebar.setFixedWidth(max(1, int(v))))
        if opening:
            self.sidebar.show()
        else:
            anim.finished.connect(self.sidebar.hide)
        anim.start(QVariantAnimation.DeletionPolicy.DeleteWhenStopped)

    def _fade(self, page):
        """Fade a page in when it is opened."""
        old = getattr(self, "_fade_anim", None)
        if old is not None:
            old.stop()
        effect = QGraphicsOpacityEffect(page)
        page.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(260)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.finished.connect(lambda: page.setGraphicsEffect(None))
        anim.start()
        self._fade_anim = anim

    def go(self, index):
        _icon, name, sub = NAV[index]
        self.stack.setCurrentIndex(index)
        self._fade(self.stack.currentWidget())
        self.nav_buttons[index].setChecked(True)
        self.title.setText(name)
        self.subtitle.setText(sub)
        if index in (0, 1):
            self.lost_form.reload_categories()
            self.found_form.reload_categories()
            self.lost_side.refresh()
            self.found_side.refresh()
        else:
            self.refresh_all()

    def open_item(self, item_id):
        """Show one report in View items (used by the lists beside the report forms)."""
        self.browse.view.setCurrentText("All")
        self.go(2)
        self.browse.select_id(item_id)

    def refresh_all(self):
        self.browse.refresh()
        self.search_page.refresh()
        self.activity_log.refresh()
        self.update_stats()

    def update_stats(self):
        for card, total in zip(self.cards, self.db.totals()):
            card.set_value(total)

    def on_saved(self, message, item_id):
        self.browse.view.setCurrentText("All")
        self.go(2)
        item = self.db.get_item(item_id)
        matches = matches_for(self.db, item) if item else []
        if matches:  # the new report looks like reports on the other side
            MatchesDialog(self, item, matches, intro=message).exec()
        else:
            QMessageBox.information(self, "FINDIT", message)
