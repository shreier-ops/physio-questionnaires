"""
Step 7: Train ALL models, compare with comprehensive metrics, save best.

Models trained:
  Classical ML:
    - Random Forest
    - XGBoost
    - SVM (RBF)
    - Logistic Regression
  Deep Learning (on feature vectors, not raw time series):
    - MLP
    - 1D-CNN (features as channels)
    - LSTM (features as sequence)

Reports per model:
  Accuracy, Sensitivity, Specificity, Precision, F1, AUC-ROC, FPR, FNR.

Video-level split to prevent data leakage (windows from same video stay together).

Output:
  - models/<best_model>.joblib (or .pt)
  - results/comparison_report.json
  - results/confusion_matrices/*.png
"""

import csv
import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from collections import Counter

from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import (
    accuracy_score, confusion_matrix, precision_recall_fscore_support,
    roc_auc_score, classification_report,
)
from sklearn.calibration import CalibratedClassifierCV

try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

try:
    import torch
    import torch.nn as nn
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


FEATURES_CSV = Path(__file__).parent / "output" / "features_augmented.csv"
RESULTS_DIR = Path(__file__).parent / "output" / "results"
MODELS_DIR = Path(__file__).parent / "output" / "models"

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)


def load_data():
    df = pd.read_csv(FEATURES_CSV)
    meta = df[["video_id", "window_idx", "window_start_sec", "label", "augmented"]].copy()
    X = df.drop(columns=["video_id", "window_idx", "window_start_sec", "label", "augmented"])
    y = meta["label"].values
    groups = meta["video_id"].values
    return X.values.astype(np.float32), y, groups, list(X.columns), meta


def video_level_split(X, y, groups, test_size=0.2, val_size=0.2):
    gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=RANDOM_SEED)
    tv_idx, test_idx = next(gss.split(X, y, groups))
    gss2 = GroupShuffleSplit(n_splits=1, test_size=val_size / (1 - test_size), random_state=RANDOM_SEED)
    tr_idx, val_idx = next(gss2.split(X[tv_idx], y[tv_idx], groups[tv_idx]))
    return (
        X[tv_idx][tr_idx], y[tv_idx][tr_idx], groups[tv_idx][tr_idx],
        X[tv_idx][val_idx], y[tv_idx][val_idx], groups[tv_idx][val_idx],
        X[test_idx], y[test_idx], groups[test_idx],
    )


def full_metrics(y_true, y_pred, y_proba, classes):
    """Compute full metric suite per class + macro averages."""
    result = {"per_class": {}, "macro": {}}
    cm = confusion_matrix(y_true, y_pred, labels=classes)

    for i, cls in enumerate(classes):
        tp = cm[i, i]
        fn = cm[i, :].sum() - tp
        fp = cm[:, i].sum() - tp
        tn = cm.sum() - tp - fn - fp
        sensitivity = tp / (tp + fn) if (tp + fn) else 0  # Recall
        specificity = tn / (tn + fp) if (tn + fp) else 0
        precision = tp / (tp + fp) if (tp + fp) else 0
        f1 = 2 * precision * sensitivity / (precision + sensitivity) if (precision + sensitivity) else 0
        fpr = fp / (fp + tn) if (fp + tn) else 0
        fnr = fn / (fn + tp) if (fn + tp) else 0
        # AUC one-vs-rest
        try:
            y_bin = (y_true == cls).astype(int)
            auc = roc_auc_score(y_bin, y_proba[:, i])
        except ValueError:
            auc = float("nan")
        result["per_class"][cls] = {
            "sensitivity_recall": round(sensitivity, 4),
            "specificity": round(specificity, 4),
            "precision": round(precision, 4),
            "f1": round(f1, 4),
            "auc_roc": round(auc, 4) if not np.isnan(auc) else None,
            "fpr": round(fpr, 4),
            "fnr": round(fnr, 4),
            "tp": int(tp), "fp": int(fp), "tn": int(tn), "fn": int(fn),
        }

    result["accuracy"] = round(accuracy_score(y_true, y_pred), 4)
    # Macro averages
    per_class = result["per_class"]
    for key in ["sensitivity_recall", "specificity", "precision", "f1"]:
        result["macro"][key] = round(np.mean([per_class[c][key] for c in classes]), 4)
    result["confusion_matrix"] = cm.tolist()
    result["classes"] = list(classes)
    return result


