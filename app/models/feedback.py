from app.extensions import db


class Feedback(db.Model):
    """An anonymous comment. Deliberately stores no user id, name, or exact timestamp."""

    __tablename__ = "feedback"

    id = db.Column(db.Integer, primary_key=True)
    window_id = db.Column(
        db.Integer, db.ForeignKey("feedback_windows.id", ondelete="CASCADE"), nullable=False, index=True
    )
    unit_id = db.Column(
        db.Integer, db.ForeignKey("units.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Office feedback only: what the student did there (e.g. "Paying tuition"), PII-filtered.
    transaction_type = db.Column(db.String(100))
    text = db.Column(db.Text, nullable=False)  # already passed through the PII filter
    pii_redacted = db.Column(db.Boolean, default=False, nullable=False)
    submitted_on = db.Column(db.Date, nullable=False)  # date only, to limit re-identification

    unit = db.relationship("Unit")
    sentiment = db.relationship(
        "SentimentResult", backref="feedback", uselist=False, cascade="all, delete-orphan"
    )


class SubmissionToken(db.Model):
    """One-way HMAC of (user, window, unit). Blocks duplicate submissions without
    linking any comment back to its author."""

    __tablename__ = "submission_tokens"

    id = db.Column(db.Integer, primary_key=True)
    window_id = db.Column(
        db.Integer, db.ForeignKey("feedback_windows.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash = db.Column(db.String(64), unique=True, nullable=False)
    created_on = db.Column(db.Date, nullable=False)
