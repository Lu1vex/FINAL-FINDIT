"""Turn a report's fields into text for the screen."""


def category_label(row):
    category = row["category"] or ""
    other = (row["other_category"] or "").strip()

    if category == "Other" and other:
        return "Other: " + other
    return category


def contact_label(row):
    name = (row["contact_name"] or "").strip()

    if name:
        return name + ", " + row["contact"]
    return row["contact"]
