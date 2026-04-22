"""
מסנן את candidates.csv הקיים:
- מוחק סרטונים ארוכים מ-5 דקות (הרצאות)
- מוחק סרטונים עם כותרות של הרצאות/טיפולים
"""

import csv
from pathlib import Path

INPUT = Path(__file__).parent / "output" / "candidates.csv"
OUTPUT = Path(__file__).parent / "output" / "candidates.csv"

EXCLUDE_WORDS = [
    "lecture", "tutorial", "explained", "what is", "anatomy", "animation",
    "how to perform", "how to do", "epley", "semont", "barbecue", "brandt",
    "treatment", "therapy", "relief", "cure", "exercise", "yoga",
    "causes", "symptoms", "overview", "introduction", "what causes",
    "3d", "diagram", "illustration", "drawing",
]

rows = list(csv.DictReader(open(INPUT, encoding="utf-8")))
print(f"Before filter: {len(rows)}")

filtered = []
for r in rows:
    dur = int(float(r.get("duration") or 0))
    title = r.get("title", "").lower()
    if dur > 300:
        continue
    if any(w in title for w in EXCLUDE_WORDS):
        continue
    filtered.append(r)

print(f"After filter (max 5 min + no lectures): {len(filtered)}")

with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(filtered[0].keys()) if filtered else [])
    w.writeheader()
    w.writerows(filtered)

print("Saved.")
