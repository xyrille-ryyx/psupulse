"""Weekly processing - the heart of the business process in Section 4.2:

    window closes -> classify sentiment & group topics -> aggregate by week and unit
    -> raise alerts -> generate weekly report
"""
from collections import Counter, defaultdict

from app.extensions import db
from app.ml import analyze_batch
from app.ml.keywords import top_terms
from app.models import Alert, Feedback, SentimentResult, Unit, WeeklyAggregate
from app.models.base import dump_json, now
from app.utils.settings import get_setting


# --------------------------------------------------------------------------- classify
def classify_window(window, reclassify=False):
    query = Feedback.query.filter_by(window_id=window.id)
    if not reclassify:
        query = query.outerjoin(SentimentResult).filter(SentimentResult.id.is_(None))
    items = query.all()
    results = analyze_batch([fb.text for fb in items]) if items else []
    for fb, result in zip(items, results):
        row = fb.sentiment or SentimentResult(feedback=fb)
        row.label = result["label"]
        row.score = result["score"]
        row.confidence = result["confidence"]
        row.positive_score = result["positive_score"]
        row.negative_score = result["negative_score"]
        row.topic = result["topic"]
        row.topics_json = dump_json(result["topics"])
        row.keywords_json = dump_json(result["keywords"])
        row.analyzer_version = result["analyzer_version"]
        row.analyzed_at = now()
        db.session.add(row)
    db.session.flush()
    return len(items)


# --------------------------------------------------------------------------- aggregate
def _new_bucket():
    return {"labels": Counter(), "scores": [], "topics": defaultdict(Counter), "keywords": []}


def build_aggregates(window):
    WeeklyAggregate.query.filter_by(window_id=window.id).delete()
    db.session.flush()

    units = {u.id: u for u in Unit.query.all()}
    ancestors = {uid: [a.id for a in u.ancestors()] for uid, u in units.items()}
    rows = (
        db.session.query(Feedback.unit_id, SentimentResult)
        .join(SentimentResult, SentimentResult.feedback_id == Feedback.id)
        .filter(Feedback.window_id == window.id)
        .all()
    )

    # Each comment counts for its course, every parent unit, and the university (None).
    buckets = defaultdict(_new_bucket)
    for unit_id, res in rows:
        for key in [None, unit_id, *ancestors.get(unit_id, [])]:
            b = buckets[key]
            b["labels"][res.label] += 1
            b["scores"].append(res.score)
            b["topics"][res.topic][res.label] += 1
            b["keywords"].append(res.keywords)

    previous = window.previous_processed()
    prev = {a.unit_id: a for a in previous.aggregates} if previous else {}

    created = []
    for unit_id, b in buckets.items():
        total = len(b["scores"])
        pos, neg, neu = (b["labels"][k] for k in ("positive", "negative", "neutral"))
        agg = WeeklyAggregate(
            window_id=window.id,
            unit_id=unit_id,
            total=total,
            positive=pos,
            negative=neg,
            neutral=neu,
            avg_score=round(sum(b["scores"]) / total, 4),
            positive_share=round(pos / total, 4),
            negative_share=round(neg / total, 4),
            neutral_share=round(neu / total, 4),
            topics_json=dump_json(sorted(
                ({"topic": t, "total": sum(c.values()), "positive": c["positive"],
                  "negative": c["negative"], "neutral": c["neutral"]} for t, c in b["topics"].items()),
                key=lambda x: (-x["total"], x["topic"]),
            )),
            keywords_json=dump_json(top_terms(b["keywords"], limit=15)),
        )
        before = prev.get(unit_id)
        if before is not None and before.total:
            agg.delta_negative_share = round(agg.negative_share - before.negative_share, 4)
            agg.delta_avg_score = round(agg.avg_score - before.avg_score, 4)
        db.session.add(agg)
        created.append(agg)
    db.session.flush()
    return created


