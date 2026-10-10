"""Jinja filters."""
from app.ml.topics import TOPIC_LABELS


def pct(value, digits=0):
    if value is None:
        return "—"
    return f"{value * 100:.{digits}f}%"


def signed_pts(value):
    """Share delta (0.12) -> '+12 pts'."""
    if value is None:
        return "—"
    pts = value * 100
    if abs(pts) < 0.5:
        return "±0 pts"
    return f"{pts:+.0f} pts"


def topic_label(topic):
    return TOPIC_LABELS.get(topic, (topic or "").replace("_", " ").title())


def initials(name):
    """'Prof. Mark Cruz' -> 'MC' (titles like Prof./Dr./Engr. are skipped)."""
    words = [w for w in (name or "").replace(".", ". ").split() if not w.endswith(".")]
    if not words:
        return "?"
    return (words[0][0] + (words[-1][0] if len(words) > 1 else "")).upper()


def window_dates(window):
    if window is None:
        return ""
    start, end = window.start_date, window.end_date
    if start.month == end.month:
        return f"{start:%b} {start.day}–{end.day}, {end:%Y}"
    return f"{start:%b} {start.day} – {end:%b} {end.day}, {end:%Y}"
