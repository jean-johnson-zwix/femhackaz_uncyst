from pydantic import BaseModel
from typing import Optional

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
