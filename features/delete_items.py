"""Delete a report after confirmation."""
from PyQt6.QtWidgets import QMessageBox

from features.upload_items import remove_image


def delete_item(parent, db, item_id):
    """Ask, then delete. Returns True if the item was deleted."""
    if item_id is None:
        QMessageBox.information(parent, "Select an item", "Select an item in the table first.")
        return False
    answer = QMessageBox.question(parent, "Delete report", "Delete this report? This cannot be undone.")
    if answer != QMessageBox.StandardButton.Yes:
        return False
    record = db.get_item(item_id)
    db.delete_item(item_id)
    if record:
        remove_image(record["image"])  # the photo is no longer needed
    return True
