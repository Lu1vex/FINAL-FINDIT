"""Tests for friendly dates. Run: python -m unittest discover tests -v"""
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from logic.timeago import ago  # noqa: E402

TODAY = date(2026, 10, 5)


class AgoTests(unittest.TestCase):
    def test_recent_dates(self):
        self.assertEqual(ago("2026-10-05", TODAY), "today")
        self.assertEqual(ago("2026-10-04", TODAY), "yesterday")
        self.assertEqual(ago("2026-10-01", TODAY), "4 days ago")

    def test_older_dates(self):
        self.assertEqual(ago("2026-08-30", TODAY), "1 month ago")
        self.assertEqual(ago("2026-06-01", TODAY), "4 months ago")
        self.assertEqual(ago("2024-10-01", TODAY), "2 years ago")

    def test_future_or_unreadable_dates_do_not_crash(self):
        self.assertEqual(ago("2026-12-01", TODAY), "today")
        self.assertEqual(ago("", TODAY), "")
        self.assertEqual(ago(None, TODAY), "")
        self.assertEqual(ago("not a date", TODAY), "")


if __name__ == "__main__":
    unittest.main()
