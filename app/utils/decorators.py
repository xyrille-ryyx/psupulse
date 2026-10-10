from functools import wraps

from flask import abort
from flask_login import current_user

from app.extensions import login_manager


def roles_required(*roles):
    """Allow the view only for signed-in users whose role is in `roles`."""

    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return login_manager.unauthorized()
            if current_user.role not in roles:
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator


STAFF = ("faculty", "dept_head", "student_affairs", "admin")
MANAGERS = ("dept_head", "student_affairs", "admin")  # may act on alerts
