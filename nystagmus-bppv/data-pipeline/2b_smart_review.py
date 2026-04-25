"""
Auto-approves high-confidence videos and shows only borderline cases.

- final_confidence >= 0.85 AND dispute_signals == 0 → auto approve
- final_confidence < 0.40 OR label unclear/not_relevant → auto reject
- Everything else → needs your manual decision (printed to screen)
"""

import csv
from pathlib import Path
from collections import Counter

INPUT = Path(__file__).parent / "output" / "labeled_for_review.csv"

AUTO_APPROVE_THRESHOLD = 0.85
AUTO_REJECT_THRESHOLD = 0.40
SKIP_LABELS = {"unclear", "not_relevant", "horizontal_unknown", "posterior_unknown"}

rows = list(csv.DictReader(open(INPUT, encoding="utf-8")))

auto_approved = 0
auto_rejected = 0
needs_review = []

for r in rows:
    conf = float(r.get("final_confidence") or 0)
    dispute = int(float(r.get("dispute_signals") or 0))
    label = r.get("auto_label", "")

    if label in SKIP_LABELS or conf < AUTO_REJECT_THRESHOLD:
        r["YOUR_DECISION"] = "reject"
        auto_rejected += 1
    elif conf >= AUTO_APPROVE_THRESHOLD and dispute == 0:
        r["YOUR_DECISION"] = "approve"
        auto_approved += 1
    else:
        needs_review.append(r)

print(f"Auto-approved: {auto_approved}")
print(f"Auto-rejected: {auto_rejected}")
print(f"Needs your review: {len(needs_review)}")

# Show class distribution of auto-approved
approved_rows = [r for r in rows if r.get("YOUR_DECISION") == "approve"]
dist = Counter(r["auto_label"] for r in approved_rows)
print("\nAuto-approved class distribution:")
for k, v in sorted(dist.items()):
    bar = "█" * min(v, 30)
    print(f"  {k:25s} {v:3d}  {bar}")

# Print borderline videos for manual review
if needs_review:
    print(f"\n{'='*70}")
    print(f"BORDERLINE VIDEOS - check these {len(needs_review)} manually:")
    print(f"{'='*70}")
    for i, r in enumerate(needs_review, 1):
        print(f"\n[{i}/{len(needs_review)}]")
        print(f"  Title:      {r['title'][:80]}")
        print(f"  Label:      {r['auto_label']}")
        print(f"  Confidence: {r['final_confidence']}")
        print(f"  Disputes:   {r['dispute_signals']}")
        print(f"  Comments:   {r['top_3_comments'][:120]}")
        print(f"  URL:        {r['url']}")
        decision = input("  Decision (approve / reject / relabel:CLASS): ").strip()
        if not decision:
            decision = "reject"
        r["YOUR_DECISION"] = decision

# Save updated CSV
with open(INPUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

# Final summary
final_approved = [r for r in rows if r.get("YOUR_DECISION") not in ("reject", "")]
final_dist = Counter(r["auto_label"] if not r["YOUR_DECISION"].startswith("relabel:")
                     else r["YOUR_DECISION"].split(":")[1]
                     for r in final_approved)
print(f"\n{'='*70}")
print("FINAL approved class distribution:")
for k, v in sorted(final_dist.items()):
    bar = "█" * min(v, 30)
    status = "✅" if v >= 20 else "⚠️ need more"
    print(f"  {k:25s} {v:3d}  {bar}  {status}")
print(f"\nTotal approved: {sum(final_dist.values())}")
print("labeled_for_review.csv updated. Ready for step 4.")
