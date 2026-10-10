from app.extensions import db
from app.models.base import LongText, load_json, now


class Report(db.Model):
    """Frozen snapshot of a processed window, so a report never changes after it is shared."""

    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True)
    window_id = db.Column(
        db.Integer, db.ForeignKey("feedback_windows.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    generated_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))
    generated_at = db.Column(db.DateTime, default=now, nullable=False)
    summary_json = db.Column(LongText, nullable=False)

    generated_by = db.relationship("User")

    @property
    def summary(self):
        return load_json(self.summary_json, {})
