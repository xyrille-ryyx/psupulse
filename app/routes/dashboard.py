"""Dashboard and comment explorer for faculty, department heads, student affairs and admins."""
from collections import Counter, defaultdict
from types import SimpleNamespace

from flask import Blueprint, abort, current_app, render_template, request
from flask_login import current_user

from app.extensions import db
from app.models import Alert, Feedback, FeedbackWindow, SentimentResult, Unit, WeeklyAggregate
from app.ml.topics import TOPIC_LABELS
from app.utils.audit import log_access
from app.utils.decorators import STAFF, roles_required
from app.utils.scope import OVERALL, can_see_overall, can_see_unit, visible_unit_ids, visible_units
from app.utils.settings import get_setting

bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


def _processed_windows():
    return FeedbackWindow.query.filter_by(status="processed").order_by(FeedbackWindow.start_date.desc()).all()


UNIT_RANK = {"college": 0, "department": 1, "office": 2, "course": 3}


def _default_unit():
    """University-wide for admins/student affairs; faculty land on their first course, heads on their
    department (or office)."""
    if can_see_overall(current_user):
        return None, None
    units = visible_units(current_user)
    if not units:
        abort(403)
    first = min(units, key=lambda u: UNIT_RANK.get(u.unit_type, 9)) \
        if current_user.role == "dept_head" else units[0]
    return first.id, first


def _resolve_unit():
    """Read ?unit= and return (unit_id or None for university-wide, Unit or None)."""
    raw = request.args.get("unit")
    if raw is None:
        return _default_unit()
    if raw == OVERALL:
        unit_id, unit = None, None
    else:
        try:
            unit_id = int(raw)
        except ValueError:
            abort(404)
        unit = db.get_or_404(Unit, unit_id)
    if not can_see_unit(current_user, unit_id):
        abort(403)
    return unit_id, unit


ALL_TIME = "all"


def _resolve_window(windows):
    """Read ?window= : a window id, or 'all' for every processed week. Returns (window or None, param)."""
    raw = request.args.get("window")
    if raw == ALL_TIME:
        return None, ALL_TIME
    try:
        window_id = int(raw) if raw else windows[0].id
    except ValueError:
        abort(404)
    window = next((w for w in windows if w.id == window_id), None) or abort(404)
    return window, str(window.id)


def _combine(aggs, unit_id=None, unit=None):
    """Merge weekly aggregates into one all-time summary with the same attributes."""
    aggs = [a for a in aggs if a.total]
    if not aggs:
        return None
    total = sum(a.total for a in aggs)
    counts = {k: sum(getattr(a, k) for a in aggs) for k in ("positive", "negative", "neutral")}
    topics = defaultdict(Counter)
    keywords = Counter()
    for a in aggs:
        for t in a.topics:
            topics[t["topic"]].update({k: t[k] for k in ("total", "positive", "negative", "neutral")})
        keywords.update({term: n for term, n in a.keywords})
    return SimpleNamespace(
        unit_id=unit_id, unit=unit, total=total, **counts,
        positive_share=counts["positive"] / total, negative_share=counts["negative"] / total,
        neutral_share=counts["neutral"] / total,
        avg_score=sum(a.avg_score * a.total for a in aggs) / total,
        delta_negative_share=None, delta_avg_score=None,
        topics=sorted(({"topic": t, **c} for t, c in topics.items()), key=lambda x: (-x["total"], x["topic"])),
        keywords=keywords.most_common(15),
    )


def _agg_filter(query, unit_id):
    if unit_id is None:
        return query.filter(WeeklyAggregate.unit_id.is_(None))
    return query.filter(WeeklyAggregate.unit_id == unit_id)


