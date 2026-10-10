"""Load demo data: units, users, six weekly windows and synthetic student comments.

The comments are SYNTHETIC (written for testing, in English, Filipino and Taglish).
Five past weeks are processed; the current week is left open for live submissions.
A facilities problem is planted in IT 311 in week 4 so alerts can be demonstrated.

Usage:  python scripts/seed_data.py          (expects empty tables; run init_db.py first)
        python scripts/seed_data.py --reset  (drops and recreates all tables first)

Every demo account uses the password:  password123
"""
import argparse
import random
from datetime import date, timedelta

import _bootstrap  # noqa: F401

from app import create_app
from app.extensions import db
from app.ml.pipeline import get_primary_analyzer
from app.models import Feedback, FeedbackWindow, SubmissionToken, Unit, User
from app.models.base import now
from app.utils.audit import log_change
from app.utils.privacy import scrub_pii, submission_token
from app.utils.processing import process_window

DEMO_PASSWORD = "password123"
rng = random.Random(2026)

UNITS = [
    ("CCS", "College of Computing Studies", "college", None),
    ("DIT", "Department of Information Technology", "department", "CCS"),
    ("DCS", "Department of Computer Science", "department", "CCS"),
    ("IT 311", "Systems Integration and Architecture", "course", "DIT"),
    ("IT 312", "Information Assurance and Security", "course", "DIT"),
    ("IT 313", "Web Systems and Technologies", "course", "DIT"),
    ("CS 321", "Automata Theory and Formal Languages", "course", "DCS"),
    ("CS 322", "Software Engineering", "course", "DCS"),
    ("CAS", "College of Arts and Sciences", "college", None),
    ("DENG", "Department of English", "department", "CAS"),
    ("DMATH", "Department of Mathematics", "department", "CAS"),
    ("ENG 101", "Purposive Communication", "course", "DENG"),
    ("MATH 101", "Mathematics in the Modern World", "course", "DMATH"),
]

STAFF = [
    ("osa.reyes", "Maria Reyes", "student_affairs", []),
    ("head.it", "Engr. Jose Santos", "dept_head", ["DIT"]),
    ("head.cs", "Dr. Ana Villanueva", "dept_head", ["DCS"]),
    ("faculty.cruz", "Prof. Mark Cruz", "faculty", ["IT 311", "IT 313"]),
    ("faculty.garcia", "Prof. Liza Garcia", "faculty", ["IT 312", "CS 322"]),
    ("faculty.lim", "Prof. Ramon Lim", "faculty", ["CS 321", "ENG 101", "MATH 101"]),
]

# (topic hint, sentiment) -> comments. Sentiment hint is only for generating a realistic mix;
# the analyzer decides the actual label.
COMMENTS = {
    "positive": [
        "The teacher explains the lessons very clearly and gives good examples.",
        "Napakagaling magturo ni sir, malinaw lahat ng discussion.",
        "I really enjoyed the activity this week, very engaging and fun!",
        "Ang bait ni maam at very approachable kapag may tanong kami.",
        "Thank you for the extra consultation hours, super helpful po.",
        "The new lab computers are fast and the wifi is finally stable.",
        "Maayos at malinis yung classroom ngayon, salamat sa maintenance.",
        "Enrollment was smooth this time, the online portal works well.",
        "Sobrang helpful ng guidance office, they listened to my concerns.",
        "Our professor is well prepared and the slides are organized.",
        "Ang saya ng group project, natuto kami ng marami.",
        "The registrar released our documents on time, great service.",
        "Keep up the good work, the module is very informative.",
        "Ganda ng lesson today, madali lang intindihin :)",
        "I appreciate that sir gives feedback on our outputs quickly.",
        "The library is quiet and comfortable for studying.",
        "Security guards are friendly and the campus feels safe at night.",
        "The quiz was fair and covered what we discussed.",
    ],
    "negative": [
        "Sobrang init sa room, sira pa yung aircon.",
        "The wifi is very slow, we cannot open the LMS during class.",
        "Too many requirements this week, all deadlines are on the same day.",
        "Hindi malinaw yung instructions sa project, nakakalito.",
        "The professor is always late and the class starts 30 minutes after.",
        "Ang haba ng pila sa registrar, nakakainis at sobrang bagal.",
        "The CR on the third floor is dirty and has no water.",
        "Grabe yung workload, nakakapagod na and we are so stressed.",
        "The lecture was boring and the topic was confusing.",
        "Walang kwenta yung projector, hindi gumagana every meeting.",
        "The portal keeps crashing during enrollment, very frustrating.",
        "There are no lights near the back gate, it feels unsafe at night.",
        "Medyo masungit si maam kapag nagtatanong kami.",
        "The quiz was too hard and covered topics we never discussed.",
        "Pangit ng upuan sa lab, sira-sira na.",
        "Late na naman ma-release yung grades, no feedback on our outputs.",
    ],
    "neutral": [
        "We had a quiz on Wednesday and a lecture on Friday.",
        "Sana may recorded lecture para ma-review namin ulit.",
        "The class discussed chapter 4 this week.",
        "Please post the schedule of the midterm exam.",
        "May activity kami sa lab next week.",
        "Can we have the slides uploaded to the LMS?",
        "The enrollment for next semester starts in two weeks.",
        "We used the library for our research this week.",
        "Online class po tayo sa Thursday ayon kay sir.",
        "The project proposal is due next Monday.",
    ],
}

