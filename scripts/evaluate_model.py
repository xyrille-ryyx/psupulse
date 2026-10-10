"""Evaluate the sentiment analyzer against manually labeled comments (Chapter 5.2).

The CSV needs columns `text,label`; an optional `annotator_2` column adds Cohen's kappa.
Does not need a database.

Usage:  python scripts/evaluate_model.py database/sample_labeled_feedback.csv
        python scripts/evaluate_model.py my_labels.csv --errors
"""
import argparse
import csv
import sys

import _bootstrap  # noqa: F401

from app.ml.evaluation import cohens_kappa, evaluate
from app.ml.sentiment import lexicon_analyzer, wordcount_analyzer


def print_report(r):
    print(f"\n=== {r['name']} ===")
    print(f"Accuracy {r['accuracy']:.3f} | Precision (macro) {r['precision_macro']:.3f} | "
          f"Recall (macro) {r['recall_macro']:.3f} | F1 (macro) {r['f1_macro']:.3f}")
    print(f"{'class':<10}{'prec':>8}{'recall':>8}{'f1':>8}{'n':>6}")
    for label in r["labels"]:
        c = r["per_class"][label]
        print(f"{label:<10}{c['precision']:>8.3f}{c['recall']:>8.3f}{c['f1']:>8.3f}{c['support']:>6}")
    print("Confusion matrix (rows = actual, cols = predicted):")
    print(" " * 10 + "".join(f"{l[:3]:>6}" for l in r["labels"]))
    for label, row in zip(r["labels"], r["confusion_matrix"]):
        print(f"{label:<10}" + "".join(f"{v:>6}" for v in row))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path")
    parser.add_argument("--errors", action="store_true", help="list misclassified comments")
    args = parser.parse_args()

    with open(args.csv_path, encoding="utf-8-sig", newline="") as fh:
        rows = [r for r in csv.DictReader(fh) if (r.get("text") or "").strip() and (r.get("label") or "").strip()]
    if not rows:
        sys.exit("No rows with 'text' and 'label' found.")
    texts = [r["text"].strip() for r in rows]
    labels = [r["label"].strip().lower() for r in rows]
    second = [(r.get("annotator_2") or "").strip().lower() for r in rows]

    print(f"Labeled comments: {len(texts)}")
    if any(second):
        print(f"Cohen's kappa (annotator 1 vs 2): {cohens_kappa(labels, second):.3f}")

    for analyzer in (wordcount_analyzer, lexicon_analyzer):
        report = evaluate(texts, labels, analyzer)
        print_report(report)
        if args.errors and report["errors"]:
            print("Misclassified:")
            for e in report["errors"]:
                print(f"  [{e['expected']} -> {e['predicted']}] {e['text']}")


if __name__ == "__main__":
    main()
