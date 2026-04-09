from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# Classification Logic

class Symptoms(BaseModel):
    irregular_cycles: bool = False
    facial_hair: bool = False
    acne: bool = False
    scalp_thinning: bool = False
    weight_gain: bool = False
    fatigue: bool = False


class Bloodwork(BaseModel):
    lh: Optional[float] = None
    fsh: Optional[float] = None
    testosterone: Optional[float] = None
    shbg: Optional[float] = None
    dheas: Optional[float] = None
    amh: Optional[float] = None
    bmi: Optional[float] = None
    fasting_insulin: Optional[float] = None
    fasting_glucose: Optional[float] = None


class ClassifyRequest(BaseModel):
    symptoms: Symptoms
    bloodwork: Bloodwork
    user_id: Optional[str] = None


# Onboarding

DIAGNOSED_PCOS_VALUES = {"yes", "no", "unsure"}
VALID_GOALS = {
    "lose_weight",
    "manage_symptoms",
    "fertility",
    "understand_labs",
    "build_habits",
}

class OnboardingRequest(BaseModel):
    user_id: str
    name: Optional[str] = None
    age: Optional[int] = None
    diagnosed_pcos: Optional[str] = None   # 'yes' | 'no' | 'unsure'
    goals: Optional[List[str]] = None      # subset of VALID_GOALS
    cycle_length_days: Optional[int] = None
    trying_to_conceive: Optional[bool] = None
    physician_aware: Optional[bool] = None


class OnboardingResponse(BaseModel):
    user_id: str
    profile: Dict[str, Any]


# Recommendation Engine

class RecommendRequest(BaseModel):
    subtype: str  # "HA" | "OB" | "SHBG" | "LH"
    bloodwork: Optional[Bloodwork] = None
    coaching_context: Optional[Dict[str, Any]] = None


class RecommendResponse(BaseModel):
    subtype: str
    label: str
    care_pathway: Dict[str, List[str]]  # diet, exercise, supplements, referral_flags
    personalized_insight: Optional[str] = None  # LLM callout; None if unavailable
