from app.extensions import db
from app.models.base import now

# USER may_access UNIT: enrolled courses (students), handled courses (faculty),
# the department a head manages, or the office a staff member runs.
user_units = db.Table(
    "user_units",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    db.Column("unit_id", db.Integer, db.ForeignKey("units.id", ondelete="CASCADE"), primary_key=True),
)


# Created by init_db.py and database/psupulse.sql so students can rate transactions
# right after installation. Admins can add more under Admin > Units.
DEFAULT_OFFICES = [
    ("CASHIER", "Cashier's Office"),
    ("REGISTRAR", "Office of the Registrar"),
    ("ACCOUNTING", "Accounting Office"),
    ("LIBRARY", "University Library"),
    ("OSAS", "Office of Student Affairs and Services"),
]

# Suggestions shown when a student describes the transaction they made at an office.
COMMON_TRANSACTIONS = [
    "Paying tuition or fees",
    "Requesting documents (TOR, COG, certificates)",
    "Enrollment or registration",
    "Adding or dropping subjects",
    "Clearance signing",
    "ID application or replacement",
    "Scholarship or assistance",
    "Borrowing or returning books",
    "Inquiry or follow-up",
]


class Unit(db.Model):
    """College, department, course or office. Academic units form a tree:
    college > department > course. Offices (cashier, registrar, ...) stand alone and
    collect feedback on transactions any student can make."""

    __tablename__ = "units"
    TYPES = ("college", "department", "course", "office")

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    unit_type = db.Column(db.String(20), nullable=False, index=True)
    parent_id = db.Column(db.Integer, db.ForeignKey("units.id", ondelete="SET NULL"))
    created_at = db.Column(db.DateTime, default=now, nullable=False)

    parent = db.relationship(
        "Unit", remote_side=[id], backref=db.backref("children", order_by="Unit.code")
    )

    @property
    def label(self):
        return f"{self.code} — {self.name}"

    def descendant_ids(self):
        ids = [self.id]
        for child in self.children:
            ids.extend(child.descendant_ids())
        return ids

    def ancestors(self):
        chain, node = [], self.parent
        while node is not None:
            chain.append(node)
            node = node.parent
        return chain

    def __repr__(self):
        return f"<Unit {self.code}>"
