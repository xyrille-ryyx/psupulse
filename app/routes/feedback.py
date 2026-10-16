"""Feedback Collection Module: weekly, anonymous comments on enrolled courses and on
transactions made at university offices (cashier, registrar, ...)."""
from datetime import date

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user

from app.extensions import db
from app.models import Alert, Feedback, FeedbackWindow, SubmissionToken, Unit
from app.models.unit import COMMON_TRANSACTIONS
from app.utils.decorators import roles_required
from app.utils.privacy import scrub_pii, submission_token

bp = Blueprint("feedback", __name__, url_prefix="/feedback")


def _open_window():
    return (FeedbackWindow.query.filter_by(status="open")
            .order_by(FeedbackWindow.start_date.desc()).first())


def _courses():
    return [u for u in current_user.units if u.unit_type == "course"]


def _offices():
    return Unit.query.filter_by(unit_type="office").order_by(Unit.name).all()


def _already_submitted(window, unit_id):
    token = submission_token(current_user.id, window.id, unit_id)
    return SubmissionToken.query.filter_by(token_hash=token).first() is not None


@bp.route("/", methods=["GET", "POST"])
@roles_required("student")
def submit():
    window = _open_window()
    courses = _courses()
    offices = _offices()

    if request.method == "POST":
        if window is None:
            flash("The feedback window is closed. Please come back when the next week opens.", "error")
            return redirect(url_for("feedback.submit"))

        unit_id = request.form.get("unit_id", type=int)
        text = (request.form.get("comment") or "").strip()
        transaction = (request.form.get("transaction_type") or "").strip()
        min_c, max_c = current_app.config["FEEDBACK_MIN_CHARS"], current_app.config["FEEDBACK_MAX_CHARS"]
        is_office = unit_id in {o.id for o in offices}

        if unit_id not in {c.id for c in courses} and not is_office:
            flash("Please choose one of your enrolled courses or a university office.", "error")
        elif is_office and len(transaction) > 100:
            flash("Please keep the transaction description under 100 characters.", "error")
        elif not (min_c <= len(text) <= max_c):
            flash(f"Your comment should be between {min_c} and {max_c} characters.", "error")
        else:
            token = submission_token(current_user.id, window.id, unit_id)
            if SubmissionToken.query.filter_by(token_hash=token).first():
                flash(f"You already sent feedback for this {'office' if is_office else 'course'} this week. "
                      "Thank you!", "info")
            else:
                clean, redacted = scrub_pii(text)
                clean_tx, tx_redacted = scrub_pii(transaction) if is_office and transaction else (None, False)
                redacted = redacted or tx_redacted
                today = date.today()
                db.session.add(SubmissionToken(window_id=window.id, token_hash=token, created_on=today))
                db.session.add(Feedback(window_id=window.id, unit_id=unit_id, transaction_type=clean_tx,
                                        text=clean, pii_redacted=redacted, submitted_on=today))
                db.session.commit()
                msg = "Thank you! Your feedback was submitted anonymously."
                if redacted:
                    msg += " We removed personal details (such as names, numbers or emails) to protect your privacy."
                flash(msg, "success")
                return redirect(url_for("feedback.submit"))

    status = {u.id: _already_submitted(window, u.id) for u in [*courses, *offices]} if window else {}

    # "You said, we did": actions that staff chose to share publicly.
    my_unit_ids = set()
    for c in courses:
        my_unit_ids.update([c.id, *[a.id for a in c.ancestors()]])
    my_unit_ids.update(o.id for o in offices)
    actions = (Alert.query.filter(Alert.status == "resolved", Alert.public_note.is_(True),
                                  db.or_(Alert.unit_id.in_(my_unit_ids or [-1]), Alert.unit_id.is_(None)))
               .order_by(Alert.updated_at.desc()).limit(5).all())

    return render_template("feedback/submit.html", window=window, courses=courses, offices=offices,
                           transactions=COMMON_TRANSACTIONS, status=status,
                           actions=actions, max_chars=current_app.config["FEEDBACK_MAX_CHARS"],
                           min_chars=current_app.config["FEEDBACK_MIN_CHARS"])
