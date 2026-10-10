from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    if not current_user.is_authenticated:
        return render_template("landing.html")
    if current_user.role == "student":
        return redirect(url_for("feedback.submit"))
    return redirect(url_for("dashboard.index"))


@bp.route("/guide")
@login_required
def guide():
    return render_template("guide.html")


@bp.route("/privacy")
def privacy():
    return render_template("privacy.html")
