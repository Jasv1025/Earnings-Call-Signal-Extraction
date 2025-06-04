import os
import re
import json
from pathlib import Path

CACHE_DIR = "cache_mistral"

def _cache_path(prompt: str, company: str, quarter: str, section_index: int = None, is_summary: int = 0, custom_suffix: str = None) -> Path:
    sanitized_company = re.sub(r'\W+', '', company.lower())
    sanitized_quarter = re.sub(r'\W+', '', quarter.upper())

    if custom_suffix:
        filename = f"{sanitized_company}_{sanitized_quarter}_{custom_suffix}.json"
    elif is_summary == 1:
        filename = f"{sanitized_company}_{sanitized_quarter}_summary.json"
    elif is_summary == 2:
        filename = f"{sanitized_company}_{sanitized_quarter}_tone.json"
    else:
        filename = f"{sanitized_company}_{sanitized_quarter}_{section_index}.json"

    return Path(CACHE_DIR) / filename

def analyze_labeled_sections(prepared: str, qa: str, company: str = "NVIDIA", quarter: str = "QX", provider: str = "ollama") -> dict:
    final_analysis = {
        "company": company,
        "provider": provider,
        "model": "cache_only",
        "signal": "labeled_analysis",
        "result": {}
    }

    labels = [
        ("management_sentiment", "management_sentiment_summary"),
        ("qa_sentiment", "qa_sentiment_summary"),
        ("strategic_focuses", "strategic_summary"),
        ("summary", "summary")
    ]

    for key, suffix in labels:
        path = _cache_path("", company, quarter, custom_suffix=suffix, is_summary=1)
        if not path.exists():
            raise RuntimeError(f"Missing cache file: {path.name}")
        with open(path, "r", encoding="utf-8") as f:
            final_analysis["result"][key] = json.load(f)["content"]

    return final_analysis

def compare_tone(summary1: str, summary2: str, company: str = "NVIDIA", quarter1: str = "Q1", quarter2: str = "Q2") -> str:
    """Return raw tone comparison result from cache (no JSON parsing)."""
    cache_id = f"{quarter1}_vs_{quarter2}"
    path = _cache_path("", company, cache_id, is_summary=2)
    if not path.exists():
        raise RuntimeError(f"Missing cache file: {path.name}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f).get('content', '').strip()