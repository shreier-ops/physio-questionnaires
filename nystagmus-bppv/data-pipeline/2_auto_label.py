"""
Step 2: Auto-label videos from title + validate via top comments.

Reads candidates.csv, downloads top comments for each video,
runs keyword classifier on title + sentiment/dispute analysis on comments.

Output: labeled_for_review.csv with auto_label, confidence, top comments,
and a YOUR_DECISION column for manual review.
"""

import csv
import json
import subprocess
import re
from pathlib import Path
from tqdm import tqdm

INPUT = Path(__file__).parent / "output" / "candidates.csv"
OUTPUT = Path(__file__).parent / "output" / "labeled_for_review.csv"

# ============================================================
# Title classification rules
# ============================================================

CANAL_KEYWORDS = {
    "posterior": ["posterior canal", "posterior bppv", "p-bppv", "pc-bppv", "dix-hallpike"],
    "horizontal": ["horizontal canal", "horizontal bppv", "lateral canal", "h-bppv", "lc-bppv", "roll test"],
    "anterior": ["anterior canal", "anterior bppv"],
}

SIDE_KEYWORDS = {
    "right": [r"\bright\b", r"\br[\s\-]bppv", r"\bcw\b", "clockwise"],
    "left": [r"\bleft\b", r"\bl[\s\-]bppv", r"\bccw\b", "counter[- ]?clockwise", "counterclockwise"],
}

VARIANT_KEYWORDS = {
    "geo": ["geotropic", "canalolithiasis"],
    "apogeio": ["apogeotropic", "ageotropic", "cupulolithiasis"],
}

OTHER_KEYWORDS = [
    "vestibular neuritis", "neuronitis", "labyrinthitis",
    "meniere", "menière",
    "central nystagmus", "stroke", "cva", "cerebellar",
    "downbeat", "upbeat nystagmus", "spontaneous nystagmus",
    "direction changing", "congenital nystagmus", "tumor",
]


def classify_title(title: str) -> tuple[str, float]:
    """Returns (label, confidence). Confidence based on keyword strength."""
    t = title.lower()

    # Check for "other" pathologies first
    for kw in OTHER_KEYWORDS:
        if kw in t:
            return ("other_nystagmus", 0.85)

    # Check for BPPV
    canal = None
    for c, kws in CANAL_KEYWORDS.items():
        if any(kw in t for kw in kws):
            canal = c
            break

    if canal == "anterior":
        # We don't have anterior class - map to other
        return ("other_nystagmus", 0.70)

    if canal == "horizontal":
        # Determine variant
        for variant, kws in VARIANT_KEYWORDS.items():
            if any(kw in t for kw in kws):
                return (f"horizontal_{variant}", 0.90)
        # Horizontal but no variant specified
        return ("horizontal_unknown", 0.50)

    if canal == "posterior":
        for side, patterns in SIDE_KEYWORDS.items():
            if any(re.search(p, t) for p in patterns):
                return (f"posterior_{side}", 0.90)
        return ("posterior_unknown", 0.55)

    # No nystagmus keyword detected
    if "nystagmus" in t or "bppv" in t or "vertigo" in t:
        return ("unclear", 0.30)

    return ("not_relevant", 0.10)


# ============================================================
# Comment validation
# ============================================================

DISPUTE_PHRASES = [
    "wrong", "incorrect", "actually this", "actually it", "should be",
    "this is not", "this isn't", "misdiagnos", "mistake", "error",
    "not posterior", "not horizontal", "not anterior",
    "it's actually", "it is actually",
    "disagree", "i don't think this", "rather", "looks more like",
]

CONFIRM_PHRASES = [
    "great example", "textbook", "classic", "perfect example",
    "exactly", "correct diagnosis", "good demonstration", "thank you for showing",
    "very clear", "great teaching",
]


def fetch_top_comments(video_url: str, max_comments: int = 20) -> list[dict]:
    """Fetch top comments via yt-dlp."""
    cmd = [
        "yt-dlp",
        video_url,
        "--write-comments",
        "--skip-download",
        "--no-warnings",
        "--ignore-errors",
        "--extractor-args", f"youtube:max_comments={max_comments};comment_sort=top",
        "--dump-single-json",
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if not r.stdout:
            return []
        data = json.loads(r.stdout)
        comments = data.get("comments", [])[:max_comments]
        return [
            {"text": c.get("text", ""), "likes": c.get("like_count", 0) or 0}
            for c in comments
        ]
    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
        return []


def validate_with_comments(comments: list[dict]) -> tuple[float, int, int, str]:
    """
    Returns (validation_factor, dispute_count, confirm_count, top_3_text).
    validation_factor in [0.3, 1.2] - multiplied with title_confidence.
    """
    if not comments:
        return (1.0, 0, 0, "")

    dispute_score = 0
    confirm_score = 0
    for c in comments:
        text = c["text"].lower()
        weight = 1 + min(c["likes"] / 10, 5)  # capped at 5x
        for p in DISPUTE_PHRASES:
            if p in text:
                dispute_score += weight
                break
        for p in CONFIRM_PHRASES:
            if p in text:
                confirm_score += weight
                break

    factor = 1.0 + (confirm_score - dispute_score) * 0.05
    factor = max(0.3, min(1.2, factor))

    top_3 = " | ".join(c["text"][:120].replace("\n", " ") for c in comments[:3])
    return (factor, int(dispute_score), int(confirm_score), top_3)


# ============================================================
# Main
# ============================================================

def main():
    rows_out = []
    with open(INPUT, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    for row in tqdm(reader, desc="Auto-labeling"):
        label, title_conf = classify_title(row["title"])

        # Skip irrelevant videos
        if label in ("not_relevant",):
            continue

        # Comment validation (slow - only for relevant)
        comments = fetch_top_comments(row["url"])
        val_factor, dispute_n, confirm_n, top3 = validate_with_comments(comments)

        final_conf = round(title_conf * val_factor, 3)

        rows_out.append({
            "video_id": row["video_id"],
            "url": row["url"],
            "title": row["title"],
            "channel": row["channel"],
            "duration": row["duration"],
            "auto_label": label,
            "title_confidence": title_conf,
            "validation_factor": round(val_factor, 3),
            "final_confidence": final_conf,
            "dispute_signals": dispute_n,
            "confirm_signals": confirm_n,
            "top_3_comments": top3,
            "search_query": row["search_query"],
            "YOUR_DECISION": "",  # User fills: approve / reject / relabel:<class>
        })

    # Sort by confidence (highest first - easiest to review first)
    rows_out.sort(key=lambda r: -r["final_confidence"])

    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        if rows_out:
            writer = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
            writer.writeheader()
            writer.writerows(rows_out)

    print(f"\nLabeled {len(rows_out)} videos")
    print(f"Saved to {OUTPUT}")
    print("\n👉 NEXT STEP: Open this CSV and fill the YOUR_DECISION column for each row:")
    print("   - 'approve' = use this video as-is with auto_label")
    print("   - 'reject' = exclude from training")
    print("   - 'relabel:posterior_left' (or other class) = use video but with different label")


if __name__ == "__main__":
    main()
