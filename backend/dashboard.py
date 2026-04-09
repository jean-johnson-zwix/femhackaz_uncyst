import streamlit as st
import requests

API_CLASSIFY  = "http://localhost:8000/classify"
API_UPLOAD    = "http://localhost:8000/upload-report"

BLOODWORK_LABELS = {
    "lh":              "LH (IU/L)",
    "fsh":             "FSH (IU/L)",
    "testosterone":    "Testosterone (ng/dL)",
    "shbg":            "SHBG (nmol/L)",
    "dheas":           "DHEAS (µg/dL)",
    "amh":             "AMH (ng/mL)",
    "bmi":             "BMI",
    "fasting_insulin": "Fasting Insulin (µIU/mL)",
    "fasting_glucose": "Fasting Glucose (mg/dL)",
}

CONFIDENCE_COLOR = {"high": "🟢", "moderate": "🟡", "low": "🔴"}
SUBTYPE_INFO = {
    "HA":   ("Hyperandrogenic PCOS",           "Driven by excess androgens. Focus: anti-androgen strategies, spearmint tea, low-GI diet."),
    "OB":   ("Metabolic / Obesity-driven PCOS", "Driven by insulin resistance. Focus: low-GI diet, resistance training, inositol supplementation."),
    "SHBG": ("Lean / High-SHBG PCOS",           "Low androgen activity despite PCOS markers. Focus: stress reduction, adequate caloric intake, sleep."),
    "LH":   ("High LH / High AMH PCOS",         "Driven by LH excess and follicle accumulation. Focus: stress management, cycle tracking, low-intensity exercise."),
}

st.set_page_config(page_title="UnCyst — PCOS Classifier", page_icon="🩺", layout="centered")
st.title("Client Onboarding")

# ── Symptoms ──────────────────────────────────────────────────────────────────
st.header("Symptoms")
col1, col2 = st.columns(2)
with col1:
    irregular_cycles = st.checkbox("Irregular or absent periods")
    facial_hair      = st.checkbox("Excess facial / body hair")
    acne             = st.checkbox("Acne")
with col2:
    scalp_thinning   = st.checkbox("Scalp hair thinning")
    weight_gain      = st.checkbox("Unexplained weight gain")
    fatigue          = st.checkbox("Chronic fatigue")

# ── Bloodwork ─────────────────────────────────────────────────────────────────
st.header("Bloodwork")

# Initialise session state for extracted bloodwork values
for field in BLOODWORK_LABELS:
    if f"bw_{field}" not in st.session_state:
        st.session_state[f"bw_{field}"] = ""

# Upload section
uploaded_file = st.file_uploader(
    "Upload your blood report (PDF, JPEG, PNG, WEBP) — values will be auto-filled",
    type=["pdf", "jpg", "jpeg", "png", "webp"],
)

if uploaded_file is not None:
    if st.button("Extract from report", use_container_width=True):
        with st.spinner("Extracting bloodwork values…"):
            try:
                resp = requests.post(
                    API_UPLOAD,
                    files={"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)},
                    timeout=60,
                )
                resp.raise_for_status()
                data = resp.json()
                bloodwork = data.get("bloodwork", {})
                found     = data.get("fields_found", [])

                for field, val in bloodwork.items():
                    if val is not None:
                        st.session_state[f"bw_{field}"] = str(val)

                if found:
                    st.success(f"Extracted {len(found)} field(s): {', '.join(f'`{f}`' for f in found)} - {bloodwork}")
                    print(f"Extracted bloodwork: {found}")
                else:
                    st.warning("No bloodwork values could be extracted from the report.")

            except requests.exceptions.ConnectionError:
                st.error("Cannot reach the backend. Make sure `uvicorn main:app --reload` is running in the `backend/` folder.")
            except Exception as e:
                st.error(f"Extraction failed: {e}")

def parse_float(val: str):
    val = val.strip()
    try:
        return float(val) if val else None
    except ValueError:
        return None


# ── Classify ──────────────────────────────────────────────────────────────────
if st.button("Classify", type="primary", use_container_width=True):
    payload = {
        "symptoms": {
            "irregular_cycles": irregular_cycles,
            "facial_hair":      facial_hair,
            "acne":             acne,
            "scalp_thinning":   scalp_thinning,
            "weight_gain":      weight_gain,
            "fatigue":          fatigue,
        },
        "bloodwork": {
            field: parse_float(st.session_state[f"bw_{field}"])
            for field in BLOODWORK_LABELS
        },
    }

    try:
        resp = requests.post(API_CLASSIFY, json=payload, timeout=10)
        resp.raise_for_status()
        result = resp.json()
    except requests.exceptions.ConnectionError:
        st.error("Cannot reach the backend. Make sure `uvicorn main:app --reload` is running in the `backend/` folder.")
        st.stop()
    except Exception as e:
        st.error(f"Request failed: {e}")
        st.stop()

    st.divider()
    st.subheader("Classification Result")

    subtype     = result["subtype"]
    label, tip  = SUBTYPE_INFO[subtype]
    conf        = result["confidence"]
    scores      = result["scores"]
    missing     = result["missing_fields"]

    st.markdown(f"### {label}")
    st.markdown(f"**Confidence:** {CONFIDENCE_COLOR[conf]} {conf.capitalize()}")
    st.info(f"**Guidance:** {tip}")

    st.subheader("Subtype Score Breakdown")
    st.bar_chart(scores)

    if missing:
        st.warning(
            "**Missing fields** — providing these would improve confidence:\n\n"
            + ", ".join(f"`{f}`" for f in missing)
        )

    with st.expander("Raw API response"):
        st.json(result)

st.divider()
