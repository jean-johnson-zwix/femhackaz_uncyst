import json
import logging
from typing import Optional

from .llm import call_llm, call_llm_vision
from .llm_config import BLOOD_REPORT_TEXT_EXTRACTION
from .prompts import (
    BLOOD_REPORT_SYSTEM,
    BLOOD_REPORT_USER_TEXT,
    BLOOD_REPORT_USER_IMAGE,
)

logger = logging.getLogger(__name__)

BLOODWORK_FIELDS = [
    "lh", "fsh", "testosterone", "shbg", "dheas",
    "amh", "bmi", "fasting_insulin", "fasting_glucose",
]


def _parse_bloodwork_json(raw: str) -> dict:
    """Parse LLM response to a clean bloodwork dict with only known fields."""
    raw = raw.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        lines = raw.splitlines()
        raw = "\n".join(
            line for line in lines
            if not line.strip().startswith("```")
        )
    data = json.loads(raw)
    result = {}
    for field in BLOODWORK_FIELDS:
        val = data.get(field)
        if val is not None:
            try:
                result[field] = float(val)
            except (TypeError, ValueError):
                result[field] = None
        else:
            result[field] = None
    return result


def extract_from_image(image_bytes: bytes, mime_type: str) -> dict:
    raw = call_llm_vision(
        image_bytes=image_bytes,
        image_mime_type=mime_type,
        system_prompt=BLOOD_REPORT_SYSTEM,
        user_prompt=BLOOD_REPORT_USER_IMAGE,
        task=BLOOD_REPORT_TEXT_EXTRACTION,
    )
    return _parse_bloodwork_json(raw)


def extract_from_pdf(pdf_bytes: bytes) -> dict:
    try:
        import pdfplumber
        import io
        text_parts = []
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        report_text = "\n\n".join(text_parts).strip()
    except ImportError:
        raise RuntimeError("pdfplumber is missing")

    if not report_text:
        raise ValueError("Could not extract any text from the PDF.")

    raw = call_llm(
        task=BLOOD_REPORT_TEXT_EXTRACTION,
        system_prompt=BLOOD_REPORT_SYSTEM,
        user_prompt=BLOOD_REPORT_USER_TEXT.format(report_text=report_text),
    )
    return _parse_bloodwork_json(raw)


def extract_bloodwork(file_bytes: bytes, content_type: str) -> dict:
    ct = content_type.lower()
    if ct == "application/pdf":
        return extract_from_pdf(file_bytes)
    if ct in ("image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"):
        return extract_from_image(file_bytes, ct)
    raise ValueError(f"Unsupported file type: {content_type}. Upload a PDF or image (JPEG, PNG, WEBP).")
