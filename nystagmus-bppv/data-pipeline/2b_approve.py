import csv
from pathlib import Path
from collections import Counter

INPUT = Path(__file__).parent / "output" / "labeled_for_review.csv"
rows = list(csv.DictReader(open(INPUT, encoding="utf-8")))
SKIP = {"unclear", "not_relevant", "horizontal_unknown", "posterior_unknown"}
approved = rejected = 0
for r in rows:
    conf = float(r.get("final_confidence") or 0)
    dispute = int(float(r.get("dispute_signals") or 0))
    label = r.get("auto_label", "")
    if label in SKIP or conf < 0.35:
        r["YOUR_DECISION"] = "reject"
        rejected += 1
    elif conf >= 0.70 and dispute == 0:
        r["YOUR_DECISION"] = "approve"
        approved += 1
    else:
        r["YOUR_DECISION"] = "reject"
        rejected += 1
with open(INPUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
dist = Counter(r["auto_label"] for r in rows if r["YOUR_DECISION"] == "approve")
print(f"Approved: {approved}, Rejected: {rejected}")
print("Class distribution:")
for k, v in sorted(dist.items()):
    print(f"  {k}: {v}")
