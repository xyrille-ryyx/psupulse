"""Lightweight rule-based sentiment model.

LexiconSentimentAnalyzer (primary) - for every token:
  1. merge known multi-word phrases ("walang kwenta", "waste of time")
  2. look up valence in the lexicon (with Filipino affix and English suffix fallbacks)
  3. add intensity from boosters within the 3 previous tokens ("sobrang", "very")
  4. flip and dampen when a negator is within the 3 previous tokens ("hindi", "not")
  5. weight the clause after a contrast word higher ("..., pero mainit")
  6. add emphasis for exclamation marks
  7. squash the sum into a compound score between -1 and 1

WordCountBaseline simply counts positive vs negative words, so the evaluation can
show how much the rules add.
"""
import math
from dataclasses import dataclass, field

from app.ml import lexicon as L
from app.ml.preprocess import collapse_doubles, normalize, tokenize

POSITIVE_THRESHOLD = 0.05
NEGATIVE_THRESHOLD = -0.05
_MAX_PHRASE_LEN = max(len(p.split()) for p in L.PHRASES)


@dataclass
class SentimentScore:
    label: str
    compound: float
    confidence: float
    positive: float = 0.0
    negative: float = 0.0
    matches: list = field(default_factory=list)  # [(term, adjusted valence)]


def label_for(compound):
    if compound >= POSITIVE_THRESHOLD:
        return "positive"
    if compound <= NEGATIVE_THRESHOLD:
        return "negative"
    return "neutral"


def merge_phrases(tokens):
    out, i = [], 0
    while i < len(tokens):
        for n in range(min(_MAX_PHRASE_LEN, len(tokens) - i), 1, -1):
            candidate = " ".join(tokens[i:i + n])
            if candidate in L.PHRASES:
                out.append(candidate.replace(" ", "_"))
                i += n
                break
        else:
            out.append(tokens[i])
            i += 1
    return out


def _canon(token):
    return collapse_doubles(token) if token not in L.VALENCE else token


def lookup(token):
    """Return (valence, extra_intensity) for a token, or (0, 0) if it is not a sentiment word."""
    if "_" in token:
        return L.PHRASES.get(token.replace("_", " "), 0.0), 0.0
    if token in L.EMOTICONS:
        return L.EMOTICONS[token], 0.0
    if token in L.VALENCE:
        return L.VALENCE[token], 0.0

    for prefix, boost in L.TL_PREFIXES:
        if token.startswith(prefix) and len(token) > len(prefix) + 2:
            root = token[len(prefix):]
            for candidate in (root, "ma" + root):
                if candidate in L.VALENCE:
                    return L.VALENCE[candidate], boost

    candidates = []
    if token.endswith("ng") and len(token) > 4:          # Filipino linker: "magandang"
        candidates.append(token[:-2])
    if token.endswith("ly") and len(token) > 4:          # "clearly" -> "clear"
        candidates.append(token[:-2])
    if token.endswith("s") and len(token) > 3:           # plurals
        candidates.append(token[:-1])
    candidates.append(collapse_doubles(token))           # "soo" -> "so"
    for candidate in candidates:
        if candidate in L.VALENCE:
            return L.VALENCE[candidate], 0.0
    return 0.0, 0.0


def _is_modifier(token):
    canon = _canon(token)
    return canon in L.NEGATORS or canon in L.BOOSTERS or canon in L.CONTRAST


class LexiconSentimentAnalyzer:
    name = "Lexicon + rules (primary)"

    def score(self, text):
        normalized = normalize(text)
        tokens = merge_phrases(tokenize(normalized, normalized=True))
        valences = [0.0] * len(tokens)

        for i, token in enumerate(tokens):
            if _is_modifier(token):
                continue
            value, affix_boost = lookup(token)
            if not value:
                continue
            value += math.copysign(affix_boost, value)

            for distance in range(1, 4):
                j = i - distance
                if j < 0:
                    break
                boost = L.BOOSTERS.get(_canon(tokens[j]))
                if boost:
                    scaled = boost * (1.0, 0.95, 0.9)[distance - 1]
                    value += scaled if value > 0 else -scaled  # boosters grow, diminishers shrink

            scope = tokens[max(0, i - L.NEGATION_SCOPE):i]
            if any(_canon(t) in L.NEGATORS for t in scope):
                value *= L.NEGATION_SCALAR
            valences[i] = value

        for k, token in enumerate(tokens):
            if token in L.CONTRAST:
                valences = [
                    v * (L.CONTRAST_BEFORE if idx < k else L.CONTRAST_AFTER if idx > k else 1)
                    for idx, v in enumerate(valences)
                ]
                break

        total = sum(valences)
        if total:
            bangs = min(normalized.count("!"), L.MAX_EXCLAMATIONS)
            total += math.copysign(bangs * L.EXCLAMATION_BOOST, total)
        compound = total / math.sqrt(total * total + L.NORMALIZATION_ALPHA) if total else 0.0
        compound = max(-1.0, min(1.0, compound))
        label = label_for(compound)

        if label == "neutral":
            # 1.0 when nothing sentiment-bearing was found, ~0.5 near the thresholds
            confidence = 1.0 - (abs(compound) / POSITIVE_THRESHOLD) * 0.5
        else:
            confidence = min(1.0, 0.5 + abs(compound) / 2)

        return SentimentScore(
            label=label,
            compound=round(compound, 4),
            confidence=round(confidence, 3),
            positive=round(sum(v for v in valences if v > 0), 3),
            negative=round(abs(sum(v for v in valences if v < 0)), 3),
            matches=[(tokens[i].replace("_", " "), round(v, 3)) for i, v in enumerate(valences) if v],
        )


class WordCountBaseline:
    name = "Word count (baseline)"

    def score(self, text):
        tokens = tokenize(text)
        pos = sum(1 for t in tokens if L.VALENCE.get(t, 0) > 0)
        neg = sum(1 for t in tokens if L.VALENCE.get(t, 0) < 0)
        total = pos + neg
        compound = (pos - neg) / total if total else 0.0
        label = "positive" if pos > neg else "negative" if neg > pos else "neutral"
        return SentimentScore(label=label, compound=round(compound, 4),
                              confidence=round(abs(compound), 3), positive=pos, negative=neg)


lexicon_analyzer = LexiconSentimentAnalyzer()
wordcount_analyzer = WordCountBaseline()
