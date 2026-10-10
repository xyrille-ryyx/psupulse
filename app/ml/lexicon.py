"""Sentiment lexicon for English, Filipino and Taglish student comments.

Valence runs from -3 (very negative) to +3 (very positive). Edit these lists to
tune the analyzer, and record every change in Admin > Change log (Phase G/H).
"""

POSITIVE = {
    # English, strong
    "excellent": 3.0, "outstanding": 3.0, "amazing": 3.0, "awesome": 3.0, "fantastic": 3.0,
    "wonderful": 3.0, "superb": 3.0, "perfect": 3.0, "brilliant": 3.0, "love": 3.0,
    "loved": 3.0, "best": 3.0, "exceptional": 3.0, "great": 2.5, "inspiring": 2.5,
    "impressive": 2.5, "happy": 2.5, "grateful": 2.5, "thankful": 2.5, "beautiful": 2.5,
    "passionate": 2.5,
    # English, moderate
    "good": 2.0, "nice": 2.0, "helpful": 2.0, "clear": 2.0, "kind": 2.0, "friendly": 2.0,
    "patient": 2.0, "engaging": 2.0, "interesting": 2.0, "enjoyable": 2.0, "enjoy": 2.0,
    "enjoyed": 2.0, "fun": 2.0, "informative": 2.0, "organized": 2.0, "organised": 2.0,
    "effective": 2.0, "efficient": 2.0, "clean": 2.0, "comfortable": 2.0, "safe": 2.0,
    "approachable": 2.0, "knowledgeable": 2.0, "supportive": 2.0, "responsive": 2.0,
    "accommodating": 2.0, "motivating": 2.0, "glad": 2.0, "satisfied": 2.0, "pleased": 2.0,
    "appreciate": 2.0, "appreciated": 2.0, "recommend": 2.0, "improved": 2.0, "reliable": 2.0,
    "convenient": 2.0, "useful": 2.0, "valuable": 2.0, "polite": 2.0, "respectful": 2.0,
    "encouraging": 2.0, "excited": 2.0, "exciting": 2.0, "proud": 2.0, "welcoming": 2.0,
    "creative": 2.0, "dedicated": 2.0, "competent": 2.0, "professional": 2.0, "positive": 2.0,
    "successful": 2.0, "success": 2.0, "solid": 2.0,
    # English, mild
    "fast": 1.5, "quick": 1.5, "easy": 1.5, "secure": 1.5, "motivated": 1.5, "thanks": 1.5,
    "thank": 1.5, "improving": 1.5, "better": 1.5, "fair": 1.5, "smooth": 1.5,
    "accessible": 1.5, "spacious": 1.5, "relevant": 1.5, "understanding": 1.5,
    "prepared": 1.5, "punctual": 1.5, "cool": 1.5, "learned": 1.5, "worth": 1.5,
    "affordable": 1.5, "detailed": 1.5, "thorough": 1.5, "fresh": 1.5, "goods": 1.5,
    "well": 1.0, "learn": 1.0, "adequate": 1.0, "sufficient": 1.0, "updated": 1.0,
    "quiet": 1.0, "calm": 1.0, "bright": 1.0, "fine": 0.8, "okay": 0.5, "ok": 0.5,
    # Filipino / Taglish
    "maganda": 2.5, "ganda": 2.5, "magaling": 2.5, "galing": 2.5, "mabait": 2.5,
    "masaya": 2.5, "mahusay": 2.5, "husay": 2.5, "panalo": 2.5, "matulungin": 2.5,
    "bait": 2.0, "saya": 2.0, "malinis": 2.0, "maayos": 2.0, "ayos": 2.0, "sulit": 2.0,
    "salamat": 2.0, "astig": 2.0, "bongga": 2.0, "malinaw": 2.0, "maasahan": 2.0,
    "komportable": 2.0, "ligtas": 2.0, "nagustuhan": 2.0, "natuto": 2.0, "natutunan": 2.0,
    "magiliw": 2.0, "masipag": 2.0, "masarap": 2.0, "sarap": 2.0, "ganado": 2.0,
    "inspirado": 2.0, "linis": 1.5, "mabilis": 1.5, "madali": 1.5, "linaw": 1.5,
    "presko": 1.5, "gusto": 1.5, "mura": 1.5, "swak": 1.5, "bilis": 1.0, "tahimik": 1.0,
    "gaan": 1.0,
}

