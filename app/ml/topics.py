"""Keyword/rule-based topic grouping.

Each comment is matched against keyword lists; the topic with the most hits wins.
Entries ending in '*' match as prefixes ("enrol*" -> enrolment, enrolled...).
Ties go to the topic listed first, so safety concerns are never hidden.
"""
from app.ml.preprocess import tokenize

GENERAL = "general"

TOPICS = {
    "safety": [
        "safety", "safe", "unsafe", "security", "guard", "guards", "cctv", "theft", "stolen",
        "steal*", "harass*", "bully*", "fight", "threat*", "danger*", "emergency", "fire",
        "earthquake", "drill", "dark", "gate", "ligtas", "delikado", "nakaw*", "magnanakaw",
        "takot", "nakakatakot", "baha", "flood*",
    ],
    "instruction": [
        "teach*", "instructor*", "professor*", "prof", "sir", "maam", "lecture*", "lesson*",
        "discussion*", "discuss*", "explain*", "module*", "class", "classes", "subject*",
        "topic*", "example*", "slides", "guro", "turo", "nagtuturo", "leksyon", "aralin",
        "paliwanag", "magturo", "learn*", "natuto", "natutunan", "pace", "attendance",
    ],
    "workload": [
        "workload", "deadline*", "requirement*", "assignment*", "homework", "project*",
        "exam*", "quiz*", "test", "tests", "grade*", "grading", "output*", "paper*",
        "report*", "toka", "overload*", "cramming", "gawain", "pressure", "stress*",
        "activit*", "submission*",
    ],
    "facilities": [
        "room*", "classroom*", "building*", "aircon", "fan", "fans", "chair*", "table*",
        "desk*", "cr", "toilet*", "restroom*", "bathroom*", "canteen", "library", "lab",
        "labs", "laboratory", "projector*", "light", "lights", "ceiling", "roof", "leak*",
        "water", "electricity", "brownout", "parking", "elevator", "stairs", "field", "gym",
        "hallway*", "silid", "upuan", "banyo", "kuryente", "tubig", "bubong", "kantina",
        "aklatan", "mainit", "init", "hot", "siksikan", "masikip",
    ],
    "technology": [
        "wifi", "internet", "signal", "connection", "network", "lms", "portal", "system",
        "website", "online", "computer*", "pc", "pcs", "laptop*", "email", "password",
        "login", "server", "app", "zoom", "gmeet", "lag", "laggy", "crash*", "offline",
    ],
    "enrollment_registrar": [
        "enrol*", "registrar", "registration", "register", "tor", "transcript*", "record*",
        "document*", "clearance", "form", "forms", "adding", "dropping", "drop", "shifting",
        "cashier", "tuition", "fee", "fees", "payment*", "pay", "bayad", "balance",
        "schedule", "sched", "units", "queue", "pila",
    ],
    "student_services": [
        "guidance", "counsel*", "clinic", "nurse", "doctor", "health", "mental", "scholar*",
        "org", "orgs", "organization*", "osa", "office", "staff", "service*", "assistance",
        "helpdesk", "event*", "sports", "food", "transport*", "shuttle", "dorm*", "id",
        "osas", "council",
    ],
}

TOPIC_LABELS = {
    "safety": "Safety & Security",
    "instruction": "Instruction & Teaching",
    "workload": "Workload & Assessment",
    "facilities": "Facilities",
    "technology": "Technology & Connectivity",
    "enrollment_registrar": "Enrollment & Registrar",
    "student_services": "Student Services",
    GENERAL: "General",
}

_EXACT = {topic: {k for k in words if not k.endswith("*")} for topic, words in TOPICS.items()}
_PREFIX = {topic: tuple(k[:-1] for k in words if k.endswith("*")) for topic, words in TOPICS.items()}


def match_topics(tokens):
    """Return {topic: hit_count} for every topic with at least one keyword hit."""
    hits = {}
    for topic in TOPICS:
        count = sum(1 for t in tokens if t in _EXACT[topic] or (_PREFIX[topic] and t.startswith(_PREFIX[topic])))
        if count:
            hits[topic] = count
    return hits


def classify_topic(text=None, tokens=None):
    tokens = tokens if tokens is not None else tokenize(text or "")
    hits = match_topics(tokens)
    if not hits:
        return GENERAL, {}
    order = list(TOPICS)
    primary = max(hits, key=lambda t: (hits[t], -order.index(t)))
    return primary, hits
