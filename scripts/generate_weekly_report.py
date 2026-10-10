"""Close the open feedback window, classify, aggregate, raise alerts and generate the report.

Run it manually, or schedule it (Windows Task Scheduler / cron / APScheduler) for the end of each week.

Usage:  python scripts/generate_weekly_report.py               process the open (or latest closed) window
        python scripts/generate_weekly_report.py --window 7     process a specific window id
        python scripts/generate_weekly_report.py --reprocess    re-run classification for a processed window
"""
import argparse

import _bootstrap  # noqa: F401

from app import create_app
from app.extensions import db
from app.models import FeedbackWindow
from app.utils.processing import process_window


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--window", type=int, help="feedback window id")
    parser.add_argument("--reprocess", action="store_true")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        if args.window:
            window = db.session.get(FeedbackWindow, args.window)
        else:
            window = (FeedbackWindow.query.filter(FeedbackWindow.status.in_(["open", "closed"]))
                      .order_by(FeedbackWindow.start_date).first())
        if window is None:
            print("No open or closed window to process.")
            return
        result = process_window(window, reclassify=args.reprocess)
        print(f"{window.label}: {result['classified']} comments classified, "
              f"{result['alerts']} alert(s), report #{result['report_id']} generated.")


if __name__ == "__main__":
    main()
