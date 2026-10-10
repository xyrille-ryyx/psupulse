"""Alerting Module views: flagged concerns and their follow-up ("action taken and tracked")."""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from app.extensions import db
from app.models import Alert
from app.utils.decorators import MANAGERS, STAFF, roles_required
from app.utils.scope import can_see_unit, visible_unit_ids

bp = Blueprint("alerts", __name__, url_prefix="/alerts")


@bp.route("/")
@roles_required(*STAFF)
def index():
    status = request.args.get("status", "active")
    query = Alert.query
    allowed = visible_unit_ids(current_user)
    if allowed is not None:
        query = query.filter(Alert.unit_id.in_(allowed or [-1]))
    if status == "active":
        query = query.filter(Alert.status != "resolved")
    elif status in Alert.STATUSES:
        query = query.filter(Alert.status == status)
    alerts = query.order_by(Alert.created_at.desc(), Alert.id.desc()).all()
    return render_template("alerts/index.html", alerts=alerts, status=status,
                           can_manage=current_user.role in MANAGERS)


@bp.route("/<int:alert_id>", methods=["POST"])
@roles_required(*MANAGERS)
def update(alert_id):
    alert = db.get_or_404(Alert, alert_id)
    if not can_see_unit(current_user, alert.unit_id):
        abort(403)
    status = request.form.get("status")
    if status not in Alert.STATUSES:
        abort(400)
    notes = (request.form.get("action_notes") or "").strip()
    if status == "resolved" and not notes:
        flash("Please describe the action taken before resolving the alert.", "error")
        return redirect(url_for("alerts.index"))
    alert.status = status
    alert.action_notes = notes or alert.action_notes
    alert.public_note = bool(request.form.get("public_note")) and status == "resolved"
    alert.handled_by_id = current_user.id
    db.session.commit()
    flash("Alert updated.", "success")
    return redirect(url_for("alerts.index", status=request.form.get("return_status", "active")))
