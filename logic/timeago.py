"""Turn a yyyy-MM-dd date into text like '3 days ago'."""
from datetime import date, datetime


def ago(text, today=None):
    try:
        day = datetime.strptime(text, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return ""

    if today is None:
        today = date.today()
    days = (today - day).days

    if days <= 0:
        return "today"
    if days == 1:
        return "yesterday"
    if days < 30:
        return f"{days} days ago"
    if days < 365:
        months = days // 30
        if months == 1:
            return "1 month ago"
        return f"{months} months ago"

    years = days // 365
    if years == 1:
        return "1 year ago"
    return f"{years} years ago"
