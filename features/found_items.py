from features.lost_items import ReportForm
from dashboard.theme import Theme


class FoundItemForm(ReportForm):
    kind = "Found"
    prompt = "Where did you find it?"
    subtitle = "Thank you. Say where the item is now so its owner can come and get it."
    success_text = "Found item reported. Thank you for helping!"
    accent = Theme.FOUND
    tint = Theme.FOUND_TINT
    icon_name = "tag_check"
    button_name = "saveFound"
