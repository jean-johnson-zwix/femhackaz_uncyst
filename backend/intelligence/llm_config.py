from typing import Dict, Any

# LLM Task Directory
BLOOD_REPORT_TEXT_EXTRACTION = "blood_report_text_extraction"


# Timeouts for different providers in seconds
PROVIDER_TIMEOUTS = {
    "gemini":     45,
    "groq":       30,
    "sambanova":  60,
    "openrouter": 90,
}

LLM_TASK_CONFIGS: Dict[str, Dict[str, Any]] = {
    BLOOD_REPORT_TEXT_EXTRACTION: {
        "description": "Extract structured bloodwork fields from blood report text (PDF)",
        "provider": "gemini",
        "model": "gemini-2.5-flash",
        "fallbacks": [("groq", "llama-3.3-70b-versatile")],
        "vision_fallbacks": [("openrouter", "google/gemini-2.0-flash-001")],
        "max_tokens": 1024,
        "temperature": 0.0,
        "response_format": "json",
    },
}

def get_llm_task_config(task_name: str) -> Dict[str, Any]:
    try:
        return LLM_TASK_CONFIGS[task_name]
    except KeyError as e:
        raise ValueError(f"Unknown LLM task config: {task_name}") from e