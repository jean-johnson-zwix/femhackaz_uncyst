import streamlit as st
import requests

API_CLASSIFY  = "http://localhost:8000/classify"
API_UPLOAD    = "http://localhost:8000/upload-report"
API_RECOMMEND = "http://localhost:8000/recommend"
API_ONBOARD   = "http://localhost:8000/onboard"
API_USER      = "http://localhost:8000/user"
API_USERS     = "http://localhost:8000/users"

GOAL_OPTIONS = {
    "lose_weight":      "Lose weight / reduce BMI",
    "manage_symptoms":  "Manage symptoms (acne, hair, fatigue)",
    "fertility":        "Improve fertility / track cycle",
    "understand_labs":  "Understand my lab results",
    "build_habits":     "Build consistent healthy habits",
}

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
st.title("UnCyst — PCOS Classifier")

# ═══════════════════════════════════════════════════════════════════════════════
# FLOW GATE — nothing below renders until the user is identified
# ═══════════════════════════════════════════════════════════════════════════════

def _reset_session():
    for key in ["flow", "user_id", "profile", "profile_saved"]:
        st.session_state.pop(key, None)


# Step 1 — choose flow
if "flow" not in st.session_state:
    st.subheader("Welcome! Are you a new or returning user?")
    col_new, col_ret = st.columns(2)
    with col_new:
        if st.button("I'm new here", use_container_width=True, type="primary"):
            import uuid
            st.session_state["flow"] = "new"
            st.session_state["user_id"] = str(uuid.uuid4())
            st.session_state["profile_saved"] = False
            st.rerun()
    with col_ret:
        if st.button("I have an account", use_container_width=True):
            st.session_state["flow"] = "returning"
            st.rerun()
    st.stop()


# Step 2a — returning user: pick from dropdown
if st.session_state["flow"] == "returning" and "profile" not in st.session_state:
    st.subheader("Welcome back!")

    all_users = []
    try:
        r = requests.get(API_USERS, timeout=10)
        r.raise_for_status()
        all_users = r.json().get("users", [])
    except requests.exceptions.ConnectionError:
        st.error("Cannot reach the backend.")
        if st.button("Back"):
            _reset_session()
            st.rerun()
        st.stop()
    except Exception as e:
        st.error(f"Failed to load users: {e}")

    if not all_users:
        st.info("No existing accounts found. Start as a new user instead.")
        if st.button("Back", use_container_width=True):
            _reset_session()
            st.rerun()
        st.stop()

    def _user_label(u: dict) -> str:
        name = u.get("name") or "Unnamed"
        short_id = u["user_id"][:8]
        date = u.get("onboarding_date", "")[:10]
        return f"{name}  ({short_id}…  joined {date})"

    options = [None] + all_users
    selected = st.selectbox(
        "Select your account",
        options=options,
        format_func=lambda u: "Select a user…" if u is None else _user_label(u),
    )

    col_load, col_back = st.columns([3, 1])
    with col_load:
        if st.button("Load my profile", use_container_width=True, type="primary"):
            if selected is None:
                st.error("Please select an account.")
            else:
                try:
                    r = requests.get(f"{API_USER}/{selected['user_id']}", timeout=10)
                    r.raise_for_status()
                    st.session_state["user_id"] = selected["user_id"]
                    st.session_state["profile"] = r.json().get("profile", {})
                    st.session_state["profile_saved"] = True
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to load profile: {e}")
    with col_back:
        if st.button("Back", use_container_width=True):
            _reset_session()
            st.rerun()
    st.stop()


