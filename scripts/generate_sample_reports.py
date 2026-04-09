from PIL import Image, ImageDraw, ImageFont
import os

W, H = 900, 1100
BG       = (255, 255, 255)
HEADER   = (40,  80,  140)
ROW_ALT  = (240, 245, 252)
ROW_NORM = (255, 255, 255)
FLAG     = (180, 30,  30)
NORMAL   = (30,  120, 50)
BORDER   = (180, 190, 210)
TEXT     = (30,  30,  30)
SUBTEXT  = (100, 100, 100)

def load_font(size, bold=False):
    candidates = [
        "C:/Windows/Fonts/Arial.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()

def draw_report(filename, patient, dob, date, rows):
    img  = Image.new("RGB", (W, H), BG)
    d    = ImageDraw.Draw(img)

    font_lg   = load_font(22, bold=True)
    font_md   = load_font(16, bold=True)
    font_sm   = load_font(14)
    font_xsm  = load_font(12)
    font_bold = load_font(14, bold=True)

    # ── Header bar ─────────────────────────────────────────────────
    d.rectangle([(0, 0), (W, 70)], fill=HEADER)
    d.text((30, 15), "AZ Women's Health Laboratory", font=font_lg, fill=(255, 255, 255))
    d.text((30, 45), "Comprehensive Hormonal Panel", font=font_xsm, fill=(200, 215, 240))

    # ── Patient info ───────────────────────────────────────────────
    y = 90
    d.text((30, y),       f"Patient:       {patient}",   font=font_sm, fill=TEXT)
    d.text((30, y + 22),  f"Date of Birth: {dob}",        font=font_sm, fill=TEXT)
    d.text((30, y + 44),  f"Collected:     {date}",       font=font_sm, fill=TEXT)
    d.text((500, y),      "Specimen:  Serum / Plasma",    font=font_sm, fill=SUBTEXT)
    d.text((500, y + 22), "Accession: AZ-2026-04-09",     font=font_sm, fill=SUBTEXT)
    d.text((500, y + 44), "Ordering Physician: Dr. R. Patel MD", font=font_sm, fill=SUBTEXT)

    d.line([(30, y + 70), (W - 30, y + 70)], fill=BORDER, width=1)

    # ── Table header ───────────────────────────────────────────────
    ty = y + 82
    d.rectangle([(30, ty), (W - 30, ty + 28)], fill=HEADER)
    cols = [30, 280, 430, 570, 710]
    headers = ["Test Name", "Result", "Units", "Reference Range", "Flag"]
    for i, h in enumerate(headers):
        d.text((cols[i] + 6, ty + 6), h, font=font_bold, fill=(255, 255, 255))

    # ── Table rows ─────────────────────────────────────────────────
    ry = ty + 30
    for idx, (name, result, units, ref, flag) in enumerate(rows):
        row_bg = ROW_ALT if idx % 2 == 0 else ROW_NORM
        d.rectangle([(30, ry), (W - 30, ry + 26)], fill=row_bg)
        d.line([(30, ry + 26), (W - 30, ry + 26)], fill=BORDER, width=1)

        flag_color = FLAG if flag == "H" else (NORMAL if flag == "N" else SUBTEXT)
        d.text((cols[0] + 6, ry + 5), name,   font=font_sm, fill=TEXT)
        d.text((cols[1] + 6, ry + 5), result, font=font_bold if flag == "H" else font_sm, fill=FLAG if flag == "H" else TEXT)
        d.text((cols[2] + 6, ry + 5), units,  font=font_xsm, fill=SUBTEXT)
        d.text((cols[3] + 6, ry + 5), ref,    font=font_xsm, fill=SUBTEXT)
        d.text((cols[4] + 6, ry + 5), flag,   font=font_bold, fill=flag_color)
        ry += 28

    # ── Footer ─────────────────────────────────────────────────────
    d.line([(30, H - 60), (W - 30, H - 60)], fill=BORDER, width=1)
    d.text((30, H - 50), "Results are for clinical use only. Consult your physician.", font=font_xsm, fill=SUBTEXT)
    d.text((30, H - 32), "AZ Women's Health Lab · 4800 N Central Ave, Phoenix AZ 85012 · (602) 555-0198", font=font_xsm, fill=SUBTEXT)

    img.save(filename)
    print(f"Saved: {filename}")


# ── Report 1: Hyperandrogenic (HA) ────────────────────────────────────────────
# Expected score: HA=5+ (testosterone>70 +2, DHEAS>200 +2, LH/FSH in 1.5-2.5 +1)
draw_report(
    filename="sample_report_HA.png",
    patient="Sofia Reyes",
    dob="1996-03-14",
    date="2026-04-08",
    rows=[
        # name                    result   units       reference range      flag
        ("LH (Luteinizing Hormone)", "9.2", "IU/L",    "2.0 – 15.0",        "N"),
        ("FSH (Follicle Stimulating)", "5.1", "IU/L",  "3.0 – 10.0",        "N"),
        ("LH/FSH Ratio",             "1.80", "",       "< 1.5 (typical)",   "H"),
        ("Total Testosterone",       "88.4", "ng/dL",  "15 – 70",           "H"),
        ("Free Testosterone",        "3.1",  "pg/mL",  "0.3 – 1.9",         "H"),
        ("DHEA-Sulfate (DHEAS)",     "312.0","µg/dL",  "35 – 200",          "H"),
        ("SHBG",                     "48.0", "nmol/L", "18 – 114",          "N"),
        ("AMH (Anti-Müllerian)",     "5.2",  "ng/mL",  "1.0 – 3.5",         "H"),
        ("Estradiol",                "62.0", "pg/mL",  "12 – 166",          "N"),
        ("Progesterone",             "0.6",  "ng/mL",  "0.1 – 0.8 (follic)","N"),
        ("Fasting Glucose",          "88.0", "mg/dL",  "70 – 99",           "N"),
        ("Fasting Insulin",          "9.0",  "µIU/mL", "2.0 – 15.0",        "N"),
        ("BMI (recorded)",           "23.4", "kg/m²",  "18.5 – 24.9",       "N"),
        ("TSH",                      "2.1",  "µIU/mL", "0.4 – 4.0",         "N"),
    ]
)

# ── Report 2: Metabolic / Obesity-driven (OB) ────────────────────────────────
# Expected score: OB=8 (BMI≥30 +3, fasting_insulin>15 +2, fasting_glucose>100 +2, SHBG<40 +1)
draw_report(
    filename="sample_report_OB.png",
    patient="Maya Torres",
    dob="1993-07-22",
    date="2026-04-08",
    rows=[
        # name                    result   units       reference range      flag
        ("LH (Luteinizing Hormone)", "7.4",  "IU/L",  "2.0 – 15.0",        "N"),
        ("FSH (Follicle Stimulating)","5.8",  "IU/L",  "3.0 – 10.0",        "N"),
        ("LH/FSH Ratio",             "1.28", "",       "< 1.5 (typical)",   "N"),
        ("Total Testosterone",       "52.0", "ng/dL",  "15 – 70",           "N"),
        ("Free Testosterone",        "1.4",  "pg/mL",  "0.3 – 1.9",         "N"),
        ("DHEA-Sulfate (DHEAS)",     "145.0","µg/dL",  "35 – 200",          "N"),
        ("SHBG",                     "28.0", "nmol/L", "18 – 114",          "H"),
        ("AMH (Anti-Müllerian)",     "4.1",  "ng/mL",  "1.0 – 3.5",         "H"),
        ("Estradiol",                "55.0", "pg/mL",  "12 – 166",          "N"),
        ("Progesterone",             "0.5",  "ng/mL",  "0.1 – 0.8 (follic)","N"),
        ("Fasting Glucose",          "118.0","mg/dL",  "70 – 99",           "H"),
        ("Fasting Insulin",          "24.5", "µIU/mL", "2.0 – 15.0",        "H"),
        ("BMI (recorded)",           "33.5", "kg/m²",  "18.5 – 24.9",       "H"),
        ("TSH",                      "2.8",  "µIU/mL", "0.4 – 4.0",         "N"),
    ]
)