FACILITY_SPIKE = [
    "Sobrang init sa room, sira pa yung aircon. Hindi kami makapag-focus.",
    "The aircon in our room is broken again, it is very hot and uncomfortable.",
    "Mainit at masikip sa classroom, walang electric fan na gumagana.",
    "The room is so hot, we are sweating the whole class. Please fix the aircon.",
    "Hindi gumagana yung aircon for two weeks na, nakakainis.",
    "Classroom is unbearable because of the heat, broken aircon and no fans.",
]


def sentiment_mix(course_code, week):
    """Per-course weekly probabilities (positive, negative, neutral)."""
    base = {"IT 311": (0.55, 0.25, 0.20), "IT 312": (0.50, 0.25, 0.25), "IT 313": (0.60, 0.20, 0.20),
            "CS 321": (0.40, 0.35, 0.25), "CS 322": (0.55, 0.25, 0.20), "ENG 101": (0.60, 0.15, 0.25),
            "MATH 101": (0.45, 0.30, 0.25)}[course_code]
    if course_code == "CS 321" and week >= 3:          # workload builds up toward midterms
        base = (0.30, 0.50, 0.20)
    return base


def build_units():
    by_code = {}
    for code, name, unit_type, parent in UNITS:
        unit = Unit(code=code, name=name, unit_type=unit_type, parent=by_code.get(parent))
        db.session.add(unit)
        by_code[code] = unit
    db.session.flush()
    return by_code


def make_user(username, full_name, role, units):
    user = User(username=username, full_name=full_name, role=role,
                email=f"{username}@example.edu.ph")
    user.set_password(DEMO_PASSWORD)
    user.units = units
    db.session.add(user)
    return user


def build_users(units):
    make_user("admin", "System Administrator", "admin", []).set_password("admin12345")
    for username, name, role, codes in STAFF:
        make_user(username, name, role, [units[c] for c in codes])

    courses = [u for u in units.values() if u.unit_type == "course" and u.code != "MATH 101"]
    students = []
    for i in range(1, 46):
        picks = rng.sample(courses, 3)
        if i <= 4:                                      # small class to demo the privacy threshold
            picks.append(units["MATH 101"])
        students.append(make_user(f"student{i:02d}", f"Student {i:02d}", "student", picks))
    db.session.flush()
    return students


def pick_comment(course, week, mix):
    if course.code == "IT 311" and week == 4 and rng.random() < 0.6:
        return rng.choice(FACILITY_SPIKE)
    roll, cumulative = rng.random(), 0.0
    for sentiment, p in zip(("positive", "negative", "neutral"), mix):
        cumulative += p
        if roll <= cumulative:
            return rng.choice(COMMENTS[sentiment])
    return rng.choice(COMMENTS["neutral"])


def build_windows(students):
    this_monday = date.today() - timedelta(days=date.today().weekday())
    windows = []
    for week in range(1, 7):
        start = this_monday - timedelta(weeks=6 - week)
        window = FeedbackWindow(label=f"Week {week}", week_number=week, start_date=start,
                                end_date=start + timedelta(days=6),
                                status="open" if week == 6 else "closed", opened_at=now())
        db.session.add(window)
        db.session.flush()

        participation = 0.25 if week == 6 else 0.8
        for student in students:
            for course in student.units:
                if rng.random() > participation:
                    continue
                text, redacted = scrub_pii(pick_comment(course, week, sentiment_mix(course.code, week)))
                day = start + timedelta(days=rng.randint(0, 6))
                db.session.add(SubmissionToken(window_id=window.id, created_on=day,
                                               token_hash=submission_token(student.id, window.id, course.id)))
                db.session.add(Feedback(window_id=window.id, unit_id=course.id, text=text,
                                        pii_redacted=redacted, submitted_on=min(day, date.today())))
        windows.append(window)
    db.session.flush()
    return windows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="drop and recreate all tables first")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        if args.reset:
            db.drop_all()
        db.create_all()
        if Unit.query.first() or User.query.filter(User.username != "admin").first():
            raise SystemExit("Data already exists. Use --reset to wipe it and reseed.")
        User.query.filter_by(username="admin").delete()

        units = build_units()
        students = build_users(units)
        windows = build_windows(students)
        log_change("analyzer", f"Initial sentiment engine: {get_primary_analyzer().name}; 7 topic categories",
                   "Prototype baseline configuration")
        db.session.commit()

        admin = User.query.filter_by(username="admin").first()
        for window in windows[:-1]:
            result = process_window(window, admin)
            print(f"{window.label}: {result['classified']} comments, {result['alerts']} alert(s)")

        print("\nDemo data loaded. Sign in with:")
        print("  admin / admin12345            (system administrator)")
        print(f"  osa.reyes / {DEMO_PASSWORD}      (student affairs)")
        print(f"  head.it / {DEMO_PASSWORD}        (department head, IT)")
        print(f"  faculty.cruz / {DEMO_PASSWORD}   (faculty, IT 311 & IT 313)")
        print(f"  student01 / {DEMO_PASSWORD}      (student — Week 6 is open)")


if __name__ == "__main__":
    main()
