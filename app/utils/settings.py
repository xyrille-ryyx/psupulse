"""Runtime settings that administrators can change without a redeploy."""
from app.extensions import db
from app.models import Setting

DEFAULTS = {
    "min_group_size": (
        "5", int,
        "Minimum number of comments before a group's results are shown (protects small classes).",
    ),
    "negative_spike_threshold": (
        "0.15", float,
        "Week-over-week rise in negative share that raises an alert (0.15 = 15 percentage points).",
    ),
    "high_negative_threshold": (
        "0.50", float,
        "Share of negative comments in a week that raises an alert (0.50 = 50%).",
    ),
    "recurring_topic_min": (
        "3", int,
        "Negative comments on the same topic, in two consecutive weeks, needed to flag it as recurring.",
    ),
}


def get_setting(key):
    default, cast, _ = DEFAULTS[key]
    row = db.session.get(Setting, key)
    try:
        return cast(row.value if row else default)
    except (TypeError, ValueError):
        return cast(default)


def set_setting(key, value):
    _, cast, _ = DEFAULTS[key]
    cast(value)  # raises ValueError for bad input
    row = db.session.get(Setting, key)
    if row is None:
        db.session.add(Setting(key=key, value=str(value)))
    else:
        row.value = str(value)


def all_settings():
    return [
        {"key": key, "value": get_setting(key), "description": desc}
        for key, (_, _, desc) in DEFAULTS.items()
    ]
