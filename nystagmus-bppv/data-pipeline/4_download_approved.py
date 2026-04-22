"""
Step 4: Download only APPROVED videos (plus relabeled).

Uses yt-dlp to download actual video files for feature extraction.
Writes approved_videos.csv with final labels.
"""

import csv
import subprocess
from pathlib import Path
from tqdm import tqdm

INPUT = Path(__file__).parent / "output" / "labeled_for_review.csv"
VIDEOS_DIR = Path(__file__).parent / "output" / "videos"
APPROVED_CSV = Path(__file__).parent / "output" / "approved_videos.csv"


def main():
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

    rows = list(csv.DictReader(open(INPUT, encoding="utf-8")))
    approved = []
    for r in rows:
        d = r["YOUR_DECISION"].strip()
        if d == "approve":
            final_label = r["auto_label"]
        elif d.startswith("relabel:"):
            final_label = d.split(":", 1)[1].strip()
        else:
            continue

        approved.append({
            "video_id": r["video_id"],
            "url": r["url"],
            "title": r["title"],
            "final_label": final_label,
            "local_path": str(VIDEOS_DIR / f"{r['video_id']}.mp4"),
        })

    print(f"Downloading {len(approved)} approved videos...")

    for v in tqdm(approved):
        out = VIDEOS_DIR / f"{v['video_id']}.mp4"
        if out.exists() and out.stat().st_size > 0:
            continue
        cmd = [
            "yt-dlp", v["url"],
            "-f", "best[height<=720][ext=mp4]/best[ext=mp4]/best",
            "-o", str(out),
            "--no-warnings",
            "--quiet",
            "--no-playlist",
        ]
        subprocess.run(cmd, capture_output=True, timeout=600)

    # Save manifest
    with open(APPROVED_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(approved[0].keys()) if approved else [])
        w.writeheader()
        w.writerows(approved)

    print(f"✅ Downloaded. Manifest: {APPROVED_CSV}")


if __name__ == "__main__":
    main()
