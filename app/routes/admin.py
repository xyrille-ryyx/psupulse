"""System administration: users, units, feedback windows, settings, change log, analyzer lab."""
import csv
import io
from datetime import datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from app.extensions import db
from app.ml import analyze, engine_status
from app.ml.evaluation import cohens_kappa, evaluate
from app.ml.pipeline import get_primary_analyzer
from app.ml.sentiment import wordcount_analyzer
from app.models import (AccessLog, Alert, ChangeLog, Feedback, FeedbackWindow, Report, Unit, User)
from app.models.base import now
from app.utils.audit import log_change
from app.utils.decorators import roles_required
from app.utils.processing import process_window
from app.utils.reports import generate_report
from app.utils.settings import DEFAULTS, all_settings, get_setting, set_setting

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.before_request
@roles_required("admin")
def guard():
    """Every admin route requires the admin role."""


# --------------------------------------------------------------------------- overview
@bp.route("/")
def index():
    stats = {
        "users": User.query.count(),
        "students": User.query.filter_by(role="student").count(),
        "units": Unit.query.count(),
        "windows": FeedbackWindow.query.count(),
        "feedback": Feedback.query.count(),
        "open_alerts": Alert.query.filter(Alert.status != "resolved").count(),
        "reports": Report.query.count(),
    }
    open_window = FeedbackWindow.query.filter_by(status="open").first()
    pending = (Feedback.query.filter_by(window_id=open_window.id).count() if open_window else 0)
    return render_template("admin/index.html", stats=stats, open_window=open_window, pending=pending)


# --------------------------------------------------------------------------- users
def _assign_units(user, unit_ids):
    user.units = Unit.query.filter(Unit.id.in_(unit_ids or [-1])).all()


@bp.route("/users")
def users():
    role = request.args.get("role", "")
    query = User.query
    if role in User.ROLES:
        query = query.filter_by(role=role)
    return render_template("admin/users.html", users=query.order_by(User.role, User.username).all(),
                           role=role, units=Unit.query.order_by(Unit.code).all())


@bp.route("/users/new", methods=["POST"])
def user_create():
    f = request.form
    username = f.get("username", "").strip()
    if not username or not f.get("full_name") or f.get("role") not in User.ROLES:
        flash("Username, full name and role are required.", "error")
    elif User.query.filter_by(username=username).first():
        flash(f"Username '{username}' is already taken.", "error")
    elif len(f.get("password", "")) < 8:
        flash("Initial password must be at least 8 characters.", "error")
    else:
        user = User(username=username, full_name=f["full_name"].strip(),
                    email=f.get("email", "").strip() or None, role=f["role"])
        user.set_password(f["password"])
        _assign_units(user, f.getlist("unit_ids", type=int))
        db.session.add(user)
        db.session.commit()
        flash(f"User '{username}' created.", "success")
    return redirect(url_for("admin.users"))


@bp.route("/users/<int:user_id>", methods=["GET", "POST"])
def user_edit(user_id):
    user = db.get_or_404(User, user_id)
    if request.method == "POST":
        f = request.form
        user.full_name = f.get("full_name", user.full_name).strip()
        user.email = f.get("email", "").strip() or None
        if f.get("role") in User.ROLES and user.id != current_user.id:
            user.role = f["role"]
        _assign_units(user, f.getlist("unit_ids", type=int))
        if f.get("password"):
            if len(f["password"]) < 8:
                flash("New password must be at least 8 characters.", "error")
                return redirect(url_for("admin.user_edit", user_id=user.id))
            user.set_password(f["password"])
        db.session.commit()
        flash("User updated.", "success")
        return redirect(url_for("admin.users"))
    return render_template("admin/user_edit.html", user=user, units=Unit.query.order_by(Unit.code).all())


@bp.route("/users/<int:user_id>/toggle", methods=["POST"])
def user_toggle(user_id):
    user = db.get_or_404(User, user_id)
    if user.id == current_user.id:
        flash("You cannot disable your own account.", "error")
    else:
        user.active = not user.active
        db.session.commit()
        flash(f"{user.username} is now {'active' if user.active else 'disabled'}.", "success")
    return redirect(url_for("admin.users"))


