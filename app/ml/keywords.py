"""Keyword mining: term frequency, bigrams and TF-IDF in plain Python."""
import math
from collections import Counter

from app.ml.preprocess import content_tokens, ngrams, tokenize


def extract_keywords(text=None, tokens=None, limit=6):
    """Most frequent meaningful words and bigrams of a single comment."""
    tokens = tokens if tokens is not None else tokenize(text or "")
    words = content_tokens(tokens)
    counts = Counter(words)
    counts.update(b for b in ngrams(words, 2) if b.split()[0] != b.split()[1])
    first_seen = {term: i for i, term in reversed(list(enumerate(words + ngrams(words, 2))))}
    ranked = sorted(counts, key=lambda t: (-counts[t], -len(t.split()), first_seen.get(t, 0)))
    return ranked[:limit]


def top_terms(keyword_lists, limit=10, min_count=2):
    """Document frequency: in how many comments does each term appear?"""
    df = Counter()
    for terms in keyword_lists:
        df.update(set(terms))
    return [(term, n) for term, n in df.most_common() if n >= min_count][:limit]


def tfidf_by_group(groups, limit=10):
    """Distinctive terms per group. groups = {name: [text, ...]} -> {name: [(term, score)]}."""
    group_terms = {name: Counter(t for text in texts for t in content_tokens(tokenize(text)))
                   for name, texts in groups.items()}
    n_groups = len(group_terms) or 1
    df = Counter()
    for counts in group_terms.values():
        df.update(counts.keys())
    result = {}
    for name, counts in group_terms.items():
        total = sum(counts.values()) or 1
        scored = {t: (c / total) * (math.log((1 + n_groups) / (1 + df[t])) + 1) for t, c in counts.items()}
        result[name] = sorted(((t, round(s, 4)) for t, s in scored.items()), key=lambda x: -x[1])[:limit]
    return result
