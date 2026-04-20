import os
from typing import Dict, Any
from time import sleep

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


def generate_report(prompt: str | None = None, findings: list | None = None, max_retries: int = 2) -> Dict[str, Any]:
    # If Gemini key missing, build fallback report from findings if provided
    if not GEMINI_API_KEY:
        if findings:
            risks = []
            recommendations = []
            summaries = []
            for g in findings:
                cat = g.get("category")
                if cat == "underprivileged":
                    summaries.append("This group receives lower approvals than baseline.")
                    risks.append(str(g.get("group")))
                    recommendations.append("Investigate and remediate underprivileged group: " + str(g.get("group")))
                elif cat == "privileged":
                    summaries.append("This group receives higher approvals than baseline and may indicate imbalance.")
                else:
                    summaries.append("No material disparity detected.")

            return {
                "summary": "Fallback report",
                "risks": risks,
                "recommendations": recommendations,
                "executive_brief": " ".join(summaries),
            }

        return {
            "summary": "Gemini key missing - fallback report",
            "risks": ["Gemini API not configured"],
            "recommendations": ["Provide GEMINI_API_KEY for richer reports"],
            "executive_brief": "A concise brief is unavailable without Gemini key.",
        }

    # Placeholder for real Gemini call with retry logic
    for attempt in range(max_retries + 1):
        try:
            # TODO: integrate google-generativeai client calls here
            sleep(0.5)
            return {
                "summary": "Generated summary (stub)",
                "risks": [],
                "recommendations": [],
                "executive_brief": "(generated)",
            }
        except Exception:
            sleep(0.5)
            continue

    return {
        "summary": "Failed to generate report",
        "risks": [],
        "recommendations": [],
        "executive_brief": "",
    }
