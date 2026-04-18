from __future__ import annotations

import json

import requests
from fastapi import HTTPException

from app.core.config import GEMINI_API_KEY


GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"


def _fallback_explanation(payload: dict) -> dict:
    group = payload["group"]
    sample_size = payload.get("count")
    approval_rate = float(payload.get("approval_rate", 0.0))
    baseline_rate = float(payload.get("baseline_rate", 0.0))
    difference = payload["difference"]
    severity = payload["severity"]
    ranking_reason = str(payload.get("ranking_reason") or "").strip()

    sample_text = f" with sample size {sample_size}" if sample_size is not None else ""
    ranking_text = f" {ranking_reason}" if ranking_reason else ""
    explanation = (
        f"Group '{group}'{sample_text} has approval rate {approval_rate:.2f} versus baseline {baseline_rate:.2f}, "
        f"yielding a gap of {difference:.2f}. This is classified as {severity} severity and suggests potential bias risk."
        f"{ranking_text}"
    )
    return {
        "explanation": explanation,
        "recommendations": [
            "Collect balanced training examples for underrepresented groups.",
            "Review feature engineering and remove variables acting as proxy signals.",
            "Add fairness checks to model validation before deployment.",
        ],
    }


def generate_explanation(payload: dict) -> dict:
    if not GEMINI_API_KEY:
        return _fallback_explanation(payload)

    prompt = (
        "You are a fairness auditor writing concise executive-ready analysis. "
        "Given a single flagged group, use the group name, sample size, approval rate, baseline rate, "
        "gap, severity, and ranking reason to explain risk clearly in 2-3 sentences. "
        "Then provide 3 short actionable recommendations. "
        "Return strict JSON only with keys: explanation (string), recommendations (array of 3 strings). "
        "No markdown and no extra keys. Data: "
        f"{json.dumps(payload)}"
    )

    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2},
    }

    try:
        response = requests.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            json=body,
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
        text = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )
        parsed = json.loads(text)
        if not isinstance(parsed.get("recommendations"), list):
            raise ValueError("Invalid Gemini response shape.")
        return {
            "explanation": str(parsed.get("explanation", "")),
            "recommendations": [str(item) for item in parsed["recommendations"][:3]],
        }
    except Exception:
        return _fallback_explanation(payload)
