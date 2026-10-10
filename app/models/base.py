import json
from datetime import datetime

from sqlalchemy.dialects.mysql import LONGTEXT

from app.extensions import db

# TEXT on MySQL is capped at 64 KB; report snapshots can exceed that.
LongText = db.Text().with_variant(LONGTEXT(), "mysql")


def now():
    return datetime.now().replace(microsecond=0)


def load_json(raw, default):
    if not raw:
        return default
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return default


def dump_json(value):
    return json.dumps(value, ensure_ascii=False)