# --------------------------------------------------------------------------- units
@bp.route("/units")
def units():
    colleges = Unit.query.filter_by(unit_type="college").order_by(Unit.code).all()
    orphans = Unit.query.filter(Unit.unit_type != "college", Unit.parent_id.is_(None)).all()
    return render_template("admin/units.html", colleges=colleges, orphans=orphans,
                           parents=Unit.query.filter(Unit.unit_type != "course").order_by(Unit.code).all())


@bp.route("/units/new", methods=["POST"])
def unit_create():
    f = request.form
    code, name, unit_type = f.get("code", "").strip().upper(), f.get("name", "").strip(), f.get("unit_type")
    parent_id = f.get("parent_id", type=int)
    parent = db.session.get(Unit, parent_id) if parent_id else None
    expected_parent = {"college": None, "department": "college", "course": "department"}.get(unit_type, "x")
    if not code or not name or unit_type not in Unit.TYPES:
        flash("Code, name and type are required.", "error")
    elif Unit.query.filter_by(code=code).first():
        flash(f"Unit code '{code}' already exists.", "error")
    elif (parent.unit_type if parent else None) != expected_parent:
        flash(f"A {unit_type} must be placed under a {expected_parent}." if expected_parent
              else "Colleges cannot have a parent unit.", "error")
    else:
        db.session.add(Unit(code=code, name=name, unit_type=unit_type, parent=parent))
        log_change("units", f"Added {unit_type} {code} — {name}")
        db.session.commit()
        flash(f"{unit_type.title()} {code} added.", "success")
    return redirect(url_for("admin.units"))


# --------------------------------------------------------------------------- feedback windows
@bp.route("/windows")
def windows():
    rows = FeedbackWindow.query.order_by(FeedbackWindow.start_date.desc()).all()
    counts = dict(db.session.query(Feedback.window_id, db.func.count(Feedback.id))
                  .group_by(Feedback.window_id).all())
    last = rows[0] if rows else None
    return render_template("admin/windows.html", windows=rows, counts=counts,
                           next_week=(last.week_number + 1) if last else 1)


@bp.route("/windows/new", methods=["POST"])
def window_create():
    f = request.form
    try:
        start = datetime.strptime(f["start_date"], "%Y-%m-%d").date()
        end = datetime.strptime(f["end_date"], "%Y-%m-%d").date()
        week = int(f["week_number"])
    except (KeyError, ValueError):
        flash("Please provide a week number, start date and end date.", "error")
        return redirect(url_for("admin.windows"))
    if end < start:
        flash("End date must be on or after the start date.", "error")
    else:
        label = f.get("label", "").strip() or f"Week {week}"
        db.session.add(FeedbackWindow(label=label, week_number=week, start_date=start, end_date=end))
        db.session.commit()
        flash(f"{label} scheduled.", "success")
    return redirect(url_for("admin.windows"))


@bp.route("/windows/<int:window_id>/<action>", methods=["POST"])
def window_action(window_id, action):
    window = db.get_or_404(FeedbackWindow, window_id)
    if action == "open":
        if FeedbackWindow.query.filter(FeedbackWindow.status == "open", FeedbackWindow.id != window.id).first():
            flash("Another window is already open. Close it first.", "error")
        elif window.status != "scheduled":
            flash("Only scheduled windows can be opened.", "error")
        else:
            window.status, window.opened_at = "open", now()
            db.session.commit()
            flash(f"{window.label} is now open for student feedback.", "success")
    elif action == "close":
        if window.status != "open":
            flash("Only an open window can be closed.", "error")
        else:
            window.status, window.closed_at = "closed", now()
            db.session.commit()
            flash(f"{window.label} closed. Run processing to classify and report.", "success")
    elif action in ("process", "reprocess"):
        if window.status in ("scheduled",):
            flash("This window has not been opened yet.", "error")
        else:
            result = process_window(window, current_user, reclassify=(action == "reprocess"))
            flash(f"{window.label} processed: {result['classified']} comments classified, "
                  f"{result['alerts']} alert(s) raised, weekly report generated.", "success")
    elif action == "report":
        if window.status != "processed":
            flash("Process the window before generating its report.", "error")
        else:
            generate_report(window, current_user)
            db.session.commit()
            flash("Weekly report regenerated.", "success")
    elif action == "delete":
        if window.feedback.count():
            flash("Windows that already contain feedback cannot be deleted.", "error")
        else:
            db.session.delete(window)
            db.session.commit()
            flash("Window deleted.", "success")
    else:
        abort(404)
    return redirect(url_for("admin.windows"))


