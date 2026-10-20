"""Tests for the on-screen text helpers. Run: python -m unittest discover tests -v"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from logic.labels import category_label, contact_label  # noqa: E402


class LabelTests(unittest.TestCase):
    def test_other_category_shows_what_it_is(self):
        row = {"category": "Other", "other_category": "Water bottle"}
        self.assertEqual(category_label(row), "Other: Water bottle")

    def test_other_without_details_and_normal_categories_stay_plain(self):
        self.assertEqual(category_label({"category": "Other", "other_category": ""}), "Other")
        self.assertEqual(category_label({"category": "Keys", "other_category": "ignored"}), "Keys")
        self.assertEqual(category_label({"category": None, "other_category": None}), "")

    def test_contact_label_joins_name_and_number(self):
        self.assertEqual(contact_label({"contact_name": "Maria Santos", "contact": "0917"}), "Maria Santos, 0917")

    def test_contact_label_for_older_reports_without_a_name(self):
        self.assertEqual(contact_label({"contact_name": "", "contact": "Ana 0917"}), "Ana 0917")
        self.assertEqual(contact_label({"contact_name": None, "contact": "Ana 0917"}), "Ana 0917")


if __name__ == "__main__":
    unittest.main()
