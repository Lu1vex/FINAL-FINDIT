"""Claim an item (with a claim form), or reopen a claimed one."""
from PyQt6.QtWidgets import QDialog, QMessageBox

from features.claim_item import ClaimDialog


def change_status(parent, db, item_id):
    """Open item: show the claim form. Claimed item: ask, then reopen. Returns True if something changed."""
    if item_id is None:
        QMessageBox.information(parent, "Select an item", "Select an item in the table first.")
        return False
    item = db.get_item(item_id)
    if item is None:
        return False
    if item["status"] == "Open":
        dialog = ClaimDialog(parent, item)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return False
        db.claim_item(item_id, **dialog.values())
        return True
    answer = QMessageBox.question(
        parent, "Reopen report", "Reopen this report? The earlier claim stays in the record.")
    if answer != QMessageBox.StandardButton.Yes:
        return False
    db.reopen_item(item_id)
    return True
