from datetime import date


class ValidationError(ValueError):
    def __init__(self, message, field=""):
        super().__init__(message)
        self.field = field


def validate_report(kind, name, location, contact_name, contact, date_text,
                    description, category="", other=""):
    if not name.strip() or not location.strip():
        raise ValidationError("Enter the item name and the location before saving.")

    if not contact_name.strip() or not contact.strip():
        raise ValidationError("Enter the contact name and a phone number or email before saving.")

    if category == "Other" and not other.strip():
        raise ValidationError("You chose Other, so type what the item is.", "other")

    if date_text > date.today().isoformat():
        raise ValidationError("The date cannot be in the future.", "date")

    if kind == "Lost" and not description.strip():
        raise ValidationError("Add a short description so others can recognize your item.", "description")


ID_PROOFS = ("School ID", "Government ID")  # proofs that come with an ID number


def validate_claim(claimed_by, contact, claim_date, report_date, proof="", id_number=""):
    if not claimed_by.strip() or not contact.strip():
        raise ValidationError("Enter who is claiming the item and how to contact them.")

    if proof in ID_PROOFS and not id_number.strip():
        raise ValidationError(f"Enter the number on the {proof}.", "id_number")

    if claim_date > date.today().isoformat():
        raise ValidationError("The claim date cannot be in the future.", "date")

    if report_date and claim_date < report_date:
        raise ValidationError(f"The claim date cannot be before the report date ({report_date}).", "date")