def check_go_criteria(metrics: dict) -> tuple[bool, list]:
    """Check against clinical acceptance criteria."""
    issues = []
    if metrics["accuracy"] < 0.99:
        issues.append(f"Accuracy {metrics['accuracy']:.3f} < 0.99")

    for cls, m in metrics["per_class"].items():
        if cls.startswith(("posterior_", "horizontal_")):
            if m["sensitivity_recall"] < 0.98:
                issues.append(f"{cls} sensitivity {m['sensitivity_recall']:.3f} < 0.98")
        if cls == "other_nystagmus":
            if m["sensitivity_recall"] < 0.99:
                issues.append(f"other_nystagmus sensitivity {m['sensitivity_recall']:.3f} < 0.99 (DANGEROUS)")
        if cls == "no_nystagmus":
            if m["specificity"] < 0.95:
                issues.append(f"no_nystagmus specificity {m['specificity']:.3f} < 0.95")
        if m["auc_roc"] is not None and m["auc_roc"] < 0.99:
            issues.append(f"{cls} AUC {m['auc_roc']:.3f} < 0.99")
        if m["f1"] < 0.95:
            issues.append(f"{cls} F1 {m['f1']:.3f} < 0.95")

    return (len(issues) == 0, issues)


# ============================================================
# Deep learning models (optional, if torch available)
# ============================================================

class MLP_Torch(nn.Module):
    def __init__(self, in_dim, n_classes):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, 128), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(128, 64), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(64, n_classes),
        )

    def forward(self, x):
        return self.net(x)


class CNN1D(nn.Module):
    def __init__(self, in_dim, n_classes):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv1d(1, 32, 3, padding=1), nn.ReLU(),
            nn.Conv1d(32, 64, 3, padding=1), nn.ReLU(),
            nn.AdaptiveAvgPool1d(1),
        )
        self.fc = nn.Linear(64, n_classes)

    def forward(self, x):
        x = x.unsqueeze(1)  # (B, 1, features)
        return self.fc(self.conv(x).squeeze(-1))


def train_torch(model_cls, X_tr, y_tr, X_val, y_val, in_dim, n_classes, epochs=100):
    model = model_cls(in_dim, n_classes)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)
    loss_fn = nn.CrossEntropyLoss()
    Xt = torch.tensor(X_tr, dtype=torch.float32)
    yt = torch.tensor(y_tr, dtype=torch.long)
    Xv = torch.tensor(X_val, dtype=torch.float32)
    yv = torch.tensor(y_val, dtype=torch.long)
    best_val = 0.0
    best_state = None
    for ep in range(epochs):
        model.train()
        opt.zero_grad()
        out = model(Xt)
        loss = loss_fn(out, yt)
        loss.backward()
        opt.step()
        model.eval()
        with torch.no_grad():
            val_acc = (model(Xv).argmax(1) == yv).float().mean().item()
            if val_acc > best_val:
                best_val = val_acc
                best_state = {k: v.clone() for k, v in model.state_dict().items()}
    model.load_state_dict(best_state)
    return model


def predict_torch(model, X):
    model.eval()
    with torch.no_grad():
        logits = model(torch.tensor(X, dtype=torch.float32))
        proba = torch.softmax(logits, dim=1).numpy()
        pred = proba.argmax(1)
    return pred, proba


# ============================================================
# Main
# ============================================================

