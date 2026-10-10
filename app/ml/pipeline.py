"""Runs the full text-mining pipeline: sentiment, topic grouping and keyword extraction."""
from app.ml.keywords import extract_keywords
from app.ml.preprocess import tokenize
from app.ml.sentiment import lexicon_analyzer
from app.ml.topics import classify_topic

ANALYZER_VERSION = "lexicon-rules-1.0"


def get_primary_analyzer():
    """The lightweight lexicon + rules model. Swap it here to plug in another analyzer."""
    return lexicon_analyzer


def engine_status():
    return {"name": get_primary_analyzer().name, "version": ANALYZER_VERSION}


def analyzer_version():
    return ANALYZER_VERSION


def analyze(text):
    tokens = tokenize(text)
    sentiment = get_primary_analyzer().score(text)
    topic, topic_hits = classify_topic(tokens=tokens)
    return {
        "label": sentiment.label,
        "score": sentiment.compound,
        "confidence": sentiment.confidence,
        "positive_score": sentiment.positive,
        "negative_score": sentiment.negative,
        "matches": sentiment.matches,
        "topic": topic,
        "topics": topic_hits,
        "keywords": extract_keywords(tokens=tokens),
        "tokens": tokens,
        "analyzer_version": ANALYZER_VERSION,
    }


def analyze_batch(texts):
    return [analyze(t) for t in texts]