NEGATIVE = {
    # English, strong
    "terrible": -3.0, "horrible": -3.0, "awful": -3.0, "worst": -3.0, "hate": -3.0,
    "hated": -3.0, "disgusting": -3.0, "unacceptable": -3.0, "pathetic": -3.0,
    "bullying": -3.0, "harassment": -3.0, "useless": -2.5, "dangerous": -2.5, "unsafe": -2.5,
    "rude": -2.5, "frustrating": -2.5, "frustrated": -2.5, "disappointing": -2.5,
    "disappointed": -2.5, "angry": -2.5, "worse": -2.5, "bully": -2.5, "threat": -2.5,
    "theft": -2.5, "stolen": -2.5,
    # English, moderate
    "bad": -2.0, "poor": -2.0, "boring": -2.0, "confusing": -2.0, "unclear": -2.0,
    "dirty": -2.0, "broken": -2.0, "unfair": -2.0, "unhelpful": -2.0, "unprepared": -2.0,
    "disorganized": -2.0, "unorganized": -2.0, "uncomfortable": -2.0, "stressful": -2.0,
    "stressed": -2.0, "exhausted": -2.0, "overwhelming": -2.0, "overwhelmed": -2.0,
    "annoying": -2.0, "annoyed": -2.0, "sad": -2.0, "fail": -2.0, "failed": -2.0,
    "failing": -2.0, "crash": -2.0, "laggy": -2.0, "overpriced": -2.0, "waste": -2.0,
    "wasted": -2.0, "ignored": -2.0, "unresponsive": -2.0, "harsh": -2.0, "scary": -2.0,
    "afraid": -2.0, "anxious": -2.0, "anxiety": -2.0, "smelly": -2.0, "flood": -2.0,
    "flooded": -2.0, "hassle": -2.0, "burden": -2.0, "impossible": -2.0, "fear": -2.0,
    "inefficient": -2.0, "lazy": -2.0, "careless": -2.0, "overload": -2.0,
    "overloaded": -2.0, "mess": -2.0, "chaotic": -2.0, "chaos": -2.0, "unbearable": -2.5,
    # English, mild
    "confused": -1.5, "difficult": -1.5, "slow": -1.5, "late": -1.5, "delayed": -1.5,
    "delay": -1.5, "messy": -1.5, "noisy": -1.5, "crowded": -1.5, "stress": -1.5,
    "tired": -1.5, "problem": -1.5, "problems": -1.5, "complaint": -1.5, "lacking": -1.5,
    "lack": -1.5, "missing": -1.5, "error": -1.5, "errors": -1.5, "lag": -1.5,
    "outdated": -1.5, "expensive": -1.5, "ignore": -1.5, "inconsistent": -1.5,
    "worried": -1.5, "worry": -1.5, "leak": -1.5, "leaking": -1.5, "unavailable": -1.5,
    "sick": -1.5, "rushed": -1.5, "cramming": -1.5, "insufficient": -1.5, "brownout": -1.5,
    "hard": -1.0, "issue": -1.0, "issues": -1.0, "absent": -1.0, "strict": -1.0,
    "hot": -1.0, "smell": -1.0, "cancelled": -1.0, "canceled": -1.0, "limited": -1.0,
    # Filipino / Taglish
    "pangit": -2.5, "panget": -2.5, "nakakainis": -2.5, "bastos": -2.5, "masungit": -2.5,
    "nakakatakot": -2.5, "delikado": -2.5, "palpak": -2.5, "bulok": -2.5,
    "nakakadismaya": -2.5, "badtrip": -2.5, "mabagal": -2.0, "magulo": -2.0,
    "madumi": -2.0, "marumi": -2.0, "sira": -2.0, "inis": -2.0, "nakakabagot": -2.0,
    "nakakapagod": -2.0, "nakakalito": -2.0, "sungit": -2.0, "galit": -2.0,
    "malungkot": -2.0, "takot": -2.0, "sablay": -2.0, "baha": -2.0, "mabaho": -2.0,
    "baho": -2.0, "tamad": -2.0, "dismaya": -2.0, "mainit": -1.5, "bagal": -1.5,
    "gulo": -1.5, "dumi": -1.5, "bagot": -1.5, "pagod": -1.5, "lito": -1.5,
    "mahirap": -1.5, "hirap": -1.5, "lungkot": -1.5, "kulang": -1.5, "kakulangan": -1.5,
    "problema": -1.5, "reklamo": -1.5, "siksikan": -1.5, "masikip": -1.5,
    "maingay": -1.5, "init": -1.0, "ingay": -1.0,
}