# --------------------------------------------------------------------------- alerts
def evaluate_alerts(window):
    """Flag sharp rises in negative sentiment, high negativity, recurring and safety topics.
    Sentiment alerts are raised for courses, offices and the university as a whole; topic alerts
    for courses and offices only. Department heads see the course alerts inside their department."""
    # Re-processing replaces untouched auto alerts but keeps ones staff already acted on.
    Alert.query.filter_by(window_id=window.id, status="open").filter(Alert.action_notes.is_(None)).delete()
    db.session.flush()

    min_n = get_setting("min_group_size")
    spike = get_setting("negative_spike_threshold")
    high = get_setting("high_negative_threshold")
    recurring_min = get_setting("recurring_topic_min")

    previous = window.previous_processed()
    prev_topics = {a.unit_id: {t["topic"]: t for t in a.topics} for a in previous.aggregates} if previous else {}
    existing = {(a.unit_id, a.alert_type, a.topic) for a in window.alerts}

    aggregates = (
        WeeklyAggregate.query.filter_by(window_id=window.id)
        .outerjoin(Unit, WeeklyAggregate.unit_id == Unit.id)
        .filter(db.or_(WeeklyAggregate.unit_id.is_(None), Unit.unit_type.in_(("course", "office"))))
        .all()
    )
    created = []

    def raise_alert(agg, alert_type, severity, message, metric=None, topic=None):
        if (agg.unit_id, alert_type, topic) in existing:
            return
        alert = Alert(window_id=window.id, unit_id=agg.unit_id, alert_type=alert_type,
                      severity=severity, message=message[:255], metric=metric, topic=topic)
        db.session.add(alert)
        created.append(alert)

    for agg in aggregates:
        if agg.total < min_n:
            continue  # too few comments to say anything without identifying students
        where = agg.unit.code if agg.unit else "University-wide"

        if agg.delta_negative_share is not None and agg.delta_negative_share >= spike:
            raise_alert(agg, "negative_spike", "high" if agg.delta_negative_share >= 2 * spike else "medium",
                        f"{where}: negative comments rose {agg.delta_negative_share * 100:.0f} points "
                        f"to {agg.negative_share * 100:.0f}% this week.", agg.delta_negative_share)
        elif agg.negative_share >= high:
            raise_alert(agg, "high_negative", "high" if agg.negative_share >= 0.7 else "medium",
                        f"{where}: {agg.negative_share * 100:.0f}% of {agg.total} comments are negative.",
                        agg.negative_share)

        if agg.unit_id is None:
            continue  # topic alerts are course/office-level; university-wide counts always "recur"
        last_week = prev_topics.get(agg.unit_id, {})
        for t in agg.topics:
            if t["topic"] == "safety" and t["negative"] > 0:
                raise_alert(agg, "safety_concern", "high",
                            f"{where}: {t['negative']} negative comment(s) about safety and security.",
                            t["negative"], "safety")
            elif (t["topic"] != "general" and t["negative"] >= recurring_min
                  and last_week.get(t["topic"], {}).get("negative", 0) >= recurring_min):
                label = t["topic"].replace("_", " ")
                raise_alert(agg, "recurring_topic", "medium",
                            f"{where}: '{label}' drew {t['negative']} negative comments again "
                            f"(last week: {last_week[t['topic']]['negative']}).", t["negative"], t["topic"])
    db.session.flush()
    return created


# --------------------------------------------------------------------------- orchestration
def process_window(window, user=None, reclassify=False):
    """Close (if needed), classify, aggregate, alert and report. Commits."""
    from app.utils.reports import generate_report

    if window.status in ("scheduled", "open"):
        window.status = "closed"
        window.closed_at = now()
    classified = classify_window(window, reclassify=reclassify)
    build_aggregates(window)
    alerts = evaluate_alerts(window)
    window.status = "processed"
    window.processed_at = now()
    db.session.flush()
    report = generate_report(window, user)
    db.session.commit()
    return {"classified": classified, "alerts": len(alerts), "report_id": report.id}
