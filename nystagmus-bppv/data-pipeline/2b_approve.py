import csv
from pathlib import Path
from collections import Counter

INPUT = Path(__file__).parent / "output" / "labeled_for_review.csv"
rows = list(csv.DictReader(open(INPUT, encoding="utf-8")))
SKIP = {"unclear", "not_relevant", "horizontal_unknown", "posterior_unknown"}

# Lower threshold for rare classes that are hard to find on YouTube
RARE_CLASSES = {"horizontal_apogeio", "no_nystagmus"}
NORMAL_THRESHOLD = 0.70
RARE_THRESHOLD = 0.45

approved = rejected = 0
for r in rows:
    conf = float(r.get("final_confidence") or 0)
    dispute = int(float(r.get("dispute_signals") or 0))
    label = r.get("auto_label", "")
    threshold = RARE_THRESHOLD if label in RARE_CLASSES else NORMAL_THRESHOLD
    if label in SKIP or conf < 0.30:
        r["YOUR_DECISION"] = "reject"
        rejected += 1
    elif conf >= threshold and dispute == 0:
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
