from app.extensions import db
from app.models.base import load_json, now


class WeeklyAggregate(db.Model):
    """Sentiment summary for one unit in one window. unit_id NULL = university-wide."""

    __tablename__ = "weekly_aggregates"
    __table_args__ = (db.UniqueConstraint("window_id", "unit_id", name="uq_aggregate_window_unit"),)

    id = db.Column(db.Integer, primary_key=True)
    window_id = db.Column(
        db.Integer, db.ForeignKey("feedback_windows.id", ondelete="CASCADE"), nullable=False, index=True
    )
    unit_id = db.Column(db.Integer, db.ForeignKey("units.id", ondelete="CASCADE"), index=True)
    total = db.Column(db.Integer, default=0, nullable=False)
    positive = db.Column(db.Integer, default=0, nullable=False)
    negative = db.Column(db.Integer, default=0, nullable=False)
    neutral = db.Column(db.Integer, default=0, nullable=False)
    avg_score = db.Column(db.Float, default=0.0, nullable=False)
    positive_share = db.Column(db.Float, default=0.0, nullable=False)
    negative_share = db.Column(db.Float, default=0.0, nullable=False)
    neutral_share = db.Column(db.Float, default=0.0, nullable=False)
    delta_negative_share = db.Column(db.Float)  # vs previous processed window
    delta_avg_score = db.Column(db.Float)
    topics_json = db.Column(db.Text)
    keywords_json = db.Column(db.Text)
    computed_at = db.Column(db.DateTime, default=now, nullable=False)

    unit = db.relationship("Unit")

    @property
    def topics(self):
        """[{topic, total, positive, negative, neutral}] sorted by volume."""
        return load_json(self.topics_json, [])

    @property
    def keywords(self):
        """[[term, count], ...] sorted by count."""
        return load_json(self.keywords_json, [])
