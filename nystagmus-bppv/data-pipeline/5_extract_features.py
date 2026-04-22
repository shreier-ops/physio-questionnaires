"""
Step 5: Extract iris trajectories and features from approved videos.

Uses MediaPipe Face Mesh (with refine_landmarks=True for iris).
For each video:
  - Detect face + iris in each frame
  - Extract iris (x,y) time series for both eyes
  - Slide a 10-second window across the trajectory
  - Compute ~20 features per window
  - Save as feature row with the video's label

Output: features.csv (one row per 10-sec window)
"""

import csv
import cv2
import numpy as np
import mediapipe as mp
from pathlib import Path
from scipy.fft import rfft, rfftfreq
from scipy.signal import find_peaks
from tqdm import tqdm

APPROVED_CSV = Path(__file__).parent / "output" / "approved_videos.csv"
FEATURES_CSV = Path(__file__).parent / "output" / "features.csv"
TRAJECTORIES_DIR = Path(__file__).parent / "output" / "trajectories"

WINDOW_SEC = 10.0
WINDOW_STRIDE_SEC = 5.0  # 50% overlap

# MediaPipe iris landmark indices
RIGHT_IRIS = [469, 470, 471, 472]  # right eye iris (from viewer's perspective: subject's left)
LEFT_IRIS = [474, 475, 476, 477]
RIGHT_EYE_CENTER_REF = 33  # outer corner of right eye
LEFT_EYE_CENTER_REF = 263  # outer corner of left eye


def extract_trajectory(video_path: Path) -> tuple[np.ndarray, float]:
    """
    Returns (trajectory, fps) where trajectory is shape (T, 4):
    columns = [right_x, right_y, left_x, left_y], normalized.
    """
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

    mp_face = mp.solutions.face_mesh
    face = mp_face.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    trajectory = []
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face.process(rgb)
        if not results.multi_face_landmarks:
            trajectory.append([np.nan] * 4)
            continue
        lms = results.multi_face_landmarks[0].landmark
        # Iris centers (avg of 4 points)
        rx = np.mean([lms[i].x for i in RIGHT_IRIS])
        ry = np.mean([lms[i].y for i in RIGHT_IRIS])
        lx = np.mean([lms[i].x for i in LEFT_IRIS])
        ly = np.mean([lms[i].y for i in LEFT_IRIS])
        # Normalize by inter-pupillary distance to be scale-invariant
        ipd = np.sqrt((lms[LEFT_EYE_CENTER_REF].x - lms[RIGHT_EYE_CENTER_REF].x) ** 2 +
                      (lms[LEFT_EYE_CENTER_REF].y - lms[RIGHT_EYE_CENTER_REF].y) ** 2)
        if ipd < 1e-6:
            trajectory.append([np.nan] * 4)
            continue
        trajectory.append([rx / ipd, ry / ipd, lx / ipd, ly / ipd])

    cap.release()
    face.close()
    return np.array(trajectory), fps


