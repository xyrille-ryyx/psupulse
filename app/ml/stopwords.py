"""Stopwords removed before keyword mining (NOT before sentiment scoring,
because words like "not" and "very" change polarity)."""

ENGLISH = {
    "a", "about", "above", "after", "again", "all", "also", "am", "an", "and", "any", "are",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but",
    "by", "can", "could", "did", "do", "does", "doing", "down", "during", "each", "even",
    "every", "few", "for", "from", "further", "get", "gets", "got", "had", "has", "have",
    "having", "he", "her", "here", "hers", "him", "his", "how", "i", "if", "in", "into", "is",
    "it", "its", "it's", "itself", "just", "let", "lot", "lots", "make", "makes", "many", "me",
    "might", "more", "most", "much", "must", "my", "myself", "now", "of", "off", "on", "once",
    "one", "only", "or", "other", "our", "ours", "out", "over", "own", "please", "same", "she",
    "should", "since", "so", "some", "still", "such", "than", "that", "the", "their", "them",
    "then", "there", "these", "they", "thing", "things", "this", "those", "through", "to",
    "too", "under", "until", "up", "us", "use", "used", "very", "was", "way", "we", "week",
    "weeks", "were", "what", "when", "where", "which", "while", "who", "whom", "why", "will",
    "with", "would", "you", "your", "yours", "yourself", "i'm", "im", "ive", "i've", "really",
    "also", "always", "sometimes", "every", "today", "time", "times", "need", "needs", "like",
    "know", "think", "feel", "feels", "felt", "want", "going", "yet", "etc", "able", "maybe",
    "next", "last", "first", "two", "three", "four", "five", "start", "starts", "started",
    "day", "days", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
}

FILIPINO = {
    "ako", "ikaw", "ka", "siya", "kami", "tayo", "kayo", "sila", "ko", "mo", "niya", "namin",
    "natin", "ninyo", "nila", "akin", "atin", "amin", "inyo", "kanila", "kaniya", "ang", "ng",
    "nang", "mga", "sa", "si", "ni", "kay", "kina", "na", "at", "ay", "ito", "iyan", "iyon",
    "yan", "yun", "yung", "iyong", "dito", "diyan", "doon", "dun", "po", "opo", "lang",
    "lamang", "din", "rin", "naman", "pa", "ba", "kasi", "kung", "para", "pag", "kapag",
    "may", "mayroon", "meron", "pero", "kaya", "dahil", "tapos", "talaga", "sana", "nga",
    "daw", "raw", "ano", "sino", "saan", "bakit", "paano", "kailan", "lahat", "isa", "mas",
    "ganun", "ganito", "ganyan", "eh", "e", "ha", "o", "oo", "hindi", "di", "wala", "walang",
    "huwag", "wag", "sobra", "sobrang", "napaka", "medyo", "masyado", "masyadong", "parang",
    "minsan", "lagi", "palagi", "ngayon", "mag", "nag", "nasa", "pang", "pati", "kahit",
    "kami", "namin", "sya", "nya", "nyo", "kc", "lng", "nmn", "tlga", "pra", "ung",
}

NEGATION_WORDS = {
    "not", "no", "never", "none", "nothing", "cannot", "cant", "can't", "dont", "don't",
    "doesnt", "doesn't", "didnt", "didn't", "isnt", "isn't", "wasnt", "wasn't", "arent",
    "aren't", "wont", "won't", "without", "ayaw", "ayoko",
}

STOPWORDS = ENGLISH | FILIPINO | NEGATION_WORDS
