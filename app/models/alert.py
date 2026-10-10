from app.extensions import db
from app.models.base import now


class Alert(db.Model):
    __tablename__ = "alerts"

    TYPES = {
        "negative_spike": "Sharp rise in negative sentiment",
        "high_negative": "High share of negative comments",
        "recurring_topic": "Recurring concern",
        "safety_concern": "Safety-related concern",
    }
    SEVERITIES = ("low", "medium", "high")
    STATUSES = ("open", "acknowledged", "resolved")

    id = db.Column(db.Integer, primary_key=True)
    window_id = db.Column(
        db.Integer, db.ForeignKey("feedback_windows.id", ondelete="CASCADE"), nullable=False, index=True
    )
    unit_id = db.Column(db.Integer, db.ForeignKey("units.id", ondelete="CASCADE"), index=True)
    alert_type = db.Column(db.String(30), nullable=False)
    severity = db.Column(db.String(10), nullable=False, index=True)
    topic = db.Column(db.String(40))
    metric = db.Column(db.Float)
    message = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default="open", nullable=False, index=True)
    action_notes = db.Column(db.Text)
    public_note = db.Column(db.Boolean, default=False, nullable=False)  # shown to students as "You said, we did"
    handled_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))
    created_at = db.Column(db.DateTime, default=now, nullable=False)
    updated_at = db.Column(db.DateTime, default=now, onupdate=now, nullable=False)

    unit = db.relationship("Unit")
    handled_by = db.relationship("User")

    @property
    def type_label(self):
        return self.TYPES.get(self.alert_type, self.alert_type)
