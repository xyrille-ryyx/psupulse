"""End-to-end smoke test using Flask's test client (run after seed_data.py).

Signs in as each role, opens every main page, submits feedback, processes the open
window and checks role-based access. Prints PASS/FAIL per check.

Usage:  python scripts/smoke_test.py
"""
import sys

import _bootstrap  # noqa: F401

from app import create_app
from app.extensions import db
from app.models import Alert, FeedbackWindow, Report, Unit, User
from app.utils.privacy import submission_token

app = create_app()
app.config["WTF_CSRF_ENABLED"] = False
failures = 0


def check(name, condition):
    global failures
    print(f"{'PASS' if condition else 'FAIL'}  {name}")
    failures += 0 if condition else 1


def login(client, username, password="password123"):
    client.post("/auth/logout")
    return client.post("/auth/login", data={"username": username, "password": password}, follow_redirects=True)


with app.app_context():
    c = app.test_client()
    check("login page renders", c.get("/auth/login").status_code == 200)
    check("bad password rejected", b"Incorrect" in login(c, "admin", "wrong").data)

    # ---- student
    r = login(c, "student05")
    check("student lands on feedback form", b"Weekly feedback" in r.data)
    student = User.query.filter_by(username="student05").first()
    window = FeedbackWindow.query.filter_by(status="open").first()
    sent = {t.token_hash for t in window.tokens}
    course = next((u for u in student.units
                   if submission_token(student.id, window.id, u.id) not in sent), student.units[0])
    before = window.feedback.count()
    text = "Napakagaling ni sir pero sobrang init sa room. My name is Juan Dela Cruz, 09171234567."
    r = c.post("/feedback/", data={"unit_id": course.id, "comment": text}, follow_redirects=True)
    already = b"already sent" in r.data
    check("feedback accepted (or already sent)", b"submitted anonymously" in r.data or already)
    if not already:
        fb = window.feedback.order_by(None).all()[-1]
        check("PII scrubbed", "Juan" not in fb.text and "0917" not in fb.text and fb.pii_redacted)
        check("feedback stores no author", not hasattr(fb, "user_id"))
        r = c.post("/feedback/", data={"unit_id": course.id, "comment": "Second try for the same course."},
                   follow_redirects=True)
        check("duplicate submission blocked", b"already sent" in r.data and window.feedback.count() == before + 1)
    check("student blocked from dashboard", c.get("/dashboard/").status_code == 403)
    check("student blocked from admin", c.get("/admin/").status_code == 403)

    # ---- faculty
    login(c, "faculty.cruz")
    r = c.get("/dashboard/")
    check("faculty dashboard renders", r.status_code == 200 and b"trend-chart" in r.data)
    other = Unit.query.filter_by(code="CS 321").first()
    check("faculty cannot view other course", c.get(f"/dashboard/?unit={other.id}").status_code == 403)
    check("faculty cannot view university-wide", c.get("/dashboard/?unit=all").status_code == 403)
    check("faculty comments page", c.get("/dashboard/comments").status_code == 200)
    rep = Report.query.first()
    r = c.get(f"/reports/{rep.id}")
    check("faculty report is scoped", r.status_code == 200 and b"CS 321" not in r.data)

    # ---- department head
    login(c, "head.it")
    r = c.get("/dashboard/")
    check("dept head dashboard (department view)", r.status_code == 200 and b"Information Technology" in r.data)
    check("dept head csv export", c.get(f"/reports/{rep.id}/csv").status_code == 200)
    alert = Alert.query.join(Unit, Alert.unit_id == Unit.id).filter(Unit.code.like("IT%")).first()
    if alert:
        r = c.post(f"/alerts/{alert.id}", data={"status": "resolved", "action_notes": "Aircon repaired by facilities office.",
                                                "public_note": "1"}, follow_redirects=True)
        check("dept head resolves alert", b"Alert updated" in r.data)

    # ---- student affairs
    login(c, "osa.reyes")
    for path in ("/dashboard/?unit=all", "/dashboard/comments?unit=all&sentiment=negative", "/reports/",
                 f"/reports/{rep.id}", "/alerts/", "/alerts/?status=all"):
        check(f"student affairs GET {path}", c.get(path).status_code == 200)
    small = Unit.query.filter_by(code="MATH 101").first()
    r = c.get(f"/dashboard/?unit={small.id}")
    check("small group suppressed", b"no student can be identified" in r.data)

    # ---- admin
    login(c, "admin", "admin12345")
    for path in ("/admin/", "/admin/users", "/admin/units", "/admin/windows", "/admin/settings",
                 "/admin/changelog", "/admin/access-logs", "/admin/analyzer", f"/admin/users/{student.id}"):
        check(f"admin GET {path}", c.get(path).status_code == 200)
    r = c.post("/admin/analyzer", data={"mode": "test", "text": "Hindi maganda yung wifi, sobrang bagal!"})
    check("analyzer lab classifies", b"Negative" in r.data)
    with open(_bootstrap.PROJECT_ROOT + "/database/sample_labeled_feedback.csv", "rb") as fh:
        r = c.post("/admin/analyzer", data={"mode": "evaluate", "dataset": (fh, "labels.csv")},
                   content_type="multipart/form-data")
    check("analyzer evaluation runs", b"Confusion matrix" in r.data and b"Cohen" in r.data)
    r = c.post("/admin/settings", data={"min_group_size": "5", "negative_spike_threshold": "0.2",
                                        "high_negative_threshold": "0.5", "recurring_topic_min": "3",
                                        "reason": "smoke test"}, follow_redirects=True)
    check("settings change logged", b"change log" in r.data)
    r = c.post(f"/admin/windows/{window.id}/process", follow_redirects=True)
    check("open window processed", b"processed" in r.data and db.session.get(FeedbackWindow, window.id).status == "processed")

    # ---- student sees "you said, we did"
    login(c, "student05")
    r = c.get("/feedback/")
    check("student sees closed state", b"closed for now" in r.data)
    check("404 page", c.get("/nope").status_code == 404)

    print(f"\n{'All checks passed.' if not failures else f'{failures} check(s) failed.'}")
    sys.exit(1 if failures else 0)
