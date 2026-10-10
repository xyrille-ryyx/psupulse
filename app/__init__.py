import os
from datetime import datetime

from flask import Flask, render_template

from app.config import config_by_name
from app.extensions import csrf, db, login_manager


def create_app(config_name=None):
    config_name = config_name or os.getenv("APP_ENV", "development")
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app import models  # noqa: F401  (registers every table with SQLAlchemy)
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    _register_blueprints(app)
    _register_template_helpers(app)
    _register_error_handlers(app)
    _register_security_headers(app)
    return app


def _register_blueprints(app):
    from app.routes import blueprints

    for bp in blueprints:
        app.register_blueprint(bp)


def _register_template_helpers(app):
    from flask_login import current_user

    from app.models import Alert, User
    from app.utils.formatting import initials, pct, signed_pts, topic_label, window_dates
    from app.utils.icons import icon
    from app.utils.scope import visible_unit_ids

    for f in (pct, signed_pts, topic_label, window_dates, initials):
        app.add_template_filter(f)
    app.add_template_global(icon)

    @app.context_processor
    def inject_globals():
        active_alerts = 0
        if current_user.is_authenticated and current_user.is_staff:
            query = Alert.query.filter(Alert.status != "resolved")
            allowed = visible_unit_ids(current_user)
            if allowed is not None:
                query = query.filter(Alert.unit_id.in_(allowed or [-1]))
            active_alerts = query.count()
        return {"role_labels": User.ROLES, "current_year": datetime.now().year,
                "active_alert_count": active_alerts}


def _register_error_handlers(app):
    for code in (403, 404, 500):
        app.register_error_handler(
            code, lambda e, code=code: (render_template(f"errors/{code}.html"), code)
        )


def _register_security_headers(app):
    @app.after_request
    def set_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        return response
