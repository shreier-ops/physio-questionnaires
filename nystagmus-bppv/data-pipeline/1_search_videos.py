"""
Step 1: Search YouTube for nystagmus videos.

Uses yt-dlp to search YouTube and collect metadata (no download yet).
Output: candidates.csv with all found video metadata.
"""

import json
import csv
import subprocess
from pathlib import Path
from tqdm import tqdm

QUERIES = [
    # BPPV - posterior canal
    "posterior canal BPPV nystagmus dix-hallpike",
    "right posterior canal BPPV",
    "left posterior canal BPPV",
    # BPPV - horizontal canal
    "horizontal canal BPPV geotropic roll test",
    "horizontal canal BPPV apogeotropic",
    "lateral canal BPPV nystagmus",
    "cupulolithiasis nystagmus",
    # Other vestibular pathologies (for "other_nystagmus" class)
    "vestibular neuritis nystagmus",
    "Meniere's disease nystagmus video",
    "central nystagmus stroke",
    "downbeat nystagmus",
    "direction changing nystagmus",
    "spontaneous nystagmus",
    # General teaching
    "BPPV patient nystagmus eye movement",
    "nystagmus types neurology",
]

MAX_PER_QUERY = 50  # Per query - total will be larger
OUTPUT = Path(__file__).parent / "output" / "candidates.csv"


def search_query(query: str, max_results: int) -> list[dict]:
    """Search YouTube via yt-dlp, return list of video metadata dicts."""
    cmd = [
        "yt-dlp",
        f"ytsearch{max_results}:{query}",
        "--flat-playlist",
        "--dump-json",
        "--no-warnings",
        "--ignore-errors",
        "--skip-download",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        videos = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            try:
                v = json.loads(line)
                videos.append({
                    "video_id": v.get("id", ""),
                    "url": f"https://www.youtube.com/watch?v={v.get('id', '')}",
                    "title": v.get("title", ""),
                    "channel": v.get("uploader", v.get("channel", "")),
                    "duration": v.get("duration", 0),
                    "view_count": v.get("view_count", 0),
                    "search_query": query,
                })
            except json.JSONDecodeError:
                continue
        return videos
    except subprocess.TimeoutExpired:
        print(f"Timeout on query: {query}")
        return []


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    seen_ids = set()
    all_videos = []

    for query in tqdm(QUERIES, desc="Searching YouTube"):
        videos = search_query(query, MAX_PER_QUERY)
        for v in videos:
            if v["video_id"] and v["video_id"] not in seen_ids:
                seen_ids.add(v["video_id"])
                all_videos.append(v)

    # Filter: keep only videos between 5 sec and 30 min (likely to contain nystagmus)
    filtered = [v for v in all_videos if 5 <= (v["duration"] or 0) <= 1800]

    print(f"\nFound {len(all_videos)} unique videos")
    print(f"After duration filter (5s-30m): {len(filtered)}")

    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(filtered[0].keys()) if filtered else [])
        writer.writeheader()
        writer.writerows(filtered)

    print(f"Saved to {OUTPUT}")


if __name__ == "__main__":
    main()
