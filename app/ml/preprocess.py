"""Text cleaning and tokenization using only the standard library."""
import re
import unicodedata

from app.ml.stopwords import STOPWORDS

URL_RE = re.compile(r"(https?://\S+|www\.\S+)", re.IGNORECASE)
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
MENTION_RE = re.compile(r"@\w+")
REDACTION_RE = re.compile(r"\[(?:email|phone|id-number|name|link)\]")
REPEAT_RE = re.compile(r"([a-z])\1{2,}")          # "sooooo" -> "soo"
HYPHEN_RE = re.compile(r"(?<=[a-z])-(?=[a-z])")
WS_RE = re.compile(r"\s+")

EMOTICON = r"(?:<3|[:;=][\-']?[()dp/\\|])"
EMOJI = r"[☀-➿\U0001F300-\U0001FAFF]"
TOKEN_RE = re.compile(rf"{EMOTICON}|{EMOJI}|[a-zñ]+(?:'[a-z]+)?|\d+|[!?]")

SPELLING_FIXES = {
    "wi fi": "wifi",
    "comfort room": "cr",
    "air con": "aircon",
    "air conditioner": "aircon",
    "air conditioning": "aircon",
    "ma'am": "maam",
}


def normalize(text):
    """Lowercase, strip URLs/emails/mentions, squash repeated letters and whitespace."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("’", "'").replace("‘", "'").lower()
    text = URL_RE.sub(" ", text)
    text = EMAIL_RE.sub(" ", text)
    text = REDACTION_RE.sub(" ", text)
    text = MENTION_RE.sub(" ", text)
    text = HYPHEN_RE.sub(" ", text)
    for wrong, right in SPELLING_FIXES.items():
        text = text.replace(wrong, right)
    text = REPEAT_RE.sub(r"\1\1", text)
    return WS_RE.sub(" ", text).strip()


def tokenize(text, keep_punct=False, normalized=False):
    text = text if normalized else normalize(text)
    tokens = TOKEN_RE.findall(text)
    if keep_punct:
        return tokens
    return [t for t in tokens if t not in ("!", "?")]


def content_tokens(tokens):
    """Tokens that carry meaning for keyword mining (no stopwords, numbers or symbols)."""
    return [t for t in tokens if t.isalpha() and len(t) > 2 and t not in STOPWORDS]


def ngrams(tokens, n):
    return [" ".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


def collapse_doubles(token):
    """'goood' was reduced to 'good' by normalize(); also try 'soo' -> 'so'."""
    return re.sub(r"([a-z])\1+", r"\1", token)