@bp.route("/")
@roles_required(*STAFF)
def index():
    windows = _processed_windows()
    unit_id, unit = _resolve_unit()
    min_n = get_setting("min_group_size")
    unit_choices = visible_units(current_user)

    if not windows:
        return render_template("dashboard/index.html", windows=[], unit=unit, unit_id=unit_id,
                               unit_choices=unit_choices, can_overall=can_see_overall(current_user))

    window, window_param = _resolve_window(windows)
    processed_ids = [w.id for w in windows]

    # Trend across every processed week (oldest first). Small groups are blanked out.
    trend_rows = {a.window_id: a for a in _agg_filter(WeeklyAggregate.query, unit_id).all()}
    if window is None:
        agg = _combine([trend_rows[i] for i in processed_ids if i in trend_rows], unit_id, unit)
    else:
        agg = trend_rows.get(window.id)
    suppressed = agg is None or agg.total < min_n

    trend = {"labels": [], "total": [], "positive": [], "negative": [], "neutral": [],
             "positive_n": [], "negative_n": [], "neutral_n": []}
    for w in reversed(windows):
        a = trend_rows.get(w.id)
        ok = a is not None and a.total >= min_n
        trend["labels"].append(f"Wk {w.week_number}")
        trend["total"].append(a.total if a else 0)
        for key in ("positive", "negative", "neutral"):
            trend[key].append(round(getattr(a, f"{key}_share") * 100, 1) if ok else None)
            trend[f"{key}_n"].append(getattr(a, key) if ok else None)

    # Breakdown of the child units (or colleges and offices, for the university-wide view).
    child_ids = [c.id for c in unit.children] if unit else \
        [u.id for u in Unit.query.filter(Unit.unit_type.in_(("college", "office"))).all()]
    allowed = visible_unit_ids(current_user)
    if allowed is not None:
        child_ids = [c for c in child_ids if c in allowed]
    child_rows = (WeeklyAggregate.query.filter(WeeklyAggregate.window_id.in_([window.id] if window else processed_ids),
                                               WeeklyAggregate.unit_id.in_(child_ids or [-1]))
                  .join(Unit, WeeklyAggregate.unit_id == Unit.id).order_by(Unit.code).all())
    if window is None:
        by_unit = defaultdict(list)
        for row in child_rows:
            by_unit[row.unit_id].append(row)
        children = [_combine(rows, uid, rows[0].unit) for uid, rows in by_unit.items()]
        children = sorted((c for c in children if c), key=lambda c: c.unit.code)
    else:
        children = child_rows

    # Open alerts within scope, newest first.
    alert_q = Alert.query.filter(Alert.status != "resolved")
    if allowed is not None:
        alert_q = alert_q.filter(Alert.unit_id.in_(allowed or [-1]))
    alerts = alert_q.order_by(Alert.created_at.desc(), Alert.id.desc()).limit(3).all()

    return render_template(
        "dashboard/index.html", windows=windows, window=window, window_param=window_param, unit=unit, unit_id=unit_id,
        default_window=str(windows[0].id), default_unit_id=_default_unit()[0],
        unit_choices=unit_choices, can_overall=can_see_overall(current_user), agg=agg,
        suppressed=suppressed, min_n=min_n, trend=trend, children=children, alerts=alerts,
        topic_labels=TOPIC_LABELS,
    )


@bp.route("/comments")
@roles_required(*STAFF)
def comments():
    windows = _processed_windows()
    if not windows:
        return render_template("dashboard/comments.html", windows=[], items=None)
    unit_id, unit = _resolve_unit()
    window, window_param = _resolve_window(windows)
    sentiment = request.args.get("sentiment") or ""
    topic = request.args.get("topic") or ""
    page = request.args.get("page", 1, type=int)
    min_n = get_setting("min_group_size")

    query = (Feedback.query.join(SentimentResult, SentimentResult.feedback_id == Feedback.id)
             .filter(Feedback.window_id.in_([window.id] if window else [w.id for w in windows])))
    if unit is not None:
        query = query.filter(Feedback.unit_id.in_(unit.descendant_ids()))
    total_in_group = query.count()

    items = None
    if total_in_group >= min_n:
        if sentiment in SentimentResult.LABELS:
            query = query.filter(SentimentResult.label == sentiment)
        if topic in TOPIC_LABELS:
            query = query.filter(SentimentResult.topic == topic)
        items = query.order_by(SentimentResult.score.asc()).paginate(
            page=page, per_page=current_app.config["COMMENTS_PER_PAGE"], error_out=False)
        log_access("view_comments", f"window={window_param} unit={unit.code if unit else 'all'}")

    return render_template(
        "dashboard/comments.html", windows=windows, window=window, window_param=window_param, unit=unit, unit_id=unit_id,
        default_window=str(windows[0].id), default_unit_id=_default_unit()[0],
        unit_choices=visible_units(current_user), can_overall=can_see_overall(current_user),
        items=items, total_in_group=total_in_group, min_n=min_n, sentiment=sentiment, topic=topic,
        topic_labels=TOPIC_LABELS,
    )
