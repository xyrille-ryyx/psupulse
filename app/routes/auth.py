from urllib.parse import urlparse

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.extensions import db
from app.models import User
from app.models.base import now
from app.utils.audit import log_access

bp = Blueprint("auth", __name__, url_prefix="/auth")


def _safe_next(target):
    """Only allow redirects back into this site."""
    if not target:
        return None
    parsed = urlparse(target)
    return target if not parsed.netloc and not parsed.scheme and target.startswith("/") else None


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            flash("Incorrect username or password.", "error")
        elif not user.active:
            flash("This account is disabled. Please contact the system administrator.", "error")
        else:
            login_user(user, remember=bool(request.form.get("remember")))
            user.last_login = now()
            db.session.commit()
            log_access("login")
            return redirect(_safe_next(request.args.get("next")) or url_for("main.index"))
    return render_template("auth/login.html")


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("main.index"))


@bp.route("/password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        current = request.form.get("current_password", "")
        new = request.form.get("new_password", "")
        confirm = request.form.get("confirm_password", "")
        if not current_user.check_password(current):
            flash("Your current password is incorrect.", "error")
        elif len(new) < 8:
            flash("The new password must be at least 8 characters.", "error")
        elif new != confirm:
            flash("The new passwords do not match.", "error")
        else:
            current_user.set_password(new)
            db.session.commit()
            flash("Password updated.", "success")
            return redirect(url_for("main.index"))
    return render_template("auth/change_password.html")
