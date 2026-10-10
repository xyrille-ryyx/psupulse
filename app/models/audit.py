from app.extensions import db
from app.models.base import now


class AccessLog(db.Model):
    """Who viewed or exported reports and raw comments (Phase D security requirement)."""

    __tablename__ = "access_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), index=True)
    action = db.Column(db.String(50), nullable=False)
    target = db.Column(db.String(200))
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=now, nullable=False, index=True)

    user = db.relationship("User")


class ChangeLog(db.Model):
    """Governance log (Phase G/H): model, category and setting changes with date and reason."""

    __tablename__ = "change_logs"
    CATEGORIES = ("analyzer", "topic_categories", "settings", "units", "other")

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))
    category = db.Column(db.String(30), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=now, nullable=False, index=True)

    user = db.relationship("User")
