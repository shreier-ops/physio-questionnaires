# Data Pipeline

7-step pipeline from YouTube search → trained model. **Step 3 requires manual review.**

## Setup
```bash
cd ~/CLAUDE/nystagmus-bppv/data-pipeline
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Pipeline

### 1. Search YouTube
```bash
python 1_search_videos.py
```
Outputs: `output/candidates.csv` - all videos found per search query (no download).

### 2. Auto-label + comment validation
```bash
python 2_auto_label.py
```
For each candidate:
- Parses title with keyword classifier → `auto_label`, `title_confidence`
- Downloads top 20 comments → checks for dispute/confirm signals
- Computes `final_confidence = title_conf × validation_factor`

Outputs: `output/labeled_for_review.csv` with empty `YOUR_DECISION` column.

### 3. 🛑 HUMAN REVIEW (MANDATORY)
Open `output/labeled_for_review.csv` in Excel/Numbers/Google Sheets.
For each row, fill `YOUR_DECISION` with one of:
- `approve` — use video as-is
- `reject` — exclude from training
- `relabel:posterior_left` — use video but with this label instead

Sort by `final_confidence` ascending — review low-confidence and high-dispute rows carefully.

```bash
python 3_review_summary.py    # see decision counts + class balance
```

### 4. Download approved videos
```bash
python 4_download_approved.py
```
Downloads only `approve`/`relabel` videos to `output/videos/`.

### 5. Extract iris features
```bash
python 5_extract_features.py
```
Runs MediaPipe face mesh → iris (x,y) trajectory → 10-sec sliding windows → ~25 features per window.

Outputs: `output/features.csv` and `output/trajectories/<video_id>.npy`.

### 6. Augment data
```bash
python 6_augment.py
```
Generates synthetic samples: mirror flip (with label swap), Gaussian noise, time stretch, distance scale.

Outputs: `output/features_augmented.csv` (real + augmented).

### 7. Train + compare ALL models
```bash
python 7_train.py
```
Trains: RandomForest, XGBoost, SVM, LogisticRegression, MLP (sklearn), MLP (PyTorch), 1D-CNN.

Reports per model: Accuracy, Sensitivity, Specificity, Precision, F1, AUC-ROC, FPR, FNR.
Checks against go-criteria (≥99% accuracy, ≥99% recall for `other_nystagmus`, etc.).

Outputs:
- `output/results/comparison_report.json` - full metrics
- `output/models/best_<name>.joblib` - the winning model

## Outputs structure
```
output/
├── candidates.csv             # step 1
├── labeled_for_review.csv     # step 2 (you fill YOUR_DECISION)
├── approved_videos.csv        # step 4
├── videos/<id>.mp4            # step 4
├── trajectories/<id>.npy      # step 5
├── features.csv               # step 5
├── features_augmented.csv     # step 6
├── results/comparison_report.json  # step 7
└── models/best_*.joblib       # step 7
```
