"""Activity log page: every report, edit, claim, reopen and delete, with filters."""
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QAbstractItemView, QComboBox, QDateEdit, QFrame, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from dashboard.theme import Theme, fit_combo
from database.database import LOG_ACTIONS

COLUMNS = ["When", "Action", "Item ID", "Item", "Type", "Details"]
ACTION_COLORS = {
    "Reported": Theme.FOUND, "Edited": Theme.SPRUCE, "Claimed": Theme.CLAIMED,
    "Reopened": Theme.TAG, "Deleted": Theme.LOST,
}
PERIODS = ["Any time", "Today", "Last 7 days", "Last 30 days", "Custom range"]
DATE_FORMAT = "yyyy-MM-dd"


class ActivityLog(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        bar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search by item name, item ID, or details")
        self.search.setClearButtonEnabled(True)
        self.action = QComboBox()
        self.action.addItems(["All actions"] + LOG_ACTIONS)
        self.kind = QComboBox()
        self.kind.addItems(["All types", "Lost", "Found"])
        self.period = QComboBox()
        self.period.addItems(PERIODS)
        for combo in (self.action, self.kind, self.period):
            fit_combo(combo)
        bar.addWidget(self.search, 1)
        bar.addWidget(self.action)
        bar.addWidget(self.kind)
        bar.addWidget(self.period)
        layout.addLayout(bar)

        # Only shown when the period is "Custom range".
        self.range_row = QWidget()
        rr = QHBoxLayout(self.range_row)
        rr.setContentsMargins(0, 0, 0, 0)
        self.date_from = QDateEdit(QDate.currentDate().addDays(-7))
        self.date_to = QDateEdit(QDate.currentDate())
        for edit in (self.date_from, self.date_to):
            edit.setCalendarPopup(True)
            edit.setDisplayFormat(DATE_FORMAT)
        rr.addStretch()
        rr.addWidget(QLabel("From", objectName="fieldLabel"))
        rr.addWidget(self.date_from)
        rr.addWidget(QLabel("To", objectName="fieldLabel"))
        rr.addWidget(self.date_to)
        self.range_row.hide()
        layout.addWidget(self.range_row)

        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setFrameShape(QFrame.Shape.NoFrame)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(38)
        header = self.table.horizontalHeader()
        header.setHighlightSections(False)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        for column, name in enumerate(COLUMNS):
            if name in ("When", "Action", "Item ID", "Type"):
                header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
            else:
                header.setSectionResizeMode(column, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table, 1)

        footer = QHBoxLayout()
        self.count = QLabel("", objectName="hint")
        clear = QPushButton("Clear filters", objectName="ghost")
        clear.setCursor(Qt.CursorShape.PointingHandCursor)
        clear.clicked.connect(self.clear_filters)
        footer.addWidget(self.count)
        footer.addStretch()
        footer.addWidget(clear)
        layout.addLayout(footer)

        self.search.textChanged.connect(self.refresh)
        self.action.currentTextChanged.connect(self.refresh)
        self.kind.currentTextChanged.connect(self.refresh)
        self.period.currentTextChanged.connect(self._period_changed)
        self.date_from.dateChanged.connect(self.refresh)
        self.date_to.dateChanged.connect(self.refresh)
        self.refresh()

    def clear_filters(self):
        for box in (self.action, self.kind, self.period):
            box.blockSignals(True)
            box.setCurrentIndex(0)
            box.blockSignals(False)
        self.range_row.hide()
        self.search.clear()  # this also refreshes
        self.refresh()

    def _period_changed(self):
        self.range_row.setVisible(self.period.currentText() == "Custom range")
        self.refresh()

    def _date_range(self):
        """(from, to) as yyyy-MM-dd text, or empty strings for no limit."""
        today = QDate.currentDate()
        period = self.period.currentText()
        if period == "Today":
            return today.toString(DATE_FORMAT), today.toString(DATE_FORMAT)
        if period == "Last 7 days":
            return today.addDays(-6).toString(DATE_FORMAT), today.toString(DATE_FORMAT)
        if period == "Last 30 days":
            return today.addDays(-29).toString(DATE_FORMAT), today.toString(DATE_FORMAT)
        if period == "Custom range":
            return self.date_from.date().toString(DATE_FORMAT), self.date_to.date().toString(DATE_FORMAT)
        return "", ""

    def refresh(self):
        action = self.action.currentText()
        kind = self.kind.currentText()
        date_from, date_to = self._date_range()
        rows = self.db.get_logs(
            self.search.text().strip(),
            "All" if action == "All actions" else action,
            "All" if kind == "All types" else kind,
            date_from, date_to,
        )

        self.table.setRowCount(len(rows))
        for r, record in enumerate(rows):
            values = [record["created_at"], record["action"], record["item_id"],
                      record["item_name"], record["item_type"], record["details"]]
            for column, value in enumerate(values):
                cell = QTableWidgetItem("" if value is None else str(value))
                if column == 1:
                    font = cell.font()
                    font.setBold(True)
                    cell.setFont(font)
                    cell.setForeground(QColor(ACTION_COLORS.get(record["action"], Theme.SPRUCE)))
                self.table.setItem(r, column, cell)
        self.count.setText(f"{len(rows)} log entr{'y' if len(rows) == 1 else 'ies'}")
