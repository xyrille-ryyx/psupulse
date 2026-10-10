from app.extensions import db
from app.models.base import load_json, now


class SentimentResult(db.Model):
    __tablename__ = "sentiment_results"
    LABELS = ("positive", "negative", "neutral")

    id = db.Column(db.Integer, primary_key=True)
    feedback_id = db.Column(
        db.Integer, db.ForeignKey("feedback.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    label = db.Column(db.String(10), nullable=False, index=True)
    score = db.Column(db.Float, nullable=False)          # compound polarity, -1 .. 1
    confidence = db.Column(db.Float, nullable=False)     # 0 .. 1
    positive_score = db.Column(db.Float, default=0.0, nullable=False)
    negative_score = db.Column(db.Float, default=0.0, nullable=False)
    topic = db.Column(db.String(40), nullable=False, index=True)
    topics_json = db.Column(db.Text)
    keywords_json = db.Column(db.Text)
    analyzer_version = db.Column(db.String(40), nullable=False)
    analyzed_at = db.Column(db.DateTime, default=now, nullable=False)

    @property
    def keywords(self):
        return load_json(self.keywords_json, [])

    @property
    def topics(self):
        return load_json(self.topics_json, {})
