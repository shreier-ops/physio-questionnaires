# מתודולוגיית אימון מודל BPPV Nystagmus Classifier

> מסמך זה מתאר את כל ההחלטות המתודולוגיות לפני שמתחיל אימון המודל.
> דורש אישור המשתמש לפני הרצה של pipeline האימון.

---

## 1. הגדרת הבעיה

**קלט:** רצף פריימים (~10-20 שניות) ממצלמה קדמית של טלפון, אדם מבצע מבחן פוזיציוני (Dix-Hallpike או Roll Test).

**פלט:** סיווג לאחד מ-6 מחלקות + confidence score:
| # | Class | תיאור קליני | Fast phase direction | פעולה |
|---|---|---|---|---|
| 0 | `no_nystagmus` | אין ניד משמעותי | — | הרגעה, המשך מעקב |
| 1 | `posterior_right` | תעלה אחורית ימין (Canalolithiasis) | Upbeat + torsional (clockwise לצופה) | תמרון Epley ימין |
| 2 | `posterior_left` | תעלה אחורית שמאל | Upbeat + torsional (counter-clockwise) | תמרון Epley שמאל |
| 3 | `horizontal_geo` | תעלה אופקית, geotropic | אופקי לכיוון האוזן התחתונה | תמרון BBQ Roll |
| 4 | `horizontal_apogeio` | תעלה אופקית, apogeotropic (cupulolithiasis) | אופקי רחוק מהאוזן התחתונה | תמרון Gufoni |
| 5 | `other_nystagmus` | ניד שאינו תואם BPPV | דפוס לא-פוזיציוני / מרכזי / רציף | **פנייה מיידית לרופא** |

**על class `other_nystagmus`:**
כולל ניסטגמוס ממקור מרכזי (CVA, גידול), דלקת עצב וסטיבולרי (Vestibular Neuritis), מחלת מנייר, ניסטגמוס מולד, ועוד. מאפיינים שיפנו לכאן:
- ניד ללא latency (מתחיל מיד, ללא השהיה)
- ניד שאינו נחלש עם חזרה על הבדיקה (לא fatiguable)
- כיוון משתנה
- ניד אנכי טהור downbeat
- ניד שאינו קשור לתנועת הראש
המסר למשתמש: *"דפוס תנועת העין אינו מתאים לסחרחורת ממקור קריסטלים. מומלץ לפנות לרופא לבירור רפואי בהקדם."*

**הערה:** תעלה קדמית (Anterior, <1%) תסווג כ-`other_nystagmus` עם הסבר ספציפי. לא נבנה class נפרד לה.

---

## 2. ארכיטקטורת המודלים - השוואה מלאה

יעד הדיוק: **≥99% accuracy, FP ו-FN מזעריים** - דרישה רפואית.

לכן נאמן **כל המודלים** ונבחר לפי מדדים, לא לפי הנחות מוקדמות.

### Pipeline משותף לכל המודלים:
`MediaPipe iris tracking → feature extraction → [כל מודל] → comparison`

### מודלים שייבדקו:

#### קבוצה א: Classical ML (על feature vectors)
| מודל | יתרונות | חסרונות |
|---|---|---|
| Random Forest | Robust, interpretable, feature importance | לא בהכרח מגיע ל-99% |
| XGBoost | בד"כ הכי חזק ב-tabular data | Overfitting על דאטה קטן |
| SVM (RBF kernel) | טוב עם feature vectors | איטי על דאטה גדול |
| Logistic Regression | Baseline interpretable | ליניארי, לא מספיק מורכב |

#### קבוצה ב: Deep Learning על time series
| מודל | יתרונות | חסרונות |
|---|---|---|
| LSTM / BiLSTM | תופס temporal patterns של הניד | דורש יותר דאטה |
| 1D-CNN | מהיר, תופס local patterns | פחות context ארוך-טווח |
| Transformer (TinyBERT-style) | SOTA ב-time series | הכי כבד, דורש הכי הרבה דאטה |
| 1D-CNN + LSTM hybrid | balance בין מהירות לcontext | מורכב יותר לאמן |

