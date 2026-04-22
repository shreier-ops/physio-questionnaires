# BPPV Nystagmus Detector

PWA לזיהוי ניסטגמוס BPPV ממצלמה קדמית של טלפון, עם הנחיית תמרון בעברית ו-10 שפות נוספות.

## מבנה הפרויקט

```
nystagmus-bppv/
├── app/                        # PWA - האפליקציה הרפואית
│   ├── index.html              # אפליקציה מלאה (קובץ יחיד)
│   ├── i18n.js                 # 11 שפות
│   ├── manifest.json           # PWA manifest
│   └── sw.js                   # Service worker (offline)
├── data-pipeline/              # Python pipeline לאיסוף + אימון
│   ├── 1_search_videos.py      # חיפוש YouTube (metadata בלבד)
│   ├── 2_auto_label.py         # תיוג אוטומטי + ולידציה דרך תגובות
│   ├── 3_review_summary.py     # סיכום לסקירה ידנית
│   ├── 4_download_approved.py  # הורדת סרטונים מאושרים בלבד
│   ├── 5_extract_features.py   # MediaPipe iris tracking + feature extraction
│   ├── 6_augment.py            # Data augmentation על trajectories
│   ├── 7_train.py              # אימון + השוואת 7 מודלים
│   ├── requirements.txt
│   └── README.md               # הוראות הפעלה מפורטות
└── METHODOLOGY.md              # מסמך מתודולוגי (מאושר לפני אימון)
```

---

## האפליקציה (app/)

### זרימה
```
בחירת שפה → דיסקליימר → בחירת בדיקה → צילום 10 שניות → תוצאה → תמרון
```

### מה הולך לעשות
1. **MediaPipe Face Mesh** - מזהה iris בכל פריים (468 landmarks)
2. **Feature extraction** - מחשב ~25 פיצ'רים מ-trajectory של העיניים
3. **Classifier** - כלל-מבוסס (זמני) ← יוחלף במודל מאומן מ-pipeline
4. **Triage**:
   - `posterior_right/left` → Epley maneuver
   - `horizontal_geo` → BBQ Roll
   - `horizontal_apogeio` → BBQ Roll / Gufoni
   - `no_nystagmus` → הרגעה
   - `other_nystagmus` → **פנייה מיידית לרופא**

### שפות
עברית, English, 中文, हिन्दी, Español, Français, العربية, বাংলা, Русский, Português, اردو

### הפעלה מקומית
```bash
cd app/
python3 -m http.server 8080
# פתח http://localhost:8080
```

---

## Data Pipeline

### תנאי מקדים - אישור המשתמש
**⛔ המודל לא יאומן ללא אישור ידני של הסרטונים.**
ראה `data-pipeline/README.md` לתהליך המלא.

### זרימה
```
1_search  →  2_auto_label  →  🛑 סקירה ידנית  →  4_download  →  5_extract  →  6_augment  →  7_train
```

### מחלקות (6)
| Class | תיאור | תמרון |
|---|---|---|
| `no_nystagmus` | אין ניד | — |
| `posterior_right` | תעלה אחורית ימין | Epley ימין |
| `posterior_left` | תעלה אחורית שמאל | Epley שמאל |
| `horizontal_geo` | אופקית geotropic | BBQ Roll |
| `horizontal_apogeio` | אופקית apogeotropic | Gufoni |
| `other_nystagmus` | ניד שאינו BPPV | פנייה לרופא |

### מודלים שמושווים
RandomForest, XGBoost, SVM, LogisticRegression, MLP(sklearn), MLP(PyTorch), 1D-CNN

### קריטריוני קבלה קליניים
| מטריקה | ערך מינימלי |
|---|---|
| Accuracy | ≥ 99% |
| Sensitivity (BPPV classes) | ≥ 98% |
| Sensitivity (other_nystagmus) | ≥ 99% |
| Specificity (no_nystagmus) | ≥ 95% |
| F1 per class | ≥ 0.95 |
| AUC-ROC per class | ≥ 0.99 |

---

## סטטוס

- [x] PWA app scaffold (11 שפות, מצלמה, MediaPipe, classifier זמני)
- [x] Data pipeline (7 שלבים, human review, augmentation, multi-model training)
- [x] METHODOLOGY.md
- [ ] אימוץ מודל מאומן לתוך האפליקציה
- [ ] בדיקות קליניות

---

## הערות בטיחות

- כל העיבוד **מקומי בדפדפן** - לא נשלח וידאו לשום שרת
- Disclaimer מלא ב-11 שפות בכל פתיחה
- `other_nystagmus` תמיד מפנה לרופא, לעולם לא מנחה תמרון עצמאי
