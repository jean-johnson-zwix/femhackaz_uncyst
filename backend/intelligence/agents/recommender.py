import logging
from typing import Optional

from constants import CARE_PATHWAYS, SUBTYPE_LABELS
from models import Bloodwork
from intelligence.llm import call_llm
from intelligence.llm_config import RECOMMENDATION_INSIGHT
from intelligence.prompts import RECOMMENDATION_INSIGHT_SYSTEM, RECOMMENDATION_INSIGHT_USER

logger = logging.getLogger(__name__)

# Reference ranges used to flag outlier values for the LLM insight
_OUTLIER_RULES: list[tuple[str, str, float, str]] = [
    # (field, direction, threshold, description)
    ("testosterone",    "above", 70,   "testosterone {val:.1f} ng/dL (elevated)"),
    ("dheas",          "above", 200,  "DHEA-S {val:.0f} µg/dL (elevated)"),
    ("shbg",           "above", 80,   "SHBG {val:.0f} nmol/L (high)"),
    ("shbg",           "below", 40,   "SHBG {val:.0f} nmol/L (low)"),
    ("lh",             "above", 10,   "LH {val:.1f} IU/L (elevated)"),
    ("amh",            "above", 6,    "AMH {val:.1f} ng/mL (high)"),
    ("bmi",            "above", 30,   "BMI {val:.1f} (obese range)"),
    ("bmi",            "below", 23,   "BMI {val:.1f} (lean range)"),
    ("fasting_insulin","above", 15,   "fasting insulin {val:.1f} µIU/mL (elevated)"),
    ("fasting_glucose","above", 100,  "fasting glucose {val:.0f} mg/dL (elevated)"),
]


def _build_lab_summary(bloodwork: Optional[Bloodwork]) -> str:
    if bloodwork is None:
        return "No lab values provided."

    bw = bloodwork.model_dump()
    provided = {k: v for k, v in bw.items() if v is not None}
    if not provided:
        return "No lab values provided."

    outliers: list[str] = []
    normal: list[str] = []

    for field, direction, threshold, template in _OUTLIER_RULES:
        val = provided.get(field)
        if val is None:
            continue
        is_outlier = (direction == "above" and val > threshold) or (direction == "below" and val < threshold)
        if is_outlier:
            outliers.append("  * " + template.format(val=val))

    for field, val in provided.items():
        normal.append(f"  {field}: {val}")

    lines = ["All provided values:"] + normal
    if outliers:
        lines += ["", "Notable outliers:"] + outliers

    return "\n".join(lines)


def get_static_pathway(subtype: str) -> dict:
    if subtype not in CARE_PATHWAYS:
        raise ValueError(f"Unknown subtype: {subtype}")
    return CARE_PATHWAYS[subtype]


def get_personalized_insight(subtype: str, bloodwork: Optional[Bloodwork]) -> Optional[str]:
    label = SUBTYPE_LABELS.get(subtype, subtype)
    lab_summary = _build_lab_summary(bloodwork)

    system_prompt = RECOMMENDATION_INSIGHT_SYSTEM
    user_prompt = RECOMMENDATION_INSIGHT_USER.format(
        subtype=subtype,
        label=label,
        lab_summary=lab_summary,
    )

    try:
        insight = call_llm(
            task=RECOMMENDATION_INSIGHT,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
        return insight.strip()
    except Exception as exc:
        logger.warning("Personalized insight LLM call failed, returning None: %s", repr(exc))
        return None