#### קבוצה ג: Ensemble (אם נצטרך)
- Voting בין top-3 מודלים
- Stacking: ML models כ-meta-learner על DL predictions

### תהליך הבחירה:
1. אימון כל מודל על אותו train set
2. השוואה על validation set לפי מדדים
3. Top-2 מודלים → test set
4. המודל שמגיע ל-99% accuracy עם FP/FN מינימלי → deployment
5. אם אף מודל לא עובר → **לא deploy. אוספים עוד דאטה.**

---

## 3. פיצ'רים שיוחצו מה-iris trajectory

מכל הקלטה (חלון של 10 שניות אחרי תחילת המבחן):

**פיצ'רי כיוון (direction features):**
- `h_velocity_peak` - מהירות אופקית מקסימלית של ה-fast phase
- `v_velocity_peak` - מהירות אנכית מקסימלית (upbeat vs downbeat)
- `fast_phase_angle` - זווית הדומיננטית של ה-beat (0°=ימין, 90°=מעלה)
- `beat_direction_right/left/up/down` - ספירת beats לכל כיוון

**פיצ'רי תדירות (frequency features):**
- `dominant_frequency` - תדירות הניד (FFT)
- `beat_count` - מספר beats בחלון
- `regularity` - רגולריות הניד (std של intervals)

**פיצ'רי amplitude:**
- `h_amplitude` - משרעת אופקית
- `v_amplitude` - משרעת אנכית
- `total_displacement` - סה"כ תנועה

**פיצ'רי סינכרוניזציה בין עיניים:**
- `binocular_correlation_h` - קורלציה אופקית בין שתי העיניים
- `binocular_correlation_v` - קורלציה אנכית
- `torsional_proxy` - אינדיקטור עקיף ל-torsion (הפרש vertical בין עיניים)

**פיצ'רים זמניים:**
- `latency` - זמן מתחילת ההקלטה עד תחילת הניד
- `duration` - משך הניד
- `fatigability` - ירידה ב-amplitude לאורך זמן

**סה"כ:** ~20 פיצ'רים - מספיק דיוק, לא overfitting.

---

## 4. בחירת אלגוריתם

**Random Forest** כבחירה ראשונה, מסיבות:
1. עובד טוב על tabular data עם פיצ'רים מעטים
2. עמיד ל-outliers ופיצ'רים לא מנורמלים
3. מספק feature importance - נראה אילו פיצ'רים הכי חשובים
4. לא דורש המון tuning
5. אפשר לייצא ל-JS (via ONNX או tree-to-code) לריצה בדפדפן

**השוואה נגד:**
- XGBoost - לרוב דומה, נבדוק בcross-validation
- Logistic Regression - baseline, נבדוק גם
- SVM - איטי יותר, נדלג

---

## 5. מקורות דאטה

### מקור ראשי: YouTube
שאילתות חיפוש (נוריד metadata ונסנן - **כמה שיותר, בלי הגבלה**):
```
"posterior canal BPPV nystagmus dix-hallpike"
"horizontal canal BPPV geotropic roll test"
"apogeotropic nystagmus cupulolithiasis"
"vestibular neuritis nystagmus"
"Meniere's disease nystagmus"
"central nystagmus stroke"
"BPPV patient nystagmus eye movement"
"downbeat nystagmus"
"direction changing nystagmus"
```

מקורות מועדפים (clinicians/teaching channels):
- Peter Johns MD
- Vestibular Today / Vestibular First
- Timothy Hain MD
- Neurology Online Learning
- ערוצי פיזיותרפיה וסטיבולרית

