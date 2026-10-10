from app.extensions import db
from app.models.base import now

# USER may_access UNIT: enrolled courses (students), handled courses (faculty),
# or the department a head manages.
user_units = db.Table(
    "user_units",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    db.Column("unit_id", db.Integer, db.ForeignKey("units.id", ondelete="CASCADE"), primary_key=True),
)


class Unit(db.Model):
    """College, department or course. Units form a tree: college > department > course."""

    __tablename__ = "units"
    TYPES = ("college", "department", "course")

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