# Step 2b — new user: show onboarding form
if st.session_state["flow"] == "new" and not st.session_state.get("profile_saved"):
    st.subheader("Tell us about yourself")
    st.caption(f"Your Session ID: `{st.session_state['user_id']}` — save this to return later.")

    p_name = st.text_input("Name (optional)", placeholder="e.g. Alex")
    p_age  = st.number_input("Age", min_value=10, max_value=80, value=None, placeholder="Enter your age")
    p_diagnosed = st.selectbox(
        "Have you been diagnosed with PCOS?",
        options=["", "yes", "no", "unsure"],
        format_func=lambda x: {"": "Select…", "yes": "Yes", "no": "No", "unsure": "Not sure"}[x],
    )
    p_goals = st.multiselect(
        "What are your goals?",
        options=list(GOAL_OPTIONS.keys()),
        format_func=lambda k: GOAL_OPTIONS[k],
    )
    col_a, col_b = st.columns(2)
    with col_a:
        p_cycle = st.number_input("Typical cycle length (days)", min_value=14, max_value=90, value=None, placeholder="e.g. 28")
    with col_b:
        p_ttc = st.checkbox("Trying to conceive")
    p_physician = st.checkbox("I am working with a physician or OB/GYN")

    col_save, col_skip = st.columns([3, 1])
    with col_save:
        if st.button("Save & Continue", use_container_width=True, type="primary"):
            onboard_payload = {
                "user_id":            st.session_state["user_id"],
                "name":               p_name or None,
                "age":                int(p_age) if p_age else None,
                "diagnosed_pcos":     p_diagnosed or None,
                "goals":              p_goals or None,
                "cycle_length_days":  int(p_cycle) if p_cycle else None,
                "trying_to_conceive": p_ttc,
                "physician_aware":    p_physician,
            }
            try:
                r = requests.post(API_ONBOARD, json=onboard_payload, timeout=10)
                r.raise_for_status()
                st.session_state["profile_saved"] = True
                st.session_state["profile"] = r.json().get("profile", {})
                st.rerun()
            except requests.exceptions.ConnectionError:
                st.error("Cannot reach the backend.")
            except Exception as e:
                st.error(f"Failed to save profile: {e}")
    with col_skip:
        if st.button("Skip", use_container_width=True):
            st.session_state["profile_saved"] = True
            st.session_state["profile"] = {}
            st.rerun()
    st.stop()


# ── Identified — show header bar ──────────────────────────────────────────────
user_id = st.session_state["user_id"]
prof    = st.session_state.get("profile", {})

name_part = f", {prof['name']}" if prof.get("name") else ""
st.subheader(f"Welcome{name_part}!")
st.caption(f"Session ID: `{user_id}` — save this to return later.")

if prof.get("goals"):
    goals_display = " · ".join(GOAL_OPTIONS.get(g, g) for g in prof["goals"])
    st.caption(f"Your goals: {goals_display}")

if st.button("Switch account", use_container_width=False):
    _reset_session()
    st.rerun()

st.divider()

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
    "Upload your blood report (PDF, JPEG, PNG, WEBP)",
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
        "user_id": user_id,
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

    if result.get("drift_detected"):
        st.warning("Your subtype has shifted from a previous classification. Consider retesting your labs to confirm.")

    st.subheader("Subtype Score Breakdown")
    st.bar_chart(scores)

    if missing:
        st.warning(
            "**Missing fields** — providing these would improve confidence:\n\n"
            + ", ".join(f"`{f}`" for f in missing)
        )

    with st.expander("Raw classification response"):
        st.json(result)

    # ── Recommendations ───────────────────────────────────────────────────────
    st.divider()
    st.subheader("Your Personalised Care Plan")

    rec_payload = {
        "subtype": subtype,
        "bloodwork": payload["bloodwork"],
    }

    rec_result = None
    with st.spinner("Building your care plan…"):
        try:
            rec_resp = requests.post(API_RECOMMEND, json=rec_payload, timeout=30)
            rec_resp.raise_for_status()
            rec_result = rec_resp.json()
        except requests.exceptions.ConnectionError:
            st.error("Cannot reach the backend for recommendations.")
        except Exception as e:
            st.error(f"Recommendation request failed: {e}")

    if rec_result:
        insight = rec_result.get("personalized_insight")
        if insight:
            st.info(f"**Your numbers say:** {insight}")

        pathway = rec_result.get("care_pathway", {})
        tab_diet, tab_exercise, tab_supplements, tab_referrals = st.tabs([
            "Diet", "Exercise", "Supplements", "Referrals"
        ])

        with tab_diet:
            for item in pathway.get("diet", []):
                st.markdown(f"- {item}")

        with tab_exercise:
            for item in pathway.get("exercise", []):
                st.markdown(f"- {item}")

        with tab_supplements:
            st.caption("Always consult your physician before starting supplements.")
            for item in pathway.get("supplements", []):
                st.markdown(f"- {item}")

        with tab_referrals:
            for item in pathway.get("referral_flags", []):
                st.markdown(f"- {item}")

        with st.expander("Raw recommendation response"):
            st.json(rec_result)

st.divider()
