"""Classifier evaluation metrics, written out by hand (no scikit-learn)."""
from collections import Counter

LABELS = ("positive", "negative", "neutral")


def confusion_matrix(y_true, y_pred, labels=LABELS):
    """matrix[i][j] = number of items whose true label is labels[i] and predicted labels[j]."""
    index = {label: i for i, label in enumerate(labels)}
    matrix = [[0] * len(labels) for _ in labels]
    for t, p in zip(y_true, y_pred):
        if t in index and p in index:
            matrix[index[t]][index[p]] += 1
    return matrix


def classification_report(y_true, y_pred, labels=LABELS):
    matrix = confusion_matrix(y_true, y_pred, labels)
    per_class = {}
    for i, label in enumerate(labels):
        tp = matrix[i][i]
        fp = sum(matrix[r][i] for r in range(len(labels))) - tp
        fn = sum(matrix[i]) - tp
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class[label] = {"precision": precision, "recall": recall, "f1": f1, "support": sum(matrix[i])}

    n = len(labels)
    total = sum(sum(row) for row in matrix)
    return {
        "labels": list(labels),
        "per_class": per_class,
        "accuracy": sum(matrix[i][i] for i in range(n)) / total if total else 0.0,
        "precision_macro": sum(c["precision"] for c in per_class.values()) / n,
        "recall_macro": sum(c["recall"] for c in per_class.values()) / n,
        "f1_macro": sum(c["f1"] for c in per_class.values()) / n,
        "confusion_matrix": matrix,
        "total": total,
    }


def cohens_kappa(rater_a, rater_b):
    """Agreement between two annotators beyond chance (for the ground-truth labels)."""
    pairs = [(a, b) for a, b in zip(rater_a, rater_b) if a and b]
    if not pairs:
        return 0.0
    n = len(pairs)
    observed = sum(1 for a, b in pairs if a == b) / n
    count_a = Counter(a for a, _ in pairs)
    count_b = Counter(b for _, b in pairs)
    expected = sum(count_a[k] * count_b.get(k, 0) for k in count_a) / (n * n)
    return (observed - expected) / (1 - expected) if expected < 1 else 1.0


def evaluate(texts, y_true, analyzer):
    y_pred = [analyzer.score(t).label for t in texts]
    report = classification_report(y_true, y_pred)
    report["name"] = analyzer.name
    report["errors"] = [
        {"text": t, "expected": e, "predicted": p}
        for t, e, p in zip(texts, y_true, y_pred) if e != p
    ]
    return report
