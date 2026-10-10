"""Lightweight text mining and sentiment analysis in plain Python (no heavy ML libraries).

    sentiment   -> lexicon + rules model (primary) and a word-count baseline
    lexicon     -> sentiment word lists, negators, intensifiers, phrases (English/Filipino)
    preprocess  -> normalize and tokenize raw comments
    stopwords   -> English + Filipino stopword lists
    topics      -> keyword/rule-based concern categories
    keywords    -> term frequency, n-grams, TF-IDF for recurring terms
    evaluation  -> accuracy, precision, recall, F1, confusion matrix, kappa
    pipeline    -> runs everything for one comment or a batch
"""
from app.ml.pipeline import analyze, analyze_batch, analyzer_version, engine_status

__all__ = ["analyze", "analyze_batch", "analyzer_version", "engine_status"]
