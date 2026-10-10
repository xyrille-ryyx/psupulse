from app.extensions import db
from app.models.base import now


class FeedbackWindow(db.Model):
    """One weekly collection period. Lifecycle: scheduled -> open -> closed -> processed."""

    __tablename__ = "feedback_windows"
    STATUSES = ("scheduled", "open", "closed", "processed")

    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(120), nullable=False)
    week_number = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.Date, nullable=False, index=True)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default="scheduled", nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=now, nullable=False)
    opened_at = db.Column(db.DateTime)
    closed_at = db.Column(db.DateTime)
    processed_at = db.Column(db.DateTime)

    feedback = db.relationship(
        "Feedback", backref="window", lazy="dynamic", cascade="all, delete-orphan"
    )
    tokens = db.relationship(
        "SubmissionToken", backref="window", lazy="dynamic", cascade="all, delete-orphan"
    )
    aggregates = db.relationship(
        "WeeklyAggregate", backref="window", lazy="dynamic", cascade="all, delete-orphan"
    )
    alerts = db.relationship(
        "Alert", backref="window", lazy="dynamic", cascade="all, delete-orphan"
    )
    report = db.relationship(
        "Report", backref="window", uselist=False, cascade="all, delete-orphan"
    )

    @property
    def is_open(self):
        return self.status == "open"

    def previous_processed(self):
        return (
            FeedbackWindow.query.filter(
                FeedbackWindow.status == "processed",
                FeedbackWindow.start_date < self.start_date,
            )
            .order_by(FeedbackWindow.start_date.desc())
            .first()
        )

    def __repr__(self):
        return f"<FeedbackWindow week {self.week_number} ({self.status})>"