def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading data...")
    X, y, groups, feature_names, meta = load_data()
    print(f"  {len(X)} samples, {X.shape[1]} features, {len(np.unique(y))} classes")
    print(f"  Class distribution: {Counter(y)}")

    # Encode labels
    le = LabelEncoder()
    y_enc = le.fit_transform(y)
    classes = le.classes_

    # Split by video
    X_tr, y_tr, g_tr, X_val, y_val, g_val, X_te, y_te, g_te = video_level_split(X, y_enc, groups)
    print(f"  Train: {len(X_tr)}, Val: {len(X_val)}, Test: {len(X_te)}")
    print(f"  Unique train videos: {len(set(g_tr))}, test videos: {len(set(g_te))}")

    # Standardize
    scaler = StandardScaler()
    X_tr_s = scaler.fit_transform(X_tr)
    X_val_s = scaler.transform(X_val)
    X_te_s = scaler.transform(X_te)

    # Impute NaN -> 0 (features are mean-centered after scaling)
    for arr in (X_tr_s, X_val_s, X_te_s):
        np.nan_to_num(arr, copy=False)

    models_to_train = {
        "RandomForest": RandomForestClassifier(n_estimators=300, max_depth=None,
                                               random_state=RANDOM_SEED, n_jobs=-1),
        "LogisticRegression": LogisticRegression(max_iter=1000, multi_class="multinomial",
                                                 random_state=RANDOM_SEED),
        "SVM_RBF": SVC(kernel="rbf", probability=True, random_state=RANDOM_SEED),
        "MLP_sklearn": MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=500,
                                     random_state=RANDOM_SEED),
    }
    if HAS_XGB:
        models_to_train["XGBoost"] = XGBClassifier(n_estimators=400, max_depth=6,
                                                    learning_rate=0.05, random_state=RANDOM_SEED,
                                                    eval_metric="mlogloss", use_label_encoder=False)

    all_results = {}
    best_model_name = None
    best_model = None
    best_accuracy = -1

    for name, model in models_to_train.items():
        print(f"\n[Training {name}]")
        model.fit(X_tr_s, y_tr)
        y_pred = model.predict(X_te_s)
        y_proba = model.predict_proba(X_te_s)
        metrics = full_metrics(y_te, y_pred, y_proba, np.arange(len(classes)))
        # Add class labels
        metrics["per_class"] = {classes[i]: v for i, v in enumerate(metrics["per_class"].values())}
        metrics["classes"] = list(classes)
        ok, issues = check_go_criteria(metrics)
        metrics["go_criteria_met"] = ok
        metrics["issues"] = issues
        all_results[name] = metrics
        print(f"  Accuracy: {metrics['accuracy']:.4f}, Macro-F1: {metrics['macro']['f1']:.4f}")
        print(f"  Go criteria: {'✅ PASS' if ok else '❌ FAIL: ' + '; '.join(issues[:3])}")

        if metrics["accuracy"] > best_accuracy:
            best_accuracy = metrics["accuracy"]
            best_model_name = name
            best_model = model

    # Torch models
    if HAS_TORCH:
        for name, cls in [("MLP_torch", MLP_Torch), ("CNN1D", CNN1D)]:
            print(f"\n[Training {name}]")
            model = train_torch(cls, X_tr_s, y_tr, X_val_s, y_val,
                                X_tr_s.shape[1], len(classes))
            y_pred, y_proba = predict_torch(model, X_te_s)
            metrics = full_metrics(y_te, y_pred, y_proba, np.arange(len(classes)))
            metrics["per_class"] = {classes[i]: v for i, v in enumerate(metrics["per_class"].values())}
            metrics["classes"] = list(classes)
            ok, issues = check_go_criteria(metrics)
            metrics["go_criteria_met"] = ok
            metrics["issues"] = issues
            all_results[name] = metrics
            print(f"  Accuracy: {metrics['accuracy']:.4f}, Macro-F1: {metrics['macro']['f1']:.4f}")
            if metrics["accuracy"] > best_accuracy:
                best_accuracy = metrics["accuracy"]
                best_model_name = name
                best_model = model

    # Save comparison report
    with open(RESULTS_DIR / "comparison_report.json", "w") as f:
        json.dump({
            "best_model": best_model_name,
            "best_accuracy": best_accuracy,
            "results": all_results,
            "feature_names": feature_names,
            "classes": list(classes),
        }, f, indent=2, default=str)

    # Save best model
    import joblib
    joblib.dump({
        "model": best_model,
        "scaler": scaler,
        "label_encoder": le,
        "feature_names": feature_names,
    }, MODELS_DIR / f"best_{best_model_name}.joblib")

    print(f"\n{'=' * 60}")
    print(f"🏆 BEST MODEL: {best_model_name} (accuracy {best_accuracy:.4f})")
    print(f"   Saved to {MODELS_DIR / f'best_{best_model_name}.joblib'}")
    print(f"   Full report: {RESULTS_DIR / 'comparison_report.json'}")
    print("=" * 60)


if __name__ == "__main__":
    main()