VALENCE = {**POSITIVE, **NEGATIVE}

# Multi-word expressions are matched before single words (longest first).
PHRASES = {
    "walang kwenta": -3.0, "walang kuwenta": -3.0, "waste of time": -2.5,
    "no wifi": -1.5, "walang wifi": -1.5, "no internet": -1.5, "walang internet": -1.5,
    "no signal": -1.5, "walang signal": -1.5, "no aircon": -1.5, "walang aircon": -1.5,
    "no water": -1.5, "walang tubig": -1.5, "no electricity": -1.5, "walang kuryente": -1.5,
    "no response": -1.5, "no feedback": -1.5, "no answer": -1.5, "walang sagot": -1.5,
    "too much": -1.0, "too many": -1.0, "last minute": -1.5, "could be better": -1.0,
    "so so": -0.5, "well done": 2.5, "highly recommend": 3.0, "thank you": 2.0,
    "maraming salamat": 2.5, "keep it up": 2.5, "keep up the good work": 3.0,
    "on time": 1.5, "user friendly": 2.0, "worth it": 2.0, "sana all": 0.0,
}

NEGATORS = {
    "not", "no", "never", "none", "nobody", "nothing", "neither", "nor", "cannot", "cant",
    "can't", "dont", "don't", "doesnt", "doesn't", "didnt", "didn't", "isnt", "isn't",
    "wasnt", "wasn't", "arent", "aren't", "werent", "weren't", "wont", "won't", "wouldnt",
    "wouldn't", "shouldnt", "shouldn't", "couldnt", "couldn't", "hardly", "barely",
    "without", "hindi", "hinde", "di", "'di", "wala", "walang", "huwag", "wag", "ayaw",
    "ayoko",
}
NEGATION_SCALAR = -0.74
NEGATION_SCOPE = 3  # tokens before a sentiment word that a negator can reach

# Positive values intensify, negative values soften ("medyo maganda").
BOOSTERS = {
    "very": 0.293, "really": 0.293, "extremely": 0.293, "so": 0.293, "too": 0.293,
    "super": 0.293, "totally": 0.293, "absolutely": 0.293, "highly": 0.293,
    "incredibly": 0.293, "completely": 0.293, "truly": 0.293, "most": 0.293,
    "quite": 0.15, "sobra": 0.293, "sobrang": 0.293, "napaka": 0.293, "talaga": 0.293,
    "grabe": 0.293, "masyado": 0.293, "masyadong": 0.293, "lubha": 0.293, "todo": 0.293,
    "slightly": -0.293, "somewhat": -0.293, "kinda": -0.293, "bit": -0.293,
    "little": -0.293, "medyo": -0.293, "konti": -0.293, "kaunti": -0.293,
}

# Filipino affixes stripped to find a root word ("napakaganda" -> "ganda").
TL_PREFIXES = (("napaka", 0.4), ("pinaka", 0.4), ("nakaka", 0.0), ("naka", 0.0))

# Clause after a contrast word dominates: "maganda yung room pero mainit".
CONTRAST = {"but", "however", "pero", "kaso", "ngunit", "subalit"}
CONTRAST_BEFORE = 0.5
CONTRAST_AFTER = 1.5

EMOTICONS = {
    ":)": 2.0, ":-)": 2.0, "=)": 2.0, ":d": 2.5, ";)": 1.5, ":p": 1.0, "<3": 2.5,
    ":(": -2.0, ":-(": -2.0, "=(": -2.0, ":/": -1.0, ":|": -0.5,
    "\U0001F60A": 2.0, "\U0001F600": 2.0, "\U0001F601": 2.0, "\U0001F602": 1.0,
    "\U0001F44D": 2.0, "❤": 2.5, "\U0001F64F": 1.5, "\U0001F621": -3.0,
    "\U0001F620": -2.5, "\U0001F622": -2.0, "\U0001F62D": -2.0, "\U0001F44E": -2.0,
    "\U0001F61E": -2.0, "\U0001F641": -2.0, "\U0001F624": -2.0,
}

EXCLAMATION_BOOST = 0.292
MAX_EXCLAMATIONS = 4
NORMALIZATION_ALPHA = 15  # compound = s / sqrt(s^2 + alpha)
