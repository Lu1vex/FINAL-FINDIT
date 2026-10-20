"""Suggest likely matches between lost and found reports (no Qt).

A pair of reports gets points for:
  same category (+2), shared words in the item name (+3 each, up to 2 words),
  other shared words in name or description (+1 each, up to 3), same place (+1),
  and a found date within 14 days after the lost date (+1).
A found date earlier than the lost date loses 2 points.
Reports scoring MIN_SCORE or more are suggested.
"""
import re
from datetime import datetime

MIN_SCORE = 4
STRONG_SCORE = 8
MAX_MATCHES = 5
STOP_WORDS = ["the", "and", "with", "for", "from", "near", "item", "lost", "found", "my", "our",
              "its", "was", "has", "have", "one", "of", "in", "on", "at", "to", "is", "it", "an", "a"]


class Match:
    def __init__(self, row, score, reasons):
        self.row = row
        self.score = score
        self.reasons = reasons

    @property
    def label(self):
        if self.score >= STRONG_SCORE:
            return "Strong match"
        return "Possible match"


def get_words(text):
    """Lowercase words without filler words. A trailing 's' is dropped (keys -> key)."""
    words = set()
    for word in re.findall(r"[a-z0-9]+", (text or "").lower()):
        if len(word) < 2 or word in STOP_WORDS:
            continue
        if len(word) > 3 and word.endswith("s"):
            word = word[:-1]
        words.add(word)
    return words


def get_date(text):
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def score_pair(a, b):
    """Return (score, reasons) for two reports, one lost and one found."""
    score = 0
    reasons = []

    if a["category"] and a["category"] == b["category"] and a["category"] != "Other":
        score += 2
        reasons.append("Same category")

    name_words = get_words(a["name"]) & get_words(b["name"])
    if name_words:
        score += 3 * min(len(name_words), 2)
        reasons.append("Similar name: " + ", ".join(sorted(name_words)))

    words_a = get_words(a["name"]) | get_words(a["description"]) | get_words(a["other_category"])
    words_b = get_words(b["name"]) | get_words(b["description"]) | get_words(b["other_category"])
    extra_words = (words_a & words_b) - name_words
    if extra_words:
        score += min(len(extra_words), 3)
        reasons.append("Both mention: " + ", ".join(sorted(extra_words)[:4]))

    if get_words(a["location"]) & get_words(b["location"]):
        score += 1
        reasons.append("Same place")

    if a["type"] == "Lost":
        lost, found = a, b
    else:
        lost, found = b, a
    lost_date = get_date(lost["date"])
    found_date = get_date(found["date"])
    if lost_date and found_date:
        days = (found_date - lost_date).days
        if days < 0:
            score -= 2
        elif days <= 14:
            score += 1
            reasons.append("Dates are close")

    return score, reasons


def find_matches(item, candidates, limit=MAX_MATCHES):
    """Best matches for item among open reports of the opposite type, strongest first."""
    matches = []
    for other in candidates:
        if other["id"] == item["id"]:
            continue
        if other["type"] == item["type"]:
            continue
        if other["status"] != "Open":
            continue

        score, reasons = score_pair(item, other)
        if score >= MIN_SCORE:
            matches.append(Match(other, score, reasons))

    matches.sort(key=lambda match: (-match.score, -match.row["id"]))
    return matches[:limit]


def matches_for(db, item):
    """Matches for an open report. Claimed reports have none."""
    if item["status"] != "Open":
        return []

    if item["type"] == "Lost":
        opposite = "Found"
    else:
        opposite = "Lost"
    return find_matches(item, db.get_items("", opposite))
