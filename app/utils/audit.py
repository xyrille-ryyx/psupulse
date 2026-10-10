from flask import has_request_context, request
from flask_login import current_user

from app.extensions import db
from app.models import AccessLog, ChangeLog


def log_access(action, target=None):
    db.session.add(AccessLog(
        user_id=current_user.id if current_user.is_authenticated else None,
        action=action,
        target=(target or "")[:200],
        ip_address=request.remote_addr,
    ))
    db.session.commit()


def log_change(category, description, reason=None, user=None):
    """Adds to the session; the caller commits together with the change itself."""
    if user is None and has_request_context() and current_user.is_authenticated:
        user = current_user
    db.session.add(ChangeLog(
        user_id=user.id if user else None,
        category=category,
        description=description[:255],
        reason=reason,
    ))
