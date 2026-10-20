from PyQt6.QtCore import QDate, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox, QDateEdit, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QTextEdit, QVBoxLayout, QWidget,
)

from dashboard import graphics
from dashboard.theme import Theme, dashed_divider, fit_combo
from features.upload_items import ImagePicker, save_image
from logic.validation import ValidationError, validate_report

DATE_FORMAT = "yyyy-MM-dd"


def labeled(text, widget):
    cell = QWidget()
    layout = QVBoxLayout(cell)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(5)
    layout.addWidget(QLabel(text, objectName="fieldLabel"))
    layout.addWidget(widget)
    return cell


class ReportForm(QFrame):
    saved = pyqtSignal(str, int)

    MAX_WIDTH = 820
    HEADER_ICON_SIZE = 38
    DESCRIPTION_MIN_HEIGHT = 84
    DESCRIPTION_MAX_HEIGHT = 220

    # Lost form values. FoundItemForm changes these.
    kind = "Lost"
    prompt = "Where did you lose it?"
    subtitle = "Give enough detail that someone else can recognize your item."
    success_text = "Lost item reported. We hope it is found soon."
    accent = Theme.LOST
    tint = Theme.LOST_TINT
    icon_name = "tag_alert"
    button_name = "saveLost"

    def __init__(self, db):
        super().__init__(objectName="panel")
        self.db = db
        self.setMaximumWidth(self.MAX_WIDTH)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._create_fields()
        self._build_layout()
        self._toggle_other()

    def _create_fields(self):
        self.name = QLineEdit()
        self.name.setPlaceholderText("Black umbrella")

        self.category = QComboBox()
        self.category.addItems(self.db.category_names())
        fit_combo(self.category)
        self.category.currentTextChanged.connect(self._toggle_other)

        self.other = QLineEdit()
        self.other.setPlaceholderText("What is it? e.g. water bottle, umbrella")
        self.other_cell = labeled("What kind of item is it?", self.other)

        self.location = QLineEdit()
        self.location.setPlaceholderText("Library, 2nd floor")

        self.date = QDateEdit(QDate.currentDate())
        self.date.setCalendarPopup(True)
        self.date.setDisplayFormat(DATE_FORMAT)

        self.description = QTextEdit()
        self.description.setMinimumHeight(self.DESCRIPTION_MIN_HEIGHT)
        self.description.setMaximumHeight(self.DESCRIPTION_MAX_HEIGHT)
        self.description.setPlaceholderText("Color, brand, marks, contents")

        self.contact_name = QLineEdit()
        self.contact_name.setPlaceholderText("Maria Santos")

        self.contact = QLineEdit()
        self.contact.setPlaceholderText("09xx xxx xxxx or name@email.com")

        self.image = ImagePicker()

    def _build_layout(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self._build_header())
        outer.addWidget(dashed_divider())

        body = QVBoxLayout()
        body.setContentsMargins(24, 18, 24, 22)
        outer.addLayout(body)

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(14)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.addWidget(labeled("Item name", self.name), 0, 0)
        grid.addWidget(labeled("Category", self.category), 0, 1)
        grid.addWidget(self.other_cell, 1, 0, 1, 2)
        grid.addWidget(labeled(self.prompt, self.location), 2, 0)
        grid.addWidget(labeled("Date", self.date), 2, 1)
        grid.addWidget(labeled("Description", self.description), 3, 0, 1, 2)
        grid.setRowStretch(3, 1)
        grid.addWidget(labeled("Contact name", self.contact_name), 4, 0)
        grid.addWidget(labeled("Phone or email", self.contact), 4, 1)
        grid.addWidget(labeled("Photo (optional)", self.image), 5, 0, 1, 2)
        body.addLayout(grid, 1)

        self.error = QLabel("")
        self.error.setWordWrap(True)
        self.error.setStyleSheet(f"color: {Theme.LOST}; font-weight: 600;")
        body.addWidget(self.error)

        save_button = QPushButton("Save report", objectName=self.button_name)
        save_button.setCursor(Qt.CursorShape.PointingHandCursor)
        save_button.clicked.connect(self._handle_submit)
        body.addWidget(save_button)

        note = QLabel("Your contact details are shown to people who search, so the owner can reach you.",
                      objectName="hint")
        note.setWordWrap(True)
        body.addWidget(note)

    def _build_header(self):
        header = QFrame(objectName="ticketHead")
        header.setStyleSheet(f"QFrame#ticketHead {{ background: {self.tint}; border: none;"
                             "border-top-left-radius: 11px; border-top-right-radius: 11px; }")
        row = QHBoxLayout(header)
        row.setContentsMargins(24, 18, 24, 16)
        row.setSpacing(14)

        icon = QLabel()
        icon.setPixmap(graphics.icon_pixmap(self.icon_name, self.accent, self.HEADER_ICON_SIZE))
        icon.setFixedSize(self.HEADER_ICON_SIZE, self.HEADER_ICON_SIZE)

        text = QVBoxLayout()
        text.setSpacing(2)
        text.addWidget(QLabel(f"Report a {self.kind.lower()} item", objectName="formTitle"))
        subtitle = QLabel(self.subtitle, objectName="hint")
        subtitle.setWordWrap(True)
        text.addWidget(subtitle)

        row.addWidget(icon, 0, Qt.AlignmentFlag.AlignTop)
        row.addLayout(text, 1)
        return header

    def _toggle_other(self):
        show = self.category.currentText() == "Other"
        self.other_cell.setVisible(show)
        if not show:
            self.other.clear()

    def reload_categories(self):
        current = self.category.currentText()
        self.category.clear()
        self.category.addItems(self.db.category_names())
        self.category.setCurrentText(current)
        fit_combo(self.category)

    def _clear_fields(self):
        for field in [self.name, self.location, self.contact, self.contact_name, self.other]:
            field.clear()
        self.description.clear()
        self.image.clear()

    def _handle_submit(self):
        date_text = self.date.date().toString(DATE_FORMAT)

        try:
            validate_report(
                self.kind, self.name.text(), self.location.text(), self.contact_name.text(),
                self.contact.text(), date_text, self.description.toPlainText(),
                self.category.currentText(), self.other.text(),
            )
        except ValidationError as error:
            self.error.setText(str(error))
            return

        self.error.setText("")
        item_id = self.db.add_item(
            self.kind,
            self.name.text().strip(),
            self.category.currentText(),
            self.location.text().strip(),
            date_text,
            self.description.toPlainText().strip(),
            self.contact.text().strip(),
            save_image(self.image.path),
            contact_name=self.contact_name.text().strip(),
            other_category=self.other.text().strip(),
        )
        self._clear_fields()
        self.saved.emit(self.success_text, item_id)


class LostItemForm(ReportForm):
    pass
