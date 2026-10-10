"""Weekly reports: print-friendly HTML and CSV export, filtered to the viewer's scope."""
from flask import Blueprint, Response, abort, render_template
from flask_login import current_user

from app.extensions import db
from app.models import FeedbackWindow, Report
from app.utils.audit import log_access
from app.utils.decorators import STAFF, roles_required
from app.utils.reports import report_csv
from app.utils.scope import can_see_overall, visible_unit_ids

bp = Blueprint("reports", __name__, url_prefix="/reports")


def _scoped(summary):
    """Copy of the summary with only the rows/alerts this user may see."""
    allowed = visible_unit_ids(current_user)
    if allowed is None:
        return summary
    scoped = dict(summary)
    scoped["overall"] = None
    scoped["highlights"] = []
    scoped["units"] = [r for r in summary["units"] if r["unit_id"] in allowed]
    scoped["alerts"] = [a for a in summary["alerts"] if a["unit_id"] in allowed]
    return scoped


@bp.route("/")
@roles_required(*STAFF)
def index():
    reports = (Report.query.join(FeedbackWindow, Report.window_id == FeedbackWindow.id)
               .order_by(FeedbackWindow.start_date.desc()).all())
    return render_template("reports/index.html", reports=reports)


@bp.route("/<int:report_id>")
@roles_required(*STAFF)
def view(report_id):
    report = db.get_or_404(Report, report_id)
    summary = _scoped(report.summary)
    log_access("view_report", f"report={report.id} ({report.window.label})")
    return render_template("reports/view.html", report=report, s=summary,
                           show_overall=can_see_overall(current_user))


@bp.route("/<int:report_id>/csv")
@roles_required(*STAFF)
def export_csv(report_id):
    report = db.get_or_404(Report, report_id)
    summary = _scoped(report.summary)
    if not summary["units"]:
        abort(403)
    log_access("download_report_csv", f"report={report.id} ({report.window.label})")
    filename = f"psu-pulse-week-{report.window.week_number}-{report.window.start_date:%Y%m%d}.csv"
    return Response(
        "﻿" + report_csv(summary, summary["units"]),  # BOM so Excel opens UTF-8 correctly
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
