// 11 languages: Hebrew + top 10 world languages
const LANGS = {
  he: { name: "עברית", dir: "rtl" },
  en: { name: "English", dir: "ltr" },
  zh: { name: "中文", dir: "ltr" },
  hi: { name: "हिन्दी", dir: "ltr" },
  es: { name: "Español", dir: "ltr" },
  fr: { name: "Français", dir: "ltr" },
  ar: { name: "العربية", dir: "rtl" },
  bn: { name: "বাংলা", dir: "ltr" },
  ru: { name: "Русский", dir: "ltr" },
  pt: { name: "Português", dir: "ltr" },
  ur: { name: "اردو", dir: "rtl" }
};

const T = {
  title: {
    he: "גלאי BPPV", en: "BPPV Detector", zh: "BPPV检测器", hi: "BPPV डिटेक्टर",
    es: "Detector BPPV", fr: "Détecteur BPPV", ar: "كاشف BPPV", bn: "BPPV ডিটেক্টর",
    ru: "Детектор BPPV", pt: "Detector BPPV", ur: "BPPV ڈٹیکٹر"
  },
  subtitle: {
    he: "זיהוי ניסטגמוס וסחרחורת פוזיציונלית",
    en: "Nystagmus & positional vertigo detection",
    zh: "眼球震颤与位置性眩晕检测",
    hi: "निस्टागमस और स्थितीय चक्कर का पता लगाना",
    es: "Detección de nistagmo y vértigo posicional",
    fr: "Détection du nystagmus et vertige positionnel",
    ar: "كشف الرأرأة والدوار الوضعي",
    bn: "নিস্ট্যাগমাস এবং অবস্থানগত ভার্টিগো সনাক্তকরণ",
    ru: "Выявление нистагма и позиционного головокружения",
    pt: "Detecção de nistagmo e vertigem posicional",
    ur: "نسٹگمس اور پوزیشنل چکر کی تشخیص"
  },
  disclaimer: {
    he: "⚠️ כלי תמיכה קלינית בלבד. אינו מחליף אבחון רפואי. פנה/י לרופא במקרה של תסמינים חמורים.",
    en: "⚠️ Clinical support tool only. Not a substitute for medical diagnosis. Consult a physician for severe symptoms.",
    zh: "⚠️ 仅为临床辅助工具。不能替代医学诊断。症状严重请就医。",
    hi: "⚠️ केवल नैदानिक सहायक उपकरण। चिकित्सा निदान का विकल्प नहीं। गंभीर लक्षणों के लिए चिकित्सक से परामर्श करें।",
    es: "⚠️ Solo herramienta de apoyo clínico. No sustituye el diagnóstico médico. Consulte a un médico en caso de síntomas graves.",
    fr: "⚠️ Outil d'aide clinique uniquement. Ne remplace pas un diagnostic médical. Consultez un médecin en cas de symptômes graves.",
    ar: "⚠️ أداة دعم سريري فقط. ليست بديلاً عن التشخيص الطبي. استشر الطبيب في حالة الأعراض الشديدة.",
    bn: "⚠️ শুধুমাত্র ক্লিনিকাল সহায়তা সরঞ্জাম। চিকিৎসা নির্ণয়ের বিকল্প নয়। গুরুতর লক্ষণের জন্য ডাক্তারের পরামর্শ নিন।",
    ru: "⚠️ Только вспомогательный клинический инструмент. Не заменяет медицинскую диагностику. При серьёзных симптомах обратитесь к врачу.",
    pt: "⚠️ Apenas ferramenta de apoio clínico. Não substitui o diagnóstico médico. Consulte um médico em caso de sintomas graves.",
    ur: "⚠️ صرف طبی معاونت کا آلہ۔ طبی تشخیص کا متبادل نہیں۔ شدید علامات کی صورت میں ڈاکٹر سے رجوع کریں۔"
  },
  selectLang: {
    he: "בחר/י שפה", en: "Select language", zh: "选择语言", hi: "भाषा चुनें",
    es: "Seleccionar idioma", fr: "Choisir la langue", ar: "اختر اللغة",
    bn: "ভাষা নির্বাচন করুন", ru: "Выберите язык", pt: "Selecionar idioma", ur: "زبان منتخب کریں"
  },
  start: {
    he: "התחל בדיקה", en: "Start test", zh: "开始测试", hi: "परीक्षण शुरू करें",
    es: "Iniciar prueba", fr: "Commencer le test", ar: "ابدأ الفحص",
    bn: "পরীক্ষা শুরু করুন", ru: "Начать тест", pt: "Iniciar teste", ur: "ٹیسٹ شروع کریں"
  },
  selectTest: {
    he: "באיזו תנוחה את/ה?", en: "Which position are you in?", zh: "您目前处于哪种姿势？",
    hi: "आप किस स्थिति में हैं?", es: "¿En qué posición está?", fr: "Dans quelle position êtes-vous ?",
    ar: "ما هو الوضع الذي أنت فيه؟", bn: "আপনি কোন অবস্থানে আছেন?",
    ru: "В каком положении вы находитесь?", pt: "Em que posição está?", ur: "آپ کس پوزیشن میں ہیں؟"
  },
  dhRight: {
    he: "Dix-Hallpike ימין (ראש פנה לימין, שכיבה אחורה)",
    en: "Dix-Hallpike right (head turned right, lying back)",
    zh: "Dix-Hallpike 右侧（头转向右，仰卧）",
    hi: "Dix-Hallpike दाईं ओर (सिर दाईं ओर, पीठ के बल लेटे)",
    es: "Dix-Hallpike derecha (cabeza a la derecha, tumbado hacia atrás)",
    fr: "Dix-Hallpike droite (tête tournée à droite, allongé)",
    ar: "ديكس-هالبايك يمين (الرأس نحو اليمين، الاستلقاء للخلف)",
    bn: "Dix-Hallpike ডানদিকে (মাথা ডানে ঘুরিয়ে, পিছনে শুয়ে)",
    ru: "Дикс-Холлпайк справа (голова повёрнута вправо, лёжа)",
    pt: "Dix-Hallpike direita (cabeça à direita, deitado)",
    ur: "ڈکس ہالپائیک دائیں (سر دائیں طرف، پیٹھ کے بل لیٹے)"
  },
  dhLeft: {
    he: "Dix-Hallpike שמאל", en: "Dix-Hallpike left", zh: "Dix-Hallpike 左侧",
    hi: "Dix-Hallpike बाईं ओर", es: "Dix-Hallpike izquierda", fr: "Dix-Hallpike gauche",
    ar: "ديكس-هالبايك يسار", bn: "Dix-Hallpike বামে",
    ru: "Дикс-Холлпайк слева", pt: "Dix-Hallpike esquerda", ur: "ڈکس ہالپائیک بائیں"
  },
  rollTest: {
    he: "Roll Test (שכיבה, סיבוב ראש)", en: "Roll Test (supine, head roll)",
    zh: "Roll 测试（仰卧，头部翻转）", hi: "Roll टेस्ट (पीठ के बल, सिर घुमाएं)",
    es: "Roll Test (supino, giro de cabeza)", fr: "Roll Test (décubitus, rotation de la tête)",
    ar: "اختبار الدوران (الاستلقاء، لف الرأس)", bn: "Roll পরীক্ষা (পিঠে শুয়ে, মাথা ঘুরান)",
    ru: "Roll-тест (на спине, поворот головы)", pt: "Teste de Roll (decúbito, rotação da cabeça)",
    ur: "رول ٹیسٹ (پیٹھ کے بل، سر گھمائیں)"
  },
  recordingInstructions: {
    he: "החזק/י את הפלאפון במרחק 25-30 ס\"מ מהפנים. הסתכל/י ישר למצלמה. הבדיקה תתחיל בעוד",
    en: "Hold the phone 25-30 cm from your face. Look directly at the camera. Test begins in",
    zh: "将手机距离脸部25-30厘米。直视摄像头。测试开始倒计时",
    hi: "फोन को चेहरे से 25-30 सेमी दूर रखें। सीधे कैमरे की ओर देखें। परीक्षण शुरू होगा",
    es: "Sostenga el teléfono a 25-30 cm de la cara. Mire directamente a la cámara. La prueba comienza en",
    fr: "Tenez le téléphone à 25-30 cm du visage. Regardez directement la caméra. Le test commence dans",
    ar: "امسك الهاتف على بعد 25-30 سم من الوجه. انظر مباشرة إلى الكاميرا. يبدأ الاختبار خلال",
    bn: "ফোনটি মুখ থেকে 25-30 সেমি দূরে রাখুন। সরাসরি ক্যামেরায় তাকান। পরীক্ষা শুরু হবে",
    ru: "Держите телефон на расстоянии 25-30 см от лица. Смотрите прямо в камеру. Тест начнётся через",
    pt: "Segure o telefone a 25-30 cm do rosto. Olhe diretamente para a câmera. O teste começa em",
    ur: "فون کو چہرے سے 25-30 سینٹی میٹر دور رکھیں۔ براہ راست کیمرے کی طرف دیکھیں۔ ٹیسٹ شروع ہوگا"
  },
  analyzing: {
    he: "מנתח תנועות עיניים...", en: "Analyzing eye movements...", zh: "分析眼球运动...",
    hi: "आंखों की गति का विश्लेषण...", es: "Analizando movimientos oculares...",
    fr: "Analyse des mouvements oculaires...", ar: "تحليل حركات العين...",
    bn: "চোখের নড়াচড়া বিশ্লেষণ...", ru: "Анализ движений глаз...",
    pt: "Analisando movimentos oculares...", ur: "آنکھوں کی حرکت کا تجزیہ..."
  },
  noNystagmus: {
    he: "לא זוהה ניסטגמוס משמעותי", en: "No significant nystagmus detected",
    zh: "未检测到明显的眼球震颤", hi: "कोई महत्वपूर्ण निस्टागमस नहीं मिला",
    es: "No se detectó nistagmo significativo", fr: "Aucun nystagmus significatif détecté",
    ar: "لم يتم اكتشاف رأرأة كبيرة", bn: "কোনো উল্লেখযোগ্য নিস্ট্যাগমাস পাওয়া যায়নি",
    ru: "Значимого нистагма не выявлено", pt: "Nenhum nistagmo significativo detectado",
    ur: "کوئی اہم نسٹگمس نہیں ملا"
  },
  canalPosterior: {
    he: "חשד: תעלה אחורית",
    en: "Suspected: Posterior canal",
    zh: "疑似：后半规管",
    hi: "संदेह: पोस्टीरियर कैनाल",
    es: "Sospecha: Canal posterior",
    fr: "Suspicion : Canal postérieur",
    ar: "اشتباه: القناة الخلفية",
    bn: "সন্দেহ: পোস্টেরিয়র ক্যানাল",
    ru: "Подозрение: задний канал",
    pt: "Suspeita: Canal posterior",
    ur: "شبہ: پوسٹیریئر کینال"
  },
  canalHorizontal: {
    he: "חשד: תעלה אופקית",
    en: "Suspected: Horizontal canal",
    zh: "疑似：水平半规管",
    hi: "संदेह: होरिज़ोंटल कैनाल",
    es: "Sospecha: Canal horizontal",
    fr: "Suspicion : Canal horizontal",
    ar: "اشتباه: القناة الأفقية",
    bn: "সন্দেহ: হরাইজন্টাল ক্যানাল",
    ru: "Подозрение: горизонтальный канал",
    pt: "Suspeita: Canal horizontal",
    ur: "شبہ: ہوریزونٹل کینال"
  },
  canalAnterior: {
    he: "חשד: תעלה קדמית",
    en: "Suspected: Anterior canal",
    zh: "疑似：前半规管",
    hi: "संदेह: एंटीरियर कैनाल",
    es: "Sospecha: Canal anterior",
    fr: "Suspicion : Canal antérieur",
    ar: "اشتباه: القناة الأمامية",
    bn: "সন্দেহ: অ্যান্টেরিয়র ক্যানাল",
    ru: "Подозрение: передний канал",
    pt: "Suspeita: Canal anterior",
    ur: "شبہ: اینٹیریئر کینال"
  },
  showManeuver: {
    he: "הראה/י תמרון מתאים", en: "Show recommended maneuver", zh: "显示推荐的复位手法",
    hi: "अनुशंसित मैन्युवर दिखाएं", es: "Mostrar maniobra recomendada",
    fr: "Afficher la manœuvre recommandée", ar: "عرض المناورة الموصى بها",
    bn: "প্রস্তাবিত ম্যানুভার দেখান", ru: "Показать рекомендуемый манёвр",
    pt: "Mostrar manobra recomendada", ur: "تجویز کردہ طریقہ دکھائیں"
  },
  retry: {
    he: "בדיקה נוספת", en: "Retry test", zh: "重新测试", hi: "पुनः परीक्षण",
    es: "Repetir prueba", fr: "Réessayer le test", ar: "إعادة الاختبار",
    bn: "পুনরায় পরীক্ষা", ru: "Повторить тест", pt: "Repetir teste", ur: "دوبارہ ٹیسٹ"
  },
  confidence: {
    he: "רמת ודאות", en: "Confidence", zh: "置信度", hi: "विश्वास स्तर",
    es: "Confianza", fr: "Confiance", ar: "مستوى الثقة", bn: "আত্মবিশ্বাস",
    ru: "Уверенность", pt: "Confiança", ur: "اعتماد"
  },
  side: { he: "צד", en: "Side", zh: "侧", hi: "तरफ", es: "Lado", fr: "Côté",
    ar: "جانب", bn: "পাশ", ru: "Сторона", pt: "Lado", ur: "طرف" },
  right: { he: "ימין", en: "Right", zh: "右", hi: "दाएं", es: "Derecho", fr: "Droit",
    ar: "يمين", bn: "ডান", ru: "Правый", pt: "Direito", ur: "دائیں" },
  left: { he: "שמאל", en: "Left", zh: "左", hi: "बाएं", es: "Izquierdo", fr: "Gauche",
    ar: "يسار", bn: "বাম", ru: "Левый", pt: "Esquerdo", ur: "بائیں" },
  epley: {
    he: "תמרון Epley", en: "Epley Maneuver", zh: "Epley 复位手法", hi: "Epley मैन्युवर",
    es: "Maniobra de Epley", fr: "Manœuvre d'Epley", ar: "مناورة إبلي",
    bn: "Epley ম্যানুভার", ru: "Манёвр Эпли", pt: "Manobra de Epley", ur: "ایپلی طریقہ"
  },
  bbq: {
    he: "תמרון BBQ (Lempert)", en: "BBQ Roll (Lempert)", zh: "BBQ 翻滚手法",
    hi: "BBQ रोल मैन्युवर", es: "Maniobra BBQ Roll", fr: "Manœuvre BBQ Roll",
    ar: "مناورة BBQ Roll", bn: "BBQ রোল ম্যানুভার",
    ru: "Манёвр BBQ Roll", pt: "Manobra BBQ Roll", ur: "BBQ رول طریقہ"
  }
};

function t(key, lang) { return T[key] ? (T[key][lang] || T[key].en) : key; }
