"""Edit an existing report (everything except its type and claim status)."""
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtWidgets import (
    QComboBox, QDateEdit, QDialog, QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QTextEdit, QVBoxLayout,
)

from dashboard import graphics
from dashboard.theme import Theme, dashed_divider, fit_combo
from features.upload_items import ImagePicker, remove_image, save_image
from logic.validation import ValidationError, validate_report


class EditDialog(QDialog):
    """The report form, filled in with the current details. Call exec(); if accepted, use values()."""

    def __init__(self, parent, db, item):
        super().__init__(parent)
        self.item = item
        self.setWindowTitle("Edit report")
        self.setModal(True)
        self.setMinimumWidth(500)
        lost = item["type"] == "Lost"
        accent, tint = (Theme.LOST, Theme.LOST_TINT) if lost else (Theme.FOUND, Theme.FOUND_TINT)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QFrame()
        header.setStyleSheet(f"background: {tint}; border: none;")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(24, 18, 24, 16)
        hl.setSpacing(14)
        mark = QLabel()
        mark.setPixmap(graphics.icon_pixmap("tag_alert" if lost else "tag_check", accent, 36))
        mark.setFixedSize(36, 36)
        text = QVBoxLayout()
        text.setSpacing(2)
        text.addWidget(QLabel(f"Edit {item['type'].lower()} report", objectName="formTitle"))
        text.addWidget(QLabel("Fix a typo or add a detail. The report keeps its place in the list.", objectName="hint"))
        hl.addWidget(mark, 0, Qt.AlignmentFlag.AlignTop)
        hl.addLayout(text, 1)
        outer.addWidget(header)

        body = QVBoxLayout()
        body.setContentsMargins(24, 18, 24, 20)
        body.setSpacing(12)
        outer.addLayout(body)

        self.name = QLineEdit(item["name"])
        self.category = QComboBox()
        names = db.category_names()
        if item["category"] and item["category"] not in names:
            names.append(item["category"])  # keep a category that was removed later
        self.category.addItems(names)
        self.category.setCurrentText(item["category"] or "")
        fit_combo(self.category)
        self.other = QLineEdit(item["other_category"] or "")
        self.other.setPlaceholderText("What is it? e.g. water bottle, umbrella")
        self.other_label = QLabel("Specify")
        self.category.currentTextChanged.connect(self._toggle_other)
        self.location = QLineEdit(item["location"])
        saved_date = QDate.fromString(item["date"] or "", "yyyy-MM-dd")
        self.date = QDateEdit(saved_date if saved_date.isValid() else QDate.currentDate())
        self.date.setCalendarPopup(True)
        self.date.setDisplayFormat("yyyy-MM-dd")
        self.description = QTextEdit()
        self.description.setPlainText(item["description"] or "")
        self.description.setFixedHeight(80)
        self.contact_name = QLineEdit(item["contact_name"] or "")
        self.contact = QLineEdit(item["contact"])
        self.image = ImagePicker()
        self.image.label.setText("Keeping the current photo" if item["image"] else "No photo yet")

        form = QFormLayout()
        form.setVerticalSpacing(11)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form.addRow("Item name", self.name)
        form.addRow("Category", self.category)
        form.addRow(self.other_label, self.other)
        form.addRow("Location", self.location)
        form.addRow("Date", self.date)
        form.addRow("Description", self.description)
        form.addRow("Contact name", self.contact_name)
        form.addRow("Phone or email", self.contact)
        form.addRow("Photo", self.image)
        body.addLayout(form)
        self._toggle_other()

        self.error = QLabel("")
        self.error.setWordWrap(True)
        self.error.setStyleSheet(f"color: {Theme.LOST}; font-weight: 600;")
        body.addWidget(self.error)

        body.addWidget(dashed_divider())

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel = QPushButton("Cancel", objectName="ghost")
        cancel.clicked.connect(self.reject)
        save = QPushButton("Save changes")
        save.setDefault(True)
        save.clicked.connect(self._handle_save)
        for button in (cancel, save):
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            buttons.addWidget(button)
        body.addLayout(buttons)

    def _toggle_other(self):
        """The Specify box only appears when the category is Other."""
        show = self.category.currentText() == "Other"
        self.other.setVisible(show)
        self.other_label.setVisible(show)
        if not show:
            self.other.clear()

    def _handle_save(self):
        try:
            validate_report(
                self.item["type"], self.name.text(), self.location.text(), self.contact_name.text(),
                self.contact.text(), self.date.date().toString("yyyy-MM-dd"),
                self.description.toPlainText(), self.category.currentText(), self.other.text(),
            )
        except ValidationError as error:
            self.error.setText(str(error))
            return

        self.error.setText("")
        self.accept()

    def values(self):
        """Keyword arguments for Database.update_item (without the id and image)."""
        return dict(
            name=self.name.text().strip(),
            category=self.category.currentText(),
            location=self.location.text().strip(),
            date=self.date.date().toString("yyyy-MM-dd"),
            description=self.description.toPlainText().strip(),
            contact=self.contact.text().strip(),
            contact_name=self.contact_name.text().strip(),
            other_category=self.other.text().strip(),
        )


def edit_item(parent, db, item_id):
    """Show the edit form and save it. Returns True if the report was changed."""
    if item_id is None:
        QMessageBox.information(parent, "Select an item", "Select an item in the table first.")
        return False
    item = db.get_item(item_id)
    if item is None:
        return False
    dialog = EditDialog(parent, db, item)
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return False
    new_photo = save_image(dialog.image.path)  # "" when no new photo was chosen
    db.update_item(item_id, image=new_photo or item["image"], **dialog.values())
    if new_photo:
        remove_image(item["image"])  # the old photo has been replaced
    return True
