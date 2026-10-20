"""Browse, search, and manage reported items."""
from html import escape

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPixmap
from PyQt6.QtWidgets import (
    QAbstractItemView, QComboBox, QFrame, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from dashboard import graphics
from dashboard.theme import Theme
from features.change_status import change_status
from features.delete_items import delete_item
from features.edit_item import edit_item
from logic.labels import category_label, contact_label
from features.match_dialog import MatchesDialog
from logic.matching import matches_for
from features.upload_items import image_path

COLUMNS = ["ID", "Type", "Item", "Category", "Location", "Date", "Contact name", "Phone / email", "Status"]
STATUS_COLUMN = len(COLUMNS) - 1
TYPE_COLORS = {"Lost": Theme.LOST, "Found": Theme.FOUND}


class BrowseItems(QWidget):
    changed = pyqtSignal()  # emitted after a status change or delete

    def __init__(self, db, searchable=True):
        super().__init__()
        self.db = db
        self.rows = {}
        self.matches = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        bar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search by name, place, or description")
        self.search.textChanged.connect(self.refresh)
        self.search.setVisible(searchable)
        self.view = QComboBox()
        self.view.addItems(["All", "Lost", "Found", "Claimed"])
        self.view.currentTextChanged.connect(self.refresh)
        bar.addWidget(self.search, 1)
        bar.addWidget(self.view)
        layout.addLayout(bar)

        middle = QHBoxLayout()
        middle.setSpacing(14)
        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setFrameShape(QFrame.Shape.NoFrame)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(40)
        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setMinimumSectionSize(50)
        header.setHighlightSections(False)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.table.setTextElideMode(Qt.TextElideMode.ElideRight)

        # Short columns fit their text. The other columns share the free space.
        for column, name in enumerate(COLUMNS):
            if name in ["ID", "Type", "Date", "Status"]:
                header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
            else:
                header.setSectionResizeMode(column, QHeaderView.ResizeMode.Stretch)
        self.table.itemSelectionChanged.connect(self.show_details)
        middle.addWidget(self.table, 1)

        side = QFrame(objectName="panel")
        side.setFixedWidth(250)
        side_layout = QVBoxLayout(side)
        side_layout.setContentsMargins(14, 14, 14, 14)
        side_layout.setSpacing(12)
        self.photo = QLabel()
        self.photo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.photo.setFixedHeight(180)
        self.photo.setStyleSheet("background: #E3EAE6; border-radius: 10px;")
        self.details = QLabel()
        self.details.setTextFormat(Qt.TextFormat.RichText)
        self.details.setWordWrap(True)
        self.details.setAlignment(Qt.AlignmentFlag.AlignTop)
        side_layout.addWidget(self.photo)
        side_layout.addWidget(self.details, 1)
        self.matches_button = QPushButton("Possible matches", objectName="ghost")
        self.matches_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.matches_button.clicked.connect(self._handle_show_matches)
        self.matches_button.hide()
        side_layout.addWidget(self.matches_button)
        middle.addWidget(side)
        layout.addLayout(middle, 1)

        actions = QHBoxLayout()
        self.toggle = QPushButton("Mark as claimed")
        self.toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle.clicked.connect(self._handle_change_status)
        edit = QPushButton("Edit report", objectName="ghost")
        edit.setCursor(Qt.CursorShape.PointingHandCursor)
        edit.clicked.connect(self._handle_edit)
        delete = QPushButton("Delete", objectName="danger")
        delete.setCursor(Qt.CursorShape.PointingHandCursor)
        delete.clicked.connect(self._handle_delete)
        actions.addWidget(self.toggle)
        actions.addWidget(edit)
        actions.addWidget(delete)
        actions.addStretch()
        layout.addLayout(actions)
        self.refresh()

    def current_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        return int(self.table.item(row, 0).text())

    def refresh(self):
        records = self.db.get_items(self.search.text().strip(), self.view.currentText())
        self.rows = {}
        for record in records:
            self.rows[record["id"]] = record

        self.table.setRowCount(len(records))
        for row, record in enumerate(records):
            claimed = record["status"] == "Claimed"
            values = [record["id"], record["type"], record["name"], category_label(record),
                      record["location"], record["date"], record["contact_name"],
                      record["contact"], record["status"]]

            for column, value in enumerate(values):
                if value is None:
                    value = ""
                cell = QTableWidgetItem(str(value))

                if claimed:
                    cell.setForeground(QColor(Theme.MUTED))

                # Type and status are bold
                if column == 1 or column == STATUS_COLUMN:
                    font = cell.font()
                    font.setBold(True)
                    cell.setFont(font)
                    if column == 1 and not claimed:
                        cell.setForeground(QColor(TYPE_COLORS.get(record["type"], Theme.SPRUCE)))
                    if column == STATUS_COLUMN and claimed:
                        cell.setForeground(QColor(Theme.CLAIMED))

                self.table.setItem(row, column, cell)
        self.show_details()

    def show_details(self):
        record = self.rows.get(self.current_id())

        if record is not None and record["status"] == "Claimed":
            self.toggle.setText("Reopen report")
        else:
            self.toggle.setText("Mark as claimed")

        if record is None:
            self.matches = []
        else:
            self.matches = matches_for(self.db, record)
        self.matches_button.setVisible(len(self.matches) > 0)
        self.matches_button.setText(f"Possible matches ({len(self.matches)})")

        if record is None:
            self.photo.setPixmap(graphics.icon_pixmap("photo", Theme.LINE, 64))
            self.details.setText(f"<span style='color:{Theme.MUTED}'>Select an item to see its photo and details.</span>")
            return

        pixmap = QPixmap(image_path(record["image"]))
        if pixmap.isNull():
            # No photo, so show an icon for the category
            self.photo.setPixmap(graphics.category_pixmap(record["category"], Theme.MUTED, 72))
        else:
            self.photo.setPixmap(pixmap.scaled(
                220, 170, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

        if record["status"] == "Claimed":
            status = "Claimed"
            color = Theme.MUTED
        else:
            status = record["type"]
            color = TYPE_COLORS.get(record["type"], Theme.SPRUCE)

        claim_html = ""
        if record["status"] == "Claimed":
            claim = self.db.get_claim(record["id"])
            if claim is not None:
                lines = [
                    "Claimed by " + escape(claim["claimed_by"]),
                    escape(claim["date"] or ""),
                    "Proof: " + escape(claim["proof"] or "none recorded"),
                ]
                if claim["id_number"]:
                    lines.append("ID number: " + escape(claim["id_number"]))
                if claim["released_by"]:
                    lines.append("Released by " + escape(claim["released_by"]))
                if claim["notes"]:
                    lines.append(escape(claim["notes"]))
                claim_html = f"<p style='color:{Theme.CLAIMED}'>" + "<br>".join(lines) + "</p>"

        description = escape(record["description"] or "No description.")
        category = escape(category_label(record))
        contact = escape(contact_label(record))
        self.details.setText(
            f"<p style='font-size:17px'><b>{escape(record['name'])}</b></p>"
            f"<p style='color:{color}'><b>{status}</b></p>"
            f"<p>{description}</p>"
            f"<p style='color:{Theme.MUTED}'>{category}<br>Contact: {contact}</p>"
            + claim_html
        )

    def select_id(self, item_id):
        for row in range(self.table.rowCount()):
            if int(self.table.item(row, 0).text()) == item_id:
                self.table.selectRow(row)
                return

    def _handle_change_status(self):
        item_id = self.current_id()
        if change_status(self, self.db, item_id):
            self.refresh()
            self.changed.emit()
            self.select_id(item_id)

    def _handle_edit(self):
        item_id = self.current_id()
        if edit_item(self, self.db, item_id):
            self.refresh()
            self.changed.emit()
            self.select_id(item_id)

    def _handle_show_matches(self):
        record = self.rows.get(self.current_id())
        if record is not None and len(self.matches) > 0:
            MatchesDialog(self, record, self.matches).exec()

    def _handle_delete(self):
        if delete_item(self, self.db, self.current_id()):
            self.refresh()
            self.changed.emit()
