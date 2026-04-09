SUBTYPE_LABELS = {
    "HA": "Hyperandrogenic PCOS",
    "OB": "Metabolic / Obesity-driven PCOS",
    "SHBG": "Lean / High-SHBG PCOS",
    "LH": "High LH / High AMH PCOS",
}

CARE_PATHWAYS = {
    "HA": {
        "diet": [
            "Follow a low-glycemic index diet to reduce insulin-driven androgen production",
            "Increase spearmint tea intake (2 cups/day) — shown to reduce free testosterone",
            "Prioritize anti-inflammatory foods: fatty fish, leafy greens, berries, walnuts",
            "Limit dairy and processed sugar, which may elevate IGF-1 and worsen acne",
        ],
        "exercise": [
            "Resistance training 3x/week to improve insulin sensitivity and reduce androgens",
            "Moderate-intensity cardio (e.g., brisk walking, cycling) 150 min/week",
            "Avoid excessive HIIT — can temporarily spike cortisol and worsen androgen symptoms",
            "Yoga or Pilates for stress reduction and cortisol management",
        ],
        "supplements": [
            "Inositol (Myo-inositol 2g + D-chiro-inositol 50mg daily) — reduces testosterone",
            "Zinc 25–30 mg/day — supports androgen clearance and reduces acne",
            "Saw palmetto — may reduce DHT conversion (consult physician first)",
            "Vitamin D3 if deficient — supports hormonal balance",
        ],
        "referral_flags": [
            "Dermatology referral if acne is moderate-to-severe or unresponsive to lifestyle",
            "Endocrinology if testosterone or DHEAS is significantly elevated",
            "Consider anti-androgen medications (spironolactone) — discuss with OB/GYN",
        ],
    },
    "OB": {
        "diet": [
            "Target a modest caloric deficit (250–500 kcal/day) to reduce metabolic burden",
            "Low-GI, high-fiber diet to stabilize blood glucose and reduce fasting insulin",
            "Increase protein intake (25–30% of calories) to support satiety and muscle retention",
            "Limit refined carbohydrates, sugary drinks, and ultra-processed foods",
            "Consider time-restricted eating (16:8) — may improve insulin sensitivity",
        ],
        "exercise": [
            "Resistance training 3–4x/week — most effective single intervention for insulin resistance",
            "150–300 min/week moderate cardio (walking, swimming, cycling)",
            "Break up sedentary time every 30 minutes — even short walks after meals reduce glucose spikes",
            "Start with low-impact exercise if joint stress is a concern",
        ],
        "supplements": [
            "Myo-inositol 2–4g/day — directly addresses insulin resistance in PCOS",
            "Berberine 500mg 2–3x/day (comparable to metformin for glucose — consult physician)",
            "Magnesium glycinate 300mg — supports insulin signaling",
            "Omega-3 fatty acids 2–3g/day — reduces inflammation and triglycerides",
        ],
        "referral_flags": [
            "Discuss metformin candidacy with OB/GYN or endocrinologist if fasting insulin > 15",
            "Registered dietitian referral for personalized caloric and macronutrient planning",
            "Consider HbA1c and fasting glucose monitoring every 6 months",
            "Bariatric evaluation if BMI > 40 with comorbidities",
        ],
    },
    "SHBG": {
        "diet": [
            "Nutrient-dense, balanced diet — avoid severe caloric restriction which depresses SHBG further",
            "Emphasize healthy fats (avocado, olive oil, nuts) to support hormone production",
            "Adequate protein for lean muscle maintenance — 1.2–1.6g/kg body weight",
            "Limit alcohol — strongly suppresses SHBG production in the liver",
            "Cruciferous vegetables (broccoli, cauliflower) support estrogen detox pathways",
        ],
        "exercise": [
            "Cortisol-aware training: moderate intensity, avoid overtraining",
            "Strength training 2–3x/week to support lean mass and SHBG-testosterone balance",
            "Prioritize recovery — adequate sleep is critical for SHBG regulation",
            "Walking, swimming, or yoga preferred over high-intensity daily sessions",
        ],
        "supplements": [
            "Magnesium glycinate 300mg/day — supports cortisol regulation and sleep quality",
            "Ashwagandha (KSM-66) — adaptogen that reduces cortisol and may improve hormonal balance",
            "Vitamin D3 + K2 if deficient — supports SHBG production in the liver",
            "B-complex vitamins — support liver function and hormonal metabolism",
        ],
        "referral_flags": [
            "Rule out thyroid dysfunction (hypothyroidism can suppress SHBG) — request TSH panel",
            "Check liver function — SHBG is produced in the liver; hepatic issues affect levels",
            "Review any medications that suppress SHBG (androgens, glucocorticoids, progestins)",
        ],
    },
    "LH": {
        "diet": [
            "Anti-inflammatory diet to reduce LH pulsatility — Mediterranean-style eating",
            "Maintain stable blood sugar to avoid insulin spikes that amplify LH surges",
            "Flaxseeds and phytoestrogen-rich foods may gently modulate LH/FSH balance",
            "Limit caffeine — high intake can worsen LH pulsatility and disrupt cycle regularity",
        ],
        "exercise": [
            "Moderate, consistent exercise — extreme exercise can further disrupt LH pulsatility",
            "Yoga and mind-body practices shown to reduce LH levels in PCOS studies",
            "Cycle-syncing exercise: higher intensity in follicular phase, gentler in luteal phase",
            "Avoid sudden dramatic changes in training volume",
        ],
        "supplements": [
            "Myo-inositol 4g/day — reduces LH/FSH ratio and improves ovarian function",
            "Melatonin 3mg at bedtime — shown to reduce LH and improve oocyte quality",
            "CoQ10 200–600mg/day — supports ovarian reserve and AMH-related egg quality",
            "Vitex (Chaste Tree Berry) — may normalize LH/FSH ratio (discuss with physician)",
        ],
        "referral_flags": [
            "Reproductive endocrinology referral if trying to conceive — LH subtype responds well to ovulation induction",
            "AMH monitoring every 6–12 months to track ovarian reserve trajectory",
            "Fertility awareness education — track LH surges with OPKs to identify ovulation windows",
            "Discuss cycle regulation options with OB/GYN (progesterone support, clomiphene)",
        ],
    },
}