### כמות מטרה
**כמה שיותר - הסקריפט מחפש ומוריד metadata של כל סרטון רלוונטי, ללא הגבלה עליונה.**
- כל סרטון מפיק 1-5 חלונות של 10 שניות
- יעד לפני augmentation: ≥100 real samples per class

### מקור ב: Data Augmentation (סינטטי)
כדי להגדיל דאטה ולשפר generalization:

| טכניקה | תיאור | אפקט על label |
|---|---|---|
| **Mirror flip אופקי** | תמונת מראה של הסרטון | `posterior_right` ↔ `posterior_left`, `geo` ↔ `apogeio` |
| **Grayscale** | הסרת צבע | אותו label |
| **Gaussian noise על iris coords** | רעש קטן על הנקודות | אותו label |
| **Time stretch** | האטה/האצה של הרצף ב-±20% | אותו label |
| **Brightness/contrast simulation** | שינוי תאורה | אותו label |
| **Simulated distance** | scale up/down של iris coordinates | אותו label |
| **Random time window crop** | חלון מתחיל בנקודה שונה | אותו label |

**Mirror flip הוא הכי חשוב:** מכפיל דאטה + פותר בעיית bias (סרטוני הדרכה לרוב מדגימים רק כיוון אחד).

**מה לא לעשות ב-augmentation:**
- ❌ שינוי כיוון אנכי (upbeat/downbeat) - ישנה את האבחנה
- ❌ שינוי תדירות יותר מ-±20%
- ❌ Flip אנכי - ישנה את המשמעות

**יעד אחרי augmentation:** ≥500 samples per class

---

## 6. תהליך Auto-Labeling + Validation

### שלב 1: Keyword parser על כותרת
```python
title = "Left posterior canal BPPV Dix-Hallpike nystagmus"
→ { "canal": "posterior", "side": "left", "confidence": 0.95 }
```

### שלב 2: Comment validation
- מוריד top 20 תגובות (לפי likes) עם yt-dlp
- מחפש patterns של dispute:
  - Red flags: `"wrong"`, `"incorrect"`, `"actually"`, `"should be"`, `"this is"`, `"misdiagnos"`, `"not posterior"`, `"it's horizontal"`
  - Green flags: `"correct"`, `"great example"`, `"textbook"`, `"classic"`
- Confidence score = `title_confidence × comment_validation_factor`

### שלב 3: Human Review (**חובה לפני אימון**)
סקריפט מייצר `videos_for_review.csv`:
```
video_id | url | title | auto_label | confidence | red_flag_count | top_3_comments | YOUR_DECISION
abc123   | ... | ...   | post_left  | 0.92       | 0              | "great example"| [approve/reject/relabel]
```
אתה עובר עליו ב-Excel/Numbers. המערכת קוראת רק שורות עם `approve` או `relabel:new_class`.

### שלב 4: Feature extraction רק על מאושרים
רץ רק אחרי שהקובץ עבר סקירה שלך.

---

## 7. Train/Val/Test Split

- **60% train / 20% validation / 20% test**
- Split לפי `video_id`, לא לפי sample - מונע data leakage (חלונות מאותו סרטון לא יתחלקו בין train/test)
- Stratified לפי class
- Test set "נעול" - לא מסתכלים עד הסוף

---

## 8. מטריקות הערכה המלאות

לכל מודל ולכל class יחושבו המדדים הבאים:

| מדד | הגדרה | למה חשוב כאן |
|---|---|---|
| **Accuracy** | (TP+TN)/(כולל) | תמונה כוללת |
| **Sensitivity (Recall)** | TP/(TP+FN) | לא להחמיץ ניסטגמוס אמיתי |
| **Specificity** | TN/(TN+FP) | לא לאבחן בריא כחולה |
| **Precision** | TP/(TP+FP) | כמה מהתוצאות החיוביות נכונות |
| **F1 Score** | 2×(P×R)/(P+R) | balance בין precision לrecall |
| **AUC-ROC** | שטח מתחת לעקומת ROC | ביצועים על סף משתנה |
| **False Positive Rate** | FP/(FP+TN) | אבחנת יתר |
| **False Negative Rate** | FN/(FN+TP) | החמצת מחלה |

