"""Anonymization helpers (Data Privacy Act of 2012 / RA 10173 design requirement)."""
import hashlib
import hmac
import re

from flask import current_app

_PII_PATTERNS = [
    (re.compile(r"(https?://\S+|www\.\S+)", re.IGNORECASE), "[link]"),
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"), "[email]"),
    (re.compile(r"(?:\+?63|0)9\d{2}[\s-]?\d{3}[\s-]?\d{4}\b"), "[phone]"),
    (re.compile(r"\b\d{2,4}-\d{4,6}\b"), "[id-number]"),       # e.g. 21-12345, 2023-00123
    (re.compile(r"\b\d{7,12}\b"), "[id-number]"),
    (re.compile(
        r"\b(my name is|i am called|ako si|pangalan ko ay|ang pangalan ko ay)\s+"
        r"[A-Za-zÑñ]+(?:\s+[A-Z][a-zñ]+){0,2}",
        re.IGNORECASE,
    ), r"\1 [name]"),
]


def scrub_pii(text):
    """Mask obvious personal identifiers. Returns (clean_text, was_redacted)."""
    cleaned = text
    for pattern, replacement in _PII_PATTERNS:
        cleaned = pattern.sub(replacement, cleaned)
    return cleaned, cleaned != text


def submission_token(user_id, window_id, unit_id):
    """One-way HMAC used only to detect a duplicate submission for (student, week, course).
    It is never stored next to the comment, so comments cannot be traced to a student."""
    key = current_app.config["TOKEN_SECRET"].encode()
    message = f"{user_id}:{window_id}:{unit_id}".encode()
    return hmac.new(key, message, hashlib.sha256).hexdigest()
