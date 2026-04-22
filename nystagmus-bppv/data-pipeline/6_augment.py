"""
Step 6: Data augmentation on iris trajectories.

Operates on saved trajectories (not raw videos) which is fast and lossless.

Augmentations:
  - Mirror flip horizontal: x -> -x. Swaps right<->left labels.
  - Gaussian noise on coordinates.
  - Time stretch ±20%.
  - Distance simulation (scale).
  - Random window crop offset.

Output: features_augmented.csv (original + augmented rows).
"""

import csv
import numpy as np
from pathlib import Path
from tqdm import tqdm

# Re-use functions from 5_extract_features
import importlib.util
spec = importlib.util.spec_from_file_location("ef", Path(__file__).parent / "5_extract_features.py")
ef = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ef)

APPROVED_CSV = Path(__file__).parent / "output" / "approved_videos.csv"
FEATURES_CSV = Path(__file__).parent / "output" / "features.csv"
AUG_CSV = Path(__file__).parent / "output" / "features_augmented.csv"
TRAJ_DIR = Path(__file__).parent / "output" / "trajectories"

DEFAULT_FPS = 30.0

# Label flips for horizontal mirror
MIRROR_LABEL = {
    "posterior_right": "posterior_left",
    "posterior_left": "posterior_right",
    "horizontal_geo": "horizontal_apogeio",  # geo right ear -> apogeio if mirrored
    "horizontal_apogeio": "horizontal_geo",
    "no_nystagmus": "no_nystagmus",
    "other_nystagmus": "other_nystagmus",
}


def aug_mirror(traj: np.ndarray) -> np.ndarray:
    """Mirror horizontally: invert x of both eyes AND swap right<->left columns."""
    t = traj.copy()
    # Invert x
    t[:, 0] = -t[:, 0]  # right_x
    t[:, 2] = -t[:, 2]  # left_x
    # Swap eyes (since mirror flips which is left/right)
    t = t[:, [2, 3, 0, 1]]
    return t


def aug_noise(traj: np.ndarray, std: float = 0.005) -> np.ndarray:
    return traj + np.random.normal(0, std, traj.shape)


def aug_time_stretch(traj: np.ndarray, factor: float) -> np.ndarray:
    """Resample time axis by factor (0.8 to 1.2)."""
    n = len(traj)
    new_n = max(1, int(n * factor))
    t_old = np.linspace(0, 1, n)
    t_new = np.linspace(0, 1, new_n)
    out = np.zeros((new_n, traj.shape[1]))
    for c in range(traj.shape[1]):
        col = traj[:, c]
        # Interp ignoring NaN
        valid = ~np.isnan(col)
        if valid.sum() < 2:
            out[:, c] = col[:new_n] if new_n <= n else np.pad(col, (0, new_n - n), constant_values=np.nan)
        else:
            out[:, c] = np.interp(t_new, t_old[valid], col[valid])
    return out


def aug_scale(traj: np.ndarray, factor: float) -> np.ndarray:
    """Simulate distance change by scaling coordinate magnitude (around mean)."""
    mean = np.nanmean(traj, axis=0)
    return mean + (traj - mean) * factor


def process(traj: np.ndarray, fps: float, label: str, vid: str, suffix: str, new_label: str = None):
    """Compute features over augmented trajectory and emit rows."""
    rows = []
    for win_idx, (start, window) in enumerate(ef.slide_windows(traj, fps)):
        feats = ef.compute_features(window, fps)
        if feats is None or feats["valid_frame_ratio"] < 0.7:
            continue
        feats["video_id"] = vid
        feats["window_idx"] = win_idx
        feats["window_start_sec"] = round(start, 2)
        feats["label"] = new_label or label
        feats["augmented"] = suffix
        rows.append(feats)
    return rows


def main():
    rows = list(csv.DictReader(open(APPROVED_CSV, encoding="utf-8")))
    all_rows = []

    # Load existing real features
    if FEATURES_CSV.exists():
        all_rows = list(csv.DictReader(open(FEATURES_CSV, encoding="utf-8")))
        print(f"Loaded {len(all_rows)} real feature rows")

    for v in tqdm(rows, desc="Augmenting"):
        traj_path = TRAJ_DIR / f"{v['video_id']}.npy"
        if not traj_path.exists():
            continue
        traj = np.load(traj_path)
        label = v["final_label"]
        vid = v["video_id"]

        # 1. Mirror flip (changes label for L/R or geo/apogeio)
        new_label = MIRROR_LABEL.get(label, label)
        all_rows += process(aug_mirror(traj), DEFAULT_FPS, label, vid, "mirror", new_label)

        # 2-3. Two noise variants (same label)
        for i, std in enumerate([0.003, 0.007]):
            all_rows += process(aug_noise(traj, std), DEFAULT_FPS, label, vid, f"noise_{i}")

        # 4-5. Time stretch
        for i, fac in enumerate([0.85, 1.15]):
            all_rows += process(aug_time_stretch(traj, fac), DEFAULT_FPS, label, vid, f"stretch_{fac}")

        # 6-7. Distance scale
        for i, fac in enumerate([0.8, 1.25]):
            all_rows += process(aug_scale(traj, fac), DEFAULT_FPS, label, vid, f"scale_{fac}")

    if all_rows:
        keys = list(all_rows[0].keys())
        with open(AUG_CSV, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(all_rows)
        print(f"✅ Total rows after augmentation: {len(all_rows)} → {AUG_CSV}")

        # Class distribution
        from collections import Counter
        dist = Counter(r["label"] for r in all_rows)
        print("\nClass distribution after augmentation:")
        for k, v in sorted(dist.items()):
            print(f"  {k:25s} {v:5d}")


if __name__ == "__main__":
    main()
