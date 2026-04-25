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
    # posterior_right - ממוקד מאוד
    "right posterior canal BPPV dix-hallpike nystagmus eye",
    "dix-hallpike right positive nystagmus patient eye",
    "right BPPV upbeat torsional nystagmus examination",
    "right posterior canalolithiasis nystagmus eye close",

    # posterior_left - ממוקד מאוד
    "left posterior canal BPPV dix-hallpike nystagmus eye",
    "dix-hallpike left positive nystagmus patient eye",
    "left BPPV upbeat torsional nystagmus examination",
    "left posterior canalolithiasis nystagmus eye close",

    # horizontal_geo - geotropic
    "geotropic nystagmus roll test eye close up",
    "horizontal canal BPPV geotropic eye movement patient",
    "canalolithiasis horizontal canal nystagmus eye",
    "BBQ roll test positive nystagmus eye",

    # horizontal_apogeio - apogeotropic
    "apogeotropic nystagmus roll test eye patient",
    "cupulolithiasis nystagmus eye movement close",
    "horizontal canal BPPV apogeotropic eye examination",
    "ageotropic nystagmus roll test eye",

    # no_nystagmus - negative tests
    "dix-hallpike negative no nystagmus normal",
    "BPPV negative test normal eye movement",
    "dix-hallpike normal eye no vertigo patient",

    # other_nystagmus - non-BPPV (limited to 20)
    "vestibular neuritis nystagmus eye examination",
    "spontaneous nystagmus eye patient close up",
    "downbeat nystagmus eye movement close",
]

MAX_PER_QUERY = 50

# Cap per class to avoid imbalance
MAX_PER_CLASS = 30

EXCLUDE_TITLE_WORDS = [
    "lecture", "tutorial", "explained", "what is", "anatomy", "animation",
    "how to perform", "how to do", "epley", "semont", "barbecue", "brandt",
    "treatment", "therapy", "relief", "cure", "exercise", "yoga",
    "causes", "symptoms", "overview", "introduction", "what causes",
    "3d", "diagram", "illustration", "drawing",
]
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

    # Filter 1: duration 5 seconds to 5 minutes (clinical exam clips, not lectures)
    filtered = [v for v in all_videos if 5 <= (v["duration"] or 0) <= 300]

    # Filter 2: exclude titles that match lecture/treatment/non-exam keywords
    def is_exam_video(title: str) -> bool:
        t = title.lower()
        return not any(w in t for w in EXCLUDE_TITLE_WORDS)

    filtered = [v for v in filtered if is_exam_video(v["title"])]

    print(f"\nFound {len(all_videos)} unique videos")
    print(f"After duration filter (5s-5min): {len([v for v in all_videos if 5 <= (v['duration'] or 0) <= 300])}")
    print(f"After excluding lectures/treatments: {len(filtered)}")

    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(filtered[0].keys()) if filtered else [])
        writer.writeheader()
        writer.writerows(filtered)

    print(f"Saved to {OUTPUT}")


if __name__ == "__main__":
    main()
