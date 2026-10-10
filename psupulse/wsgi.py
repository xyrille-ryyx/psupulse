"""Production WSGI entry point.

Run from the project folder (the one containing run.py), for example:
    waitress-serve --port=8000 psupulse.wsgi:app
"""
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import create_app  # noqa: E402

app = create_app(os.getenv("APP_ENV", "production"))
