import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from logic.validation import ValidationError, validate_claim, validate_report  # noqa: E402


class ValidationTests(unittest.TestCase):
    def report(self, **changes):
        values = dict(kind="Found", name="Umbrella", location="Library", contact_name="Ana",
                      contact="0917", date_text="2026-10-01", description="", category="Bags", other="")
        values.update(changes)
        validate_report(**values)

    def test_valid_report_passes(self):
        self.report()

    def test_missing_name_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.report(name="  ")

    def test_other_needs_a_description_of_the_item(self):
        with self.assertRaises(ValidationError):
            self.report(category="Other", other="")

    def test_future_date_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.report(date_text="2999-01-01")

    def test_lost_report_needs_a_description(self):
        with self.assertRaises(ValidationError):
            self.report(kind="Lost", description="")

    def test_claim_before_report_date_is_rejected(self):
        with self.assertRaises(ValidationError):
            validate_claim("Ben", "0917", "2026-09-30", "2026-10-01")

    def test_valid_claim_passes(self):
        validate_claim("Ben", "0917", "2026-10-02", "2026-10-01")

    def test_id_proof_needs_an_id_number(self):
        with self.assertRaises(ValidationError):
            validate_claim("Ben", "0917", "2026-10-02", "2026-10-01", "School ID", "  ")
        validate_claim("Ben", "0917", "2026-10-02", "2026-10-01", "School ID", "2021-001")

    def test_other_proof_needs_no_id_number(self):
        validate_claim("Ben", "0917", "2026-10-02", "2026-10-01", "Photo of the item", "")


if __name__ == "__main__":
    unittest.main()