**דגש מיוחד על `other_nystagmus`:**
- FN גבוה = מטופל עם CVA/נוירולוגיה מסווג כ-BPPV → **מסוכן מאוד**
- Recall של class זה חייב ≥ 99%

**דגש מיוחד על `no_nystagmus`:**
- FP גבוה = אדם בריא מאובחן כחולה → תמרון מיותר
- Specificity ≥ 95%

### קריטריוני קבלה (go/no-go):
| מדד | דרישה |
|---|---|
| Accuracy כוללת | ≥ 99% |
| Sensitivity לכל BPPV class | ≥ 98% |
| Sensitivity של `other_nystagmus` | ≥ 99% |
| Specificity של `no_nystagmus` | ≥ 95% |
| AUC-ROC כל class | ≥ 0.99 |
| F1 כל class | ≥ 0.95 |

**אם מודל לא עובר → לא deploy. אוספים עוד דאטה ומשפרים פיצ'רים.**

---

## 9. Calibration & Confidence

המודל יחזיר הסתברות לכל class. נעשה **Platt scaling** על validation set כדי שההסתברויות יהיו מכוילות (calibrated).

בזמן ריצה:
- אם `max(probability) < 0.6` → מחזיר "Uncertain, retry test"
- אם `0.6 ≤ p < 0.8` → מחזיר תוצאה עם label "Low confidence, consult physician"
- אם `p ≥ 0.8` → מחזיר תוצאה רגילה עם הנחיית תמרון

---

## 10. מה לא נעשה (מגבלות מודעות)

- ❌ **לא** נאבחן torsion ישירות (דורש VOG, לא אפשרי במצלמה קדמית). ניעזר ב-proxy features.
- ❌ **לא** נתמודד עם מצבים מורכבים (multiple canals, central nystagmus) - נציין "out of scope" ונמליץ לפנות לרופא
- ❌ **לא** נחליף רופא - זה כלי תמיכה בלבד
- ❌ **לא** נאסוף PII של המשתמש - כל העיבוד מקומי בדפדפן

---

## 11. תיוג בטיחות

כל פלט יכלול:
- Disclaimer רפואי
- Confidence score
- המלצה לפנייה לרופא במקרה של:
  - Confidence נמוכה
  - סימפטומים מדאיגים (כאב ראש חמור, חולשה, דיבור משובש) - נציג checklist

---

## 12. סיכום החלטות (מעודכן לפי שיחה)

| # | נושא | החלטה |
|---|---|---|
| 1 | **Classes** | 6 classes: no_nystagmus, posterior_right, posterior_left, horizontal_geo, horizontal_apogeio, other_nystagmus. **ללא** Anterior canal נפרד. ✅ אושר |
| 2 | **מודלים** | נאמן **את כל המודלים** (RF, XGBoost, SVM, LR, LSTM, CNN, Transformer, Ensemble) ונבחר לפי מדדים. ✅ אושר |
| 3 | **כמות דאטה** | כמה שיותר - ללא הגבלה עליונה. יעד ≥100 real samples per class לפני augmentation. ✅ אושר |
| 4 | **יעד דיוק** | ≥99% accuracy, FP/FN מינימלי. ✅ אושר |
| 5 | **Human Review** | ✅ אושר - קובץ CSV לסקירה לפני כל אימון |
| 6 | **מקורות** | YouTube בלבד + Data Augmentation (mirror flip, grayscale, noise, time stretch, distance). ✅ אושר |

### עדיין ממתין לתשובה:
- המשפט "לגבי שאלות:" - מה רצית להוסיף?

---

*כשאישור מלא יתקבל → מתחיל לבנות pipeline + אפליקציה.*