def compute_features(window: np.ndarray, fps: float) -> dict:
    """
    Compute clinical features from a (T, 4) window.
    Returns dict of named features.
    """
    f = {}
    # Drop NaN rows for analysis
    mask = ~np.any(np.isnan(window), axis=1)
    valid = window[mask]
    if len(valid) < 10:
        return None  # Not enough valid frames

    # Mean position (subtract baseline)
    centered = valid - valid.mean(axis=0)
    rx, ry, lx, ly = centered[:, 0], centered[:, 1], centered[:, 2], centered[:, 3]

    # Velocities (numerical derivative)
    dt = 1.0 / fps
    vx_r = np.diff(rx) / dt
    vy_r = np.diff(ry) / dt
    vx_l = np.diff(lx) / dt
    vy_l = np.diff(ly) / dt

    # Average horizontal/vertical velocity (both eyes)
    vx = (vx_r + vx_l) / 2
    vy = (vy_r + vy_l) / 2

    # === Direction features ===
    f["h_velocity_peak"] = float(np.max(np.abs(vx)))
    f["v_velocity_peak"] = float(np.max(np.abs(vy)))
    f["h_velocity_mean"] = float(np.mean(np.abs(vx)))
    f["v_velocity_mean"] = float(np.mean(np.abs(vy)))

    # Fast phase angle: dominant direction of high-velocity moments
    speed = np.sqrt(vx ** 2 + vy ** 2)
    high_idx = np.where(speed > np.percentile(speed, 75))[0]
    if len(high_idx) > 0:
        ang = np.arctan2(vy[high_idx], vx[high_idx])
        f["fast_phase_angle_mean"] = float(np.mean(ang))
        f["fast_phase_angle_std"] = float(np.std(ang))
    else:
        f["fast_phase_angle_mean"] = 0.0
        f["fast_phase_angle_std"] = 0.0

    # Beat counts per direction
    f["beats_right"] = int(np.sum(vx > 0.5 * np.std(vx)))
    f["beats_left"] = int(np.sum(vx < -0.5 * np.std(vx)))
    f["beats_up"] = int(np.sum(vy < -0.5 * np.std(vy)))  # screen y is inverted
    f["beats_down"] = int(np.sum(vy > 0.5 * np.std(vy)))

    # === Frequency features (FFT) ===
    n = len(rx)
    if n > 8:
        freqs = rfftfreq(n, dt)
        spec_x = np.abs(rfft(rx))
        spec_y = np.abs(rfft(ry))
        # Skip DC component
        if len(spec_x) > 1:
            f["dominant_freq_h"] = float(freqs[1 + np.argmax(spec_x[1:])])
            f["dominant_freq_v"] = float(freqs[1 + np.argmax(spec_y[1:])])
            f["spectral_energy_h"] = float(np.sum(spec_x[1:] ** 2))
            f["spectral_energy_v"] = float(np.sum(spec_y[1:] ** 2))
        else:
            f["dominant_freq_h"] = f["dominant_freq_v"] = 0.0
            f["spectral_energy_h"] = f["spectral_energy_v"] = 0.0
    else:
        f["dominant_freq_h"] = f["dominant_freq_v"] = 0.0
        f["spectral_energy_h"] = f["spectral_energy_v"] = 0.0

    # === Amplitude ===
    f["h_amplitude"] = float(np.max(rx) - np.min(rx))
    f["v_amplitude"] = float(np.max(ry) - np.min(ry))
    f["total_displacement"] = float(np.sum(np.sqrt(np.diff(rx) ** 2 + np.diff(ry) ** 2)))

    # === Binocular sync ===
    if len(rx) > 2:
        f["binocular_corr_h"] = float(np.corrcoef(rx, lx)[0, 1])
        f["binocular_corr_v"] = float(np.corrcoef(ry, ly)[0, 1])
    else:
        f["binocular_corr_h"] = f["binocular_corr_v"] = 0.0

    # Torsional proxy: vertical difference between eyes
    f["torsional_proxy"] = float(np.std(ry - ly))

    # === Beat regularity ===
    peaks_x, _ = find_peaks(np.abs(vx), height=np.std(vx))
    if len(peaks_x) > 1:
        intervals = np.diff(peaks_x) / fps
        f["beat_count"] = len(peaks_x)
        f["beat_regularity"] = float(1.0 / (1.0 + np.std(intervals)))
    else:
        f["beat_count"] = len(peaks_x)
        f["beat_regularity"] = 0.0

    # === Latency: time until significant motion starts ===
    moving = speed > 2 * np.median(speed)
    if np.any(moving):
        f["latency_sec"] = float(np.argmax(moving) / fps)
    else:
        f["latency_sec"] = WINDOW_SEC

    # === Fatigability: amplitude drop from first to last third ===
    third = len(speed) // 3
    if third > 0:
        first_amp = np.std(speed[:third])
        last_amp = np.std(speed[-third:])
        f["fatigability"] = float((first_amp - last_amp) / (first_amp + 1e-6))
    else:
        f["fatigability"] = 0.0

    # === Validity ===
    f["valid_frame_ratio"] = float(mask.sum() / len(window))

    return f


def slide_windows(traj: np.ndarray, fps: float):
    """Yield (start_sec, window_array) for each 10-sec window."""
    win_n = int(WINDOW_SEC * fps)
    stride_n = int(WINDOW_STRIDE_SEC * fps)
    for start in range(0, len(traj) - win_n + 1, stride_n):
        yield start / fps, traj[start:start + win_n]


def main():
    TRAJECTORIES_DIR.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader(open(APPROVED_CSV, encoding="utf-8")))

    all_features = []
    for v in tqdm(rows, desc="Extracting"):
        path = Path(v["local_path"])
        if not path.exists() or path.stat().st_size == 0:
            continue
        try:
            traj, fps = extract_trajectory(path)
        except Exception as e:
            print(f"Error on {v['video_id']}: {e}")
            continue

        # Save trajectory for later (augmentation, debugging)
        np.save(TRAJECTORIES_DIR / f"{v['video_id']}.npy", traj)

        for win_idx, (start_sec, window) in enumerate(slide_windows(traj, fps)):
            feats = compute_features(window, fps)
            if feats is None or feats["valid_frame_ratio"] < 0.7:
                continue
            feats["video_id"] = v["video_id"]
            feats["window_idx"] = win_idx
            feats["window_start_sec"] = round(start_sec, 2)
            feats["label"] = v["final_label"]
            feats["augmented"] = "no"
            all_features.append(feats)

    if all_features:
        keys = list(all_features[0].keys())
        with open(FEATURES_CSV, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(all_features)
        print(f"✅ Extracted {len(all_features)} feature rows → {FEATURES_CSV}")
    else:
        print("❌ No features extracted")


if __name__ == "__main__":
    main()
