"""Weekly report snapshots and CSV export."""
import csv
import io

from app.extensions import db
from app.ml.pipeline import get_primary_analyzer
from app.ml.topics import TOPIC_LABELS
from app.models import Report, Unit, WeeklyAggregate
from app.models.base import dump_json, now
from app.utils.settings import get_setting

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def _agg_dict(agg, min_n):
    suppressed = agg.total < min_n
    base = {"unit_id": agg.unit_id, "total": agg.total, "suppressed": suppressed}
    if suppressed:
        return base  # counts withheld to avoid identifying students in small groups
    base.update({
        "positive": agg.positive, "negative": agg.negative, "neutral": agg.neutral,
        "positive_share": agg.positive_share, "negative_share": agg.negative_share,
        "neutral_share": agg.neutral_share, "avg_score": agg.avg_score,
        "delta_negative_share": agg.delta_negative_share, "delta_avg_score": agg.delta_avg_score,
        "topics": agg.topics, "keywords": agg.keywords[:10],
    })
    return base


def _highlights(overall, unit_rows):
    notes = []
    if overall and not overall["suppressed"]:
        notes.append(
            f"{overall['total']} comments this week: {overall['positive_share'] * 100:.0f}% positive, "
            f"{overall['negative_share'] * 100:.0f}% negative, {overall['neutral_share'] * 100:.0f}% neutral."
        )
        if overall["delta_negative_share"] is not None:
            direction = "up" if overall["delta_negative_share"] > 0 else "down"
            notes.append(f"Negative share is {direction} {abs(overall['delta_negative_share']) * 100:.0f} "
                         "points from last week.")
        concerns = [t for t in overall["topics"] if t["topic"] != "general" and t["negative"]]
        if concerns:
            top = max(concerns, key=lambda t: t["negative"])
            notes.append(f"Most negative comments were about {TOPIC_LABELS.get(top['topic'], top['topic'])} "
                         f"({top['negative']} of {top['total']}).")
    courses = [r for r in unit_rows if r["unit_type"] == "course" and not r["suppressed"]
               and r.get("delta_negative_share") is not None]
    if courses:
        worst = max(courses, key=lambda r: r["delta_negative_share"])
        if worst["delta_negative_share"] > 0:
            notes.append(f"Largest rise in negative sentiment: {worst['code']} "
                         f"(+{worst['delta_negative_share'] * 100:.0f} points).")
        best = max(courses, key=lambda r: r["positive_share"])
        notes.append(f"Most positive course: {best['code']} ({best['positive_share'] * 100:.0f}% positive).")
    return notes


def build_summary(window):
    min_n = get_setting("min_group_size")
    aggs = WeeklyAggregate.query.filter_by(window_id=window.id).all()
    units = {u.id: u for u in Unit.query.all()}
    overall = next((_agg_dict(a, min_n) for a in aggs if a.unit_id is None), None)

    type_order = {"college": 0, "department": 1, "course": 2}
    unit_rows = []
    for a in aggs:
        if a.unit_id is None:
            continue
        u = units[a.unit_id]
        row = _agg_dict(a, min_n)
        row.update({"code": u.code, "name": u.name, "unit_type": u.unit_type,
                    "parent_code": u.parent.code if u.parent else None})
        unit_rows.append(row)
    unit_rows.sort(key=lambda r: (type_order.get(r["unit_type"], 9), r["code"]))

    alerts = [{
        "id": al.id, "unit_id": al.unit_id, "unit_code": al.unit.code if al.unit else "University-wide",
        "type": al.type_label, "severity": al.severity, "message": al.message, "status": al.status,
    } for al in sorted(window.alerts, key=lambda a: SEVERITY_ORDER.get(a.severity, 9))]

    return {
        "window": {"id": window.id, "label": window.label, "week_number": window.week_number,
                   "start_date": window.start_date.isoformat(), "end_date": window.end_date.isoformat()},
        "min_group_size": min_n,
        "analyzer": get_primary_analyzer().name,
        "overall": overall,
        "units": unit_rows,
        "alerts": alerts,
        "highlights": _highlights(overall, unit_rows),
    }


def generate_report(window, user=None):
    report = window.report or Report(window_id=window.id)
    report.summary_json = dump_json(build_summary(window))
    report.generated_at = now()
    report.generated_by_id = user.id if user else None
    db.session.add(report)
    db.session.flush()
    return report


def report_csv(summary, rows):
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["PSU Pulse weekly report", summary["window"]["label"],
                     summary["window"]["start_date"], summary["window"]["end_date"]])
    writer.writerow([])
    writer.writerow(["Unit code", "Unit name", "Type", "Parent", "Comments", "Positive", "Negative",
                     "Neutral", "Positive %", "Negative %", "Neutral %", "Avg score",
                     "Change in negative % (pts)", "Top topics", "Top keywords"])
    for r in rows:
        if r["suppressed"]:
            writer.writerow([r["code"], r["name"], r["unit_type"], r["parent_code"] or "", r["total"],
                             f"hidden (fewer than {summary['min_group_size']} comments)"])
            continue
        delta = r["delta_negative_share"]
        writer.writerow([
            r["code"], r["name"], r["unit_type"], r["parent_code"] or "", r["total"],
            r["positive"], r["negative"], r["neutral"],
            f"{r['positive_share'] * 100:.1f}", f"{r['negative_share'] * 100:.1f}",
            f"{r['neutral_share'] * 100:.1f}", f"{r['avg_score']:.3f}",
            "" if delta is None else f"{delta * 100:+.1f}",
            "; ".join(TOPIC_LABELS.get(t["topic"], t["topic"]) for t in r["topics"][:3]),
            "; ".join(k for k, _ in r["keywords"][:5]),
        ])
    return out.getvalue()
