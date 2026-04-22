"""
Step 3: Generate human-readable summary of review decisions.

Helps you see balance per class, low-confidence outliers, and dispute flags
BEFORE downloading/training. Run after filling YOUR_DECISION column.
"""

import csv
from pathlib import Path
from collections import Counter

INPUT = Path(__file__).parent / "output" / "labeled_for_review.csv"


def main():
    if not INPUT.exists():
        print(f"❌ Not found: {INPUT}")
        return

    rows = list(csv.DictReader(open(INPUT, encoding="utf-8")))
    total = len(rows)

    decisions = Counter(r["YOUR_DECISION"].strip().split(":")[0] or "(empty)" for r in rows)
    print("=" * 60)
    print(f"REVIEW SUMMARY ({total} candidate videos)")
    print("=" * 60)
    print("\nDecision breakdown:")
    for k, v in decisions.most_common():
        print(f"  {k:20s} {v:4d}  ({v/total*100:.1f}%)")

    if decisions["(empty)"] > 0:
        print(f"\n⚠️  {decisions['(empty)']} rows still need a decision!")
        return

    # Final labels
    final_labels = []
    for r in rows:
        d = r["YOUR_DECISION"].strip()
        if d == "approve":
            final_labels.append(r["auto_label"])
        elif d.startswith("relabel:"):
            final_labels.append(d.split(":", 1)[1].strip())

    print("\n📊 Final class distribution (after approval):")
    label_counts = Counter(final_labels)
    for label, count in label_counts.most_common():
        bar = "█" * min(count // 2, 40)
        print(f"  {label:25s} {count:4d}  {bar}")

    if not label_counts:
        print("  (none approved yet)")
        return

    print(f"\n  TOTAL approved: {sum(label_counts.values())}")

    # Warning if any class is under-represented
    target_per_class = 100
    print("\n🎯 Target: ≥100 per class (before augmentation)")
    for label, count in label_counts.items():
        if count < target_per_class:
            need = target_per_class - count
            print(f"  ⚠️  {label}: need {need} more videos")
        else:
            print(f"  ✅ {label}: meets target")


if __name__ == "__main__":
    main()
