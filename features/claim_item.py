"""The claim form: who is taking the item, and what proof they showed."""
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtWidgets import (
    QComboBox, QDateEdit, QDialog, QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QVBoxLayout,
)

from dashboard import graphics
from dashboard.theme import Theme, dashed_divider
from logic.validation import ID_PROOFS, ValidationError, validate_claim

PROOFS = ["School ID", "Government ID", "Described the item correctly", "Photo of the item", "Other"]


class ClaimDialog(QDialog):
    """Asks for the claim details. Call exec(); if accepted, use values()."""

    def __init__(self, parent, item):
        super().__init__(parent)
        self.item = item
        self.setWindowTitle("Claim item")
        self.setModal(True)
        self.setMinimumWidth(480)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QFrame()
        header.setStyleSheet(f"background: {Theme.CLAIMED_TINT}; border: none;")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(24, 18, 24, 16)
        text = QVBoxLayout()
        text.setSpacing(2)
        text.addWidget(QLabel("Claim this item", objectName="formTitle"))
        summary = QLabel(f"{item['name']}  -  {item['type'].lower()} at {item['location']}", objectName="hint")
        summary.setTextFormat(Qt.TextFormat.PlainText)
        summary.setWordWrap(True)
        text.addWidget(summary)
        hl.addLayout(text, 1)
        hl.addWidget(graphics.picture("stamp.png", 112, 31))
        outer.addWidget(header)

        body = QVBoxLayout()
        body.setContentsMargins(24, 18, 24, 20)
        body.setSpacing(12)
        outer.addLayout(body)

        self.claimed_by = QLineEdit()
        self.claimed_by.setPlaceholderText("Full name of the owner")
        self.contact = QLineEdit()
        self.contact.setPlaceholderText("Phone number or email")
        self.proof = QComboBox()
        self.proof.addItems(PROOFS)
        self.proof.currentTextChanged.connect(self._toggle_id_number)
        self.id_number = QLineEdit()
        self.id_number.setPlaceholderText("Enter ID number")
        self.id_number_label = QLabel("ID number")
        self.released_by = QLineEdit()
        self.released_by.setPlaceholderText("Staff or guard who handed it over (optional)")
        self.date = QDateEdit(QDate.currentDate())
        self.date.setCalendarPopup(True)
        self.date.setDisplayFormat("yyyy-MM-dd")
        self.notes = QTextEdit()
        self.notes.setFixedHeight(64)
        self.notes.setPlaceholderText("Anything else worth recording (optional)")

        form = QFormLayout()
        form.setVerticalSpacing(11)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.addRow("Claimed by", self.claimed_by)
        form.addRow("Contact", self.contact)
        form.addRow("Proof shown", self.proof)
        form.addRow(self.id_number_label, self.id_number)
        form.addRow("Released by", self.released_by)
        form.addRow("Date claimed", self.date)
        form.addRow("Notes", self.notes)
        body.addLayout(form)
        self._toggle_id_number()

        self.error = QLabel("")
        self.error.setWordWrap(True)
        self.error.setStyleSheet(f"color: {Theme.LOST}; font-weight: 600;")
        body.addWidget(self.error)

        body.addWidget(dashed_divider())

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel = QPushButton("Cancel", objectName="ghost")
        cancel.clicked.connect(self.reject)
        confirm = QPushButton("Confirm claim")
        confirm.setDefault(True)
        confirm.clicked.connect(self._handle_confirm)
        for button in (cancel, confirm):
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            buttons.addWidget(button)
        body.addLayout(buttons)

    def _toggle_id_number(self):
        """The ID number line only shows when the proof is an ID."""
        needs_number = self.proof.currentText() in ID_PROOFS
        self.id_number_label.setVisible(needs_number)
        self.id_number.setVisible(needs_number)
        if needs_number:
            self.id_number.setPlaceholderText(f"Enter {self.proof.currentText()} number")
        else:
            self.id_number.clear()

    def _handle_confirm(self):
        try:
            validate_claim(
                self.claimed_by.text(), self.contact.text(),
                self.date.date().toString("yyyy-MM-dd"), self.item["date"] or "",
                self.proof.currentText(), self.id_number.text(),
            )
        except ValidationError as error:
            self.error.setText(str(error))
            return

        self.error.setText("")
        self.accept()

    def values(self):
        """Keyword arguments for Database.claim_item (without the item id)."""
        return dict(
            claimed_by=self.claimed_by.text().strip(),
            contact=self.contact.text().strip(),
            proof=self.proof.currentText(),
            id_number=self.id_number.text().strip(),
            released_by=self.released_by.text().strip(),
            date=self.date.date().toString("yyyy-MM-dd"),
            notes=self.notes.toPlainText().strip(),
        )
