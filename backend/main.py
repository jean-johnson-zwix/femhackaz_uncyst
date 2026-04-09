from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import ClassifyRequest, RecommendRequest, RecommendResponse
from constants import SUBTYPE_LABELS
from typing import Optional
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="PCOS Classifier")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/classify")
def classify(req: ClassifyRequest):
    s = req.symptoms
    b = req.bloodwork

    scores = {"HA": 0, "OB": 0, "SHBG": 0, "LH": 0}
    missing_fields: list[str] = []

    clinical_androgens = sum([s.facial_hair, s.acne, s.scalp_thinning])

    lh_fsh_ratio: Optional[float] = None
    if b.lh is not None and b.fsh is not None and b.fsh != 0:
        lh_fsh_ratio = b.lh / b.fsh

    # --- HA (Hyperandrogenic) ---
    if b.testosterone is not None:
        if b.testosterone > 70:
            scores["HA"] += 2
    else:
        missing_fields.append("testosterone")

    if b.dheas is not None:
        if b.dheas > 200:
            scores["HA"] += 2
    else:
        missing_fields.append("dheas")

    if clinical_androgens >= 2:
        scores["HA"] += 2

    if lh_fsh_ratio is not None:
        if 1.5 <= lh_fsh_ratio <= 2.5:
            scores["HA"] += 1
    else:
        if b.lh is None:
            missing_fields.append("lh")
        if b.fsh is None:
            missing_fields.append("fsh")

    # --- OB (Obesity/Metabolic) ---
    if b.bmi is not None:
        if b.bmi >= 30:
            scores["OB"] += 3
    else:
        missing_fields.append("bmi")

    if b.fasting_insulin is not None:
        if b.fasting_insulin > 15:
            scores["OB"] += 2
    else:
        missing_fields.append("fasting_insulin")

    if b.fasting_glucose is not None:
        if b.fasting_glucose > 100:
            scores["OB"] += 2
    else:
        missing_fields.append("fasting_glucose")

    if b.shbg is not None:
        if b.shbg < 40:
            scores["OB"] += 1
    else:
        missing_fields.append("shbg")

    # --- SHBG (High SHBG / Lean) ---
    if b.shbg is not None:
        if b.shbg > 80:
            scores["SHBG"] += 3
        if b.shbg < 40:
            pass  # already counted for OB, not SHBG

    if b.bmi is not None:
        if b.bmi < 23:
            scores["SHBG"] += 2

    if clinical_androgens <= 1:
        scores["SHBG"] += 1

    # --- LH (High LH / High AMH) ---
    if b.lh is not None:
        if b.lh > 10:
            scores["LH"] += 2

    if lh_fsh_ratio is not None:
        if lh_fsh_ratio > 2.0:
            scores["LH"] += 2

    if b.amh is not None:
        if b.amh > 6:
            scores["LH"] += 2
    else:
        missing_fields.append("amh")

    # Deduplicate missing_fields while preserving order
    seen = set()
    unique_missing: list[str] = []
    for f in missing_fields:
        if f not in seen:
            seen.add(f)
            unique_missing.append(f)

    sorted_subtypes = sorted(scores, key=lambda k: scores[k], reverse=True)
    top_subtype = sorted_subtypes[0]
    top_score = scores[top_subtype]
    second_score = scores[sorted_subtypes[1]]
    gap = top_score - second_score

    if top_score >= 5 and gap >= 2:
        confidence = "high"
    elif top_score >= 3:
        confidence = "moderate"
    else:
        confidence = "low"

    return {
        "subtype": top_subtype,
        "label": SUBTYPE_LABELS[top_subtype],
        "confidence": confidence,
        "scores": scores,
        "missing_fields": unique_missing,
    }


ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@app.post("/upload-report")
async def upload_report(file: UploadFile = File(...)):
    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{content_type}'. Upload a PDF or image (JPEG, PNG, WEBP).",
        )

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10 MB.")

    try:
        from intelligence.agents.extractor import extract_bloodwork
        bloodwork = extract_bloodwork(file_bytes, content_type)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    found = {k: v for k, v in bloodwork.items() if v is not None}
    missing = [k for k, v in bloodwork.items() if v is None]

    return {
        "bloodwork": bloodwork,
        "fields_found": list(found.keys()),
        "fields_missing": missing,
    }


@app.post("/recommend", response_model=RecommendResponse)
def recommend(req: RecommendRequest):
    if req.subtype not in SUBTYPE_LABELS:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown subtype '{req.subtype}'. Must be one of: HA, OB, SHBG, LH.",
        )

    from intelligence.agents.recommender import get_static_pathway, get_personalized_insight

    care_pathway = get_static_pathway(req.subtype)
    personalized_insight = get_personalized_insight(req.subtype, req.bloodwork)

    return RecommendResponse(
        subtype=req.subtype,
        label=SUBTYPE_LABELS[req.subtype],
        care_pathway=care_pathway,
        personalized_insight=personalized_insight,
    )


@app.get("/health")
def health():
    return {"status": "ok"}
