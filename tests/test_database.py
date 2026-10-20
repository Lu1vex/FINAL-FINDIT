"""Automated tests for the Database class.  Run from the project folder:
    python -m unittest discover tests -v
"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from database.database import DEFAULT_CATEGORIES, Database  # noqa: E402


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "test.db")

    def tearDown(self):
        self.db.con.close()
        self.tmp.cleanup()

    def add(self, kind="Lost", name="Black umbrella", location="Library"):
        self.db.add_item(kind, name, "Other", location, "2026-10-01", "Wooden handle", "Ana")

    def test_add_and_get(self):
        self.add()
        rows = self.db.get_items()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["name"], "Black umbrella")
        self.assertEqual(rows[0]["status"], "Open")

    def test_search_matches_name_and_location(self):
        self.add(name="Black umbrella", location="Library")
        self.add(kind="Found", name="House keys", location="Gym")
        self.assertEqual(len(self.db.get_items("umbrella")), 1)
        self.assertEqual(len(self.db.get_items("gym")), 1)

    def test_search_without_match_is_empty(self):
        self.add()
        self.assertEqual(self.db.get_items("laptop"), [])

    def test_type_filter_shows_open_items_of_that_type(self):
        self.add(kind="Lost")
        self.add(kind="Found", name="Wallet")
        self.assertEqual([r["type"] for r in self.db.get_items("", "Found")], ["Found"])

    def claim(self, item_id, name="Ben Cruz"):
        self.db.claim_item(item_id, name, "0917 000 0000", "School ID", "Ms. Reyes", "2026-10-03", "Came with a friend")

    def test_claim_marks_item_claimed_and_saves_record(self):
        self.add()
        item_id = self.db.get_items()[0]["id"]
        self.claim(item_id)
        self.assertEqual(len(self.db.get_items("", "Claimed")), 1)
        self.assertEqual(self.db.get_items("", "Lost"), [])
        record = self.db.get_claim(item_id)
        self.assertEqual((record["claimed_by"], record["proof"], record["released_by"]),
                         ("Ben Cruz", "School ID", "Ms. Reyes"))

    def test_reopen_returns_item_to_open_and_keeps_history(self):
        self.add()
        item_id = self.db.get_items()[0]["id"]
        self.claim(item_id)
        self.db.reopen_item(item_id)
        self.assertEqual(self.db.get_items("", "Claimed"), [])
        self.assertEqual(len(self.db.get_items("", "Lost")), 1)
        self.claim(item_id, name="Cara Diaz")  # claimed again by someone else
        self.assertEqual(self.db.get_claim(item_id)["claimed_by"], "Cara Diaz")

    def test_get_claim_is_none_for_unclaimed_item(self):
        self.add()
        self.assertIsNone(self.db.get_claim(self.db.get_items()[0]["id"]))

    def test_delete_removes_claim_records(self):
        self.add()
        item_id = self.db.get_items()[0]["id"]
        self.claim(item_id)
        self.db.delete_item(item_id)
        self.assertIsNone(self.db.get_claim(item_id))

    def test_delete_item(self):
        self.add()
        self.db.delete_item(self.db.get_items()[0]["id"])
        self.assertEqual(self.db.get_items(), [])

    def test_totals(self):
        self.add(kind="Lost")
        self.add(kind="Found", name="Wallet")
        self.claim(self.db.get_items()[0]["id"])
        self.assertEqual(self.db.totals(), (1, 1, 1))

    def test_add_item_returns_new_id(self):
        first = self.db.add_item("Lost", "Umbrella", "Other", "Library", "2026-10-01", "", "Ana")
        second = self.db.add_item("Found", "Keys", "Keys", "Gym", "2026-10-02", "", "Ben")
        self.assertEqual(self.db.get_item(second)["name"], "Keys")
        self.assertNotEqual(first, second)

    def test_update_item_changes_details_but_not_type_or_status(self):
        self.add()
        item_id = self.db.get_items()[0]["id"]
        self.db.update_item(item_id, "Red umbrella", "Bags", "Canteen", "2026-10-02", "Torn cover", "Ana, 0917", "p.png")
        row = self.db.get_item(item_id)
        self.assertEqual((row["name"], row["category"], row["location"], row["image"]),
                         ("Red umbrella", "Bags", "Canteen", "p.png"))
        self.assertEqual((row["type"], row["status"]), ("Lost", "Open"))

    def test_contact_name_and_other_category_are_saved_and_searchable(self):
        item_id = self.db.add_item("Lost", "Tumbler", "Other", "Canteen", "2026-10-01", "Blue", "0917 111 2222",
                                   contact_name="Maria Santos", other_category="Water bottle")
        row = self.db.get_item(item_id)
        self.assertEqual((row["contact_name"], row["contact"], row["other_category"]),
                         ("Maria Santos", "0917 111 2222", "Water bottle"))
        self.assertEqual(len(self.db.get_items("water bottle")), 1)
        self.assertEqual(len(self.db.get_items("maria")), 1)

    def test_update_item_can_change_contact_name_and_other_category(self):
        self.add()
        item_id = self.db.get_items()[0]["id"]
        self.db.update_item(item_id, "Tumbler", "Other", "Canteen", "2026-10-01", "", "0917", "",
                            contact_name="Ana Cruz", other_category="Thermos")
        row = self.db.get_item(item_id)
        self.assertEqual((row["contact_name"], row["other_category"]), ("Ana Cruz", "Thermos"))

    def test_old_database_is_upgraded_with_new_columns(self):
        old = Path(self.tmp.name) / "old.db"
        import sqlite3
        con = sqlite3.connect(old)
        con.execute("""CREATE TABLE items (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT NOT NULL,
            name TEXT NOT NULL, category TEXT, location TEXT NOT NULL, date TEXT, description TEXT,
            contact TEXT NOT NULL, image TEXT DEFAULT '', status TEXT NOT NULL DEFAULT 'Open')""")
        con.execute("INSERT INTO items (type,name,category,location,date,description,contact) "
                    "VALUES ('Lost','Umbrella','Other','Library','2026-10-01','','Ana 0917')")
        con.commit()
        con.close()
        db = Database(old)
        row = db.get_items()[0]
        self.assertEqual((row["contact"], row["contact_name"], row["other_category"]), ("Ana 0917", "", ""))
        db.close()

    def test_claim_saves_id_number(self):
        self.add()
        item_id = self.db.get_items()[0]["id"]
        self.db.claim_item(item_id, "Ben Cruz", "0917", "School ID", "", "2026-10-03", "", id_number="2021-00123")
        self.assertEqual(self.db.get_claim(item_id)["id_number"], "2021-00123")

    def test_actions_are_logged(self):
        self.add()
        item_id = self.db.get_items()[0]["id"]
        self.db.update_item(item_id, "Red umbrella", "Bags", "Canteen", "2026-10-02", "", "Ana", "")
        self.claim(item_id)
        self.db.reopen_item(item_id)
        self.db.delete_item(item_id)
        actions = [r["action"] for r in self.db.get_logs()]
        self.assertEqual(actions, ["Deleted", "Reopened", "Claimed", "Edited", "Reported"])
        self.assertEqual(self.db.get_logs()[0]["item_name"], "Red umbrella")  # kept after delete

    def test_log_filters(self):
        self.add(kind="Lost", name="Umbrella")
        self.add(kind="Found", name="Wallet")
        self.claim(self.db.get_items("wallet")[0]["id"])
        self.assertEqual(len(self.db.get_logs(action="Claimed")), 1)
        self.assertEqual(len(self.db.get_logs(item_type="Lost")), 1)
        self.assertEqual(len(self.db.get_logs("wallet")), 2)
        today = self.db.get_logs()[0]["created_at"][:10]
        self.assertEqual(len(self.db.get_logs(date_from=today, date_to=today)), 3)
        self.assertEqual(self.db.get_logs(date_to="2000-01-01"), [])

    def test_default_categories_are_created(self):
        self.assertEqual(sorted(self.db.category_names()), sorted(DEFAULT_CATEGORIES))

    def test_search_treats_percent_and_underscore_literally(self):
        self.add(name="Black umbrella")
        self.add(name="100% cotton shirt")
        self.add(name="gym_bag")
        self.assertEqual(len(self.db.get_items("%")), 1)
        self.assertEqual(len(self.db.get_items("_")), 1)

    def test_get_item_returns_row_or_none(self):
        self.add()
        item_id = self.db.get_items()[0]["id"]
        self.assertEqual(self.db.get_item(item_id)["name"], "Black umbrella")
        self.assertIsNone(self.db.get_item(9999))

    def test_database_creates_missing_folder(self):
        nested = Path(self.tmp.name) / "a" / "b" / "x.db"
        db = Database(nested)
        db.close()
        self.assertTrue(nested.exists())


if __name__ == "__main__":
    unittest.main()
