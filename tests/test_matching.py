"""Tests for match suggestions. Run from the project folder:
    python -m unittest discover tests -v
"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from database.database import Database  # noqa: E402
from logic.matching import find_matches, matches_for  # noqa: E402


class MatchingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "test.db")

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def add(self, kind, name, category="Other", location="Library", date="2026-10-01", description=""):
        return self.db.get_item(self.db.add_item(kind, name, category, location, date, description, "Ana"))

    def test_same_item_described_twice_is_a_strong_match(self):
        lost = self.add("Lost", "Black umbrella", description="wooden handle")
        self.add("Found", "Black umbrella", description="Has a wooden handle", date="2026-10-02")
        matches = matches_for(self.db, lost)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].label, "Strong match")

    def test_unrelated_items_do_not_match(self):
        lost = self.add("Lost", "Black umbrella")
        self.add("Found", "Laptop charger", category="Electronics", location="Gym")
        self.assertEqual(matches_for(self.db, lost), [])

    def test_only_the_opposite_type_is_suggested(self):
        lost = self.add("Lost", "House keys", category="Keys")
        self.add("Lost", "House keys", category="Keys")
        self.assertEqual(matches_for(self.db, lost), [])

    def test_claimed_reports_are_not_suggested_and_have_no_matches(self):
        lost = self.add("Lost", "House keys", category="Keys")
        found = self.add("Found", "House keys", category="Keys")
        self.db.claim_item(found["id"], "Ben", "0917")
        self.assertEqual(matches_for(self.db, lost), [])
        self.assertEqual(matches_for(self.db, self.db.get_item(found["id"])), [])

    def test_plural_words_match(self):
        lost = self.add("Lost", "Keys", category="Keys")
        self.add("Found", "House key", category="Keys")
        self.assertEqual(len(matches_for(self.db, lost)), 1)

    def test_found_before_lost_scores_lower(self):
        lost = self.add("Lost", "Blue backpack", category="Bags", date="2026-10-05")
        after = self.add("Found", "Blue backpack", category="Bags", date="2026-10-06")
        before = self.add("Found", "Blue backpack", category="Bags", date="2026-10-01")
        scores = {m.row["id"]: m.score for m in find_matches(lost, [after, before])}
        self.assertGreater(scores[after["id"]], scores[before["id"]])

    def test_other_category_details_help_matching(self):
        lost = self.db.get_item(self.db.add_item(
            "Lost", "Tumbler", "Other", "Canteen", "2026-10-01", "Blue", "0917", other_category="Water bottle"))
        self.add("Found", "Water bottle", location="Canteen", date="2026-10-02")
        self.assertEqual(len(matches_for(self.db, lost)), 1)

    def test_best_match_comes_first_and_list_is_limited(self):
        lost = self.add("Lost", "Blue backpack", category="Bags", description="two zippers")
        weak = self.add("Found", "Backpack", category="Bags", date="2026-10-02")
        strong = self.add("Found", "Blue backpack", category="Bags", description="two zippers", date="2026-10-02")
        ordered = find_matches(lost, [weak, strong])
        self.assertEqual(ordered[0].row["id"], strong["id"])
        for _ in range(8):
            self.add("Found", "Blue backpack", category="Bags", date="2026-10-02")
        self.assertEqual(len(matches_for(self.db, lost)), 5)


if __name__ == "__main__":
    unittest.main()