# --------------------------------------------------------------------------- settings & governance
@bp.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        reason = request.form.get("reason", "").strip()
        changed = []
        try:
            for key in DEFAULTS:
                new = request.form.get(key, "").strip()
                if new and str(get_setting(key)) != new:
                    old = get_setting(key)
                    set_setting(key, new)
                    changed.append(f"{key}: {old} → {new}")
        except ValueError:
            db.session.rollback()
            flash("Please enter valid numbers.", "error")
            return redirect(url_for("admin.settings"))
        if changed:
            log_change("settings", "; ".join(changed), reason or None)
            db.session.commit()
            flash("Settings saved and recorded in the change log.", "success")
        else:
            flash("No changes.", "info")
        return redirect(url_for("admin.settings"))
    return render_template("admin/settings.html", settings=all_settings())


@bp.route("/changelog", methods=["GET", "POST"])
def changelog():
    if request.method == "POST":
        category = request.form.get("category")
        description = request.form.get("description", "").strip()
        if category not in ChangeLog.CATEGORIES or not description:
            flash("Category and description are required.", "error")
        else:
            log_change(category, description, request.form.get("reason", "").strip() or None)
            db.session.commit()
            flash("Change recorded.", "success")
        return redirect(url_for("admin.changelog"))
    entries = ChangeLog.query.order_by(ChangeLog.created_at.desc()).limit(200).all()
    return render_template("admin/changelog.html", entries=entries, categories=ChangeLog.CATEGORIES)


@bp.route("/access-logs")
def access_logs():
    logs = AccessLog.query.order_by(AccessLog.created_at.desc()).limit(300).all()
    return render_template("admin/access_logs.html", logs=logs)


# --------------------------------------------------------------------------- analyzer lab
def _read_labeled_csv(file_storage):
    """CSV with columns: text,label  (optional: annotator_2 for Cohen's kappa)."""
    content = file_storage.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content))
    rows = [r for r in reader if (r.get("text") or "").strip() and (r.get("label") or "").strip()]
    texts = [r["text"].strip() for r in rows]
    labels = [r["label"].strip().lower() for r in rows]
    second = [(r.get("annotator_2") or "").strip().lower() for r in rows]
    return texts, labels, second


@bp.route("/analyzer", methods=["GET", "POST"])
def analyzer():
    sample, result, evaluation = request.form.get("text", ""), None, None
    if request.method == "POST":
        if request.form.get("mode") == "evaluate":
            upload = request.files.get("dataset")
            if not upload or not upload.filename:
                flash("Choose a labeled CSV file (columns: text,label).", "error")
            else:
                try:
                    texts, labels, second = _read_labeled_csv(upload)
                except (UnicodeDecodeError, csv.Error):
                    texts = []
                if not texts:
                    flash("No usable rows found. The CSV needs 'text' and 'label' columns.", "error")
                else:
                    evaluation = {
                        "n": len(texts),
                        "reports": [evaluate(texts, labels, a) for a in (get_primary_analyzer(), wordcount_analyzer)],
                        "kappa": cohens_kappa(labels, second) if any(second) else None,
                    }
        elif sample.strip():
            result = analyze(sample)
            result["baseline"] = wordcount_analyzer.score(sample).label
    return render_template("admin/analyzer.html", sample=sample, result=result, evaluation=evaluation,
                           engine=engine_status())
