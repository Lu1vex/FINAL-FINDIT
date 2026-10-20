"""SQLite storage for FINDIT (Lost and Found System)."""
import sqlite3
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
DB_FILE = DATA_DIR / "lost_found.db"
ACTION_REPORTED, ACTION_EDITED, ACTION_CLAIMED = "Reported", "Edited", "Claimed"
ACTION_REOPENED, ACTION_DELETED = "Reopened", "Deleted"
LOG_ACTIONS = [ACTION_REPORTED, ACTION_EDITED, ACTION_CLAIMED, ACTION_REOPENED, ACTION_DELETED]
DEFAULT_CATEGORIES = ["Bags", "Electronics", "ID & Cards", "Keys", "Clothing", "Books", "Other"]


class Database:
    """The only class that talks to SQLite. Other modules call its methods."""

    def __init__(self, path=DB_FILE):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.con = sqlite3.connect(path)
        self.con.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self):
        self.con.execute(
            """CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL, name TEXT NOT NULL, category TEXT,
                location TEXT NOT NULL, date TEXT, description TEXT,
                contact TEXT NOT NULL, image TEXT DEFAULT '',
                status TEXT NOT NULL DEFAULT 'Open',
                contact_name TEXT DEFAULT '', other_category TEXT DEFAULT '')"""
        )
        self.con.execute(
            """CREATE TABLE IF NOT EXISTS claims (
                id INTEGER PRIMARY KEY AUTOINCREMENT, item_id INTEGER NOT NULL,
                claimed_by TEXT NOT NULL, contact TEXT NOT NULL, proof TEXT,
                released_by TEXT, date TEXT, notes TEXT, id_number TEXT DEFAULT '')"""
        )
        self.con.execute(
            """CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL,
                action TEXT NOT NULL, item_id INTEGER, item_name TEXT DEFAULT '',
                item_type TEXT DEFAULT '', details TEXT DEFAULT '')"""
        )
        self.con.execute(
            "CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)"
        )

        # Databases made by older versions get the new columns added.
        columns = []
        for row in self.con.execute("PRAGMA table_info(items)"):
            columns.append(row["name"])
        for name in ["contact_name", "other_category"]:
            if name not in columns:
                self.con.execute(f"ALTER TABLE items ADD COLUMN {name} TEXT DEFAULT ''")

        claim_columns = [row["name"] for row in self.con.execute("PRAGMA table_info(claims)")]
        if "id_number" not in claim_columns:
            self.con.execute("ALTER TABLE claims ADD COLUMN id_number TEXT DEFAULT ''")

        count = self.con.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
        if count == 0:
            for name in DEFAULT_CATEGORIES:
                self.con.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        self.con.commit()

    def add_item(self, kind, name, category, location, date, description, contact, image="",
                 contact_name="", other_category=""):
        """Add a lost or found report and return its id."""
        cursor = self.con.execute(
            "INSERT INTO items (type, name, category, location, date, description, contact, image, "
            "contact_name, other_category) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (kind, name, category, location, date, description, contact, image,
             contact_name, other_category),
        )
        self._log(ACTION_REPORTED, cursor.lastrowid, name, kind, f"Reported at {location}")
        self.con.commit()
        return cursor.lastrowid

    def update_item(self, item_id, name, category, location, date, description, contact, image,
                    contact_name="", other_category=""):
        """Change the details of a report. Its type and status stay the same."""
        self.con.execute(
            "UPDATE items SET name=?, category=?, location=?, date=?, description=?, contact=?, "
            "image=?, contact_name=?, other_category=? WHERE id=?",
            (name, category, location, date, description, contact, image,
             contact_name, other_category, item_id),
        )
        row = self.get_item(item_id)
        self._log(ACTION_EDITED, item_id, name, row["type"] if row else "", "Report details changed")
        self.con.commit()

    def get_items(self, text="", view="All"):
        """Reports that match the text. view is All, Lost, Found (open only) or Claimed."""
        # Escape \ % and _ so they are searched as normal letters, not wildcards.
        text = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = "%" + text + "%"

        fields = ["name", "location", "description", "category", "other_category", "contact_name"]
        checks = []
        for field in fields:
            checks.append(f"{field} LIKE ? ESCAPE '\\'")
        sql = "SELECT * FROM items WHERE (" + " OR ".join(checks) + ")"
        values = [pattern] * len(fields)

        if view == "Lost" or view == "Found":
            sql += " AND type=? AND status='Open'"
            values.append(view)
        elif view == "Claimed":
            sql += " AND status='Claimed'"

        sql += " ORDER BY id DESC"
        return self.con.execute(sql, values).fetchall()

    def get_item(self, item_id):
        """One report by id, or None."""
        return self.con.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()

    def claim_item(self, item_id, claimed_by, contact, proof="", released_by="", date="", notes="",
                   id_number=""):
        """Save who claimed a report and mark it Claimed. Both happen together or not at all."""
        row = self.get_item(item_id)
        with self.con:
            self.con.execute(
                "INSERT INTO claims (item_id, claimed_by, contact, proof, released_by, date, notes, id_number) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (item_id, claimed_by, contact, proof, released_by, date, notes, id_number),
            )
            self.con.execute("UPDATE items SET status='Claimed' WHERE id=?", (item_id,))
            self._log(ACTION_CLAIMED, item_id, row["name"] if row else "", row["type"] if row else "",
                      f"Claimed by {claimed_by}" + (f" ({proof})" if proof else ""))

    def reopen_item(self, item_id):
        """Mark a claimed report Open again. Old claims are kept as history."""
        row = self.get_item(item_id)
        self.con.execute("UPDATE items SET status='Open' WHERE id=?", (item_id,))
        self._log(ACTION_REOPENED, item_id, row["name"] if row else "", row["type"] if row else "",
                  "Marked as open again")
        self.con.commit()

    def get_claim(self, item_id):
        """The latest claim of a report, or None if it was never claimed."""
        return self.con.execute(
            "SELECT * FROM claims WHERE item_id=? ORDER BY id DESC LIMIT 1", (item_id,)
        ).fetchone()

    def delete_item(self, item_id):
        """Delete a report and its claims."""
        row = self.get_item(item_id)
        with self.con:
            self.con.execute("DELETE FROM claims WHERE item_id=?", (item_id,))
            self.con.execute("DELETE FROM items WHERE id=?", (item_id,))
            if row:  # the log keeps the name, so the history survives the delete
                self._log(ACTION_DELETED, item_id, row["name"], row["type"], "Report deleted")

    def _log(self, action, item_id, item_name, item_type, details=""):
        """Write one activity log line. The caller commits."""
        self.con.execute(
            "INSERT INTO logs (created_at, action, item_id, item_name, item_type, details) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), action, item_id, item_name, item_type, details),
        )

    def get_logs(self, text="", action="All", item_type="All", date_from="", date_to=""):
        """Activity log lines, newest first. Every filter is optional.
        date_from and date_to are yyyy-MM-dd and include the whole day."""
        text = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = "%" + text + "%"
        sql = ("SELECT * FROM logs WHERE (item_name LIKE ? ESCAPE '\\' OR details LIKE ? ESCAPE '\\' "
               "OR CAST(item_id AS TEXT) LIKE ? ESCAPE '\\')")
        values = [pattern, pattern, pattern]
        if action != "All":
            sql += " AND action=?"
            values.append(action)
        if item_type != "All":
            sql += " AND item_type=?"
            values.append(item_type)
        if date_from:
            sql += " AND date(created_at) >= ?"
            values.append(date_from)
        if date_to:
            sql += " AND date(created_at) <= ?"
            values.append(date_to)
        sql += " ORDER BY id DESC"
        return self.con.execute(sql, values).fetchall()

    def count(self, where):
        sql = "SELECT COUNT(*) FROM items WHERE " + where
        return self.con.execute(sql).fetchone()[0]

    def totals(self):
        """Counts of (lost, found, claimed) reports."""
        return self.count("type='Lost'"), self.count("type='Found'"), self.count("status='Claimed'")

    def category_names(self):
        names = []
        for row in self.con.execute("SELECT name FROM categories ORDER BY name"):
            names.append(row["name"])
        return names

    def close(self):
        self.con.close()
