from __future__ import annotations

from pathlib import Path

import pandas as pd
from fastapi import HTTPException

from app.services.fairness_engine import scan_groups
from app.services.state import (
    get_latest_uploaded_path,
    set_latest_scan_report,
)
from app.services.cache_service import set_report

DEFAULT_TARGET_CANDIDATES = [
    "approved",
    "prediction",
    "outcome",
    "loan_status",
    "hired",
    "selected",
    "subsidy_approved",
    "claim_approved",
]
SENSITIVE_COLUMNS = ["gender", "region", "income", "education", "age"]


def _resolve_dataset_path(dataset_path: str | None) -> Path:
    # Prefer the latest uploaded file so scan always reflects the current dataset session.
    resolved = get_latest_uploaded_path() or dataset_path
    if not resolved:
        raise HTTPException(
            status_code=400,
            detail="No dataset found. Upload a CSV first or provide dataset_path.",
        )

    path = Path(resolved)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Dataset not found: {resolved}")

    return path


def _is_binary_zero_one_column(series: pd.Series) -> bool:
    cleaned = series.dropna()
    if cleaned.empty:
        return False

    numeric = pd.to_numeric(cleaned, errors="coerce")
    if numeric.notna().all():
        unique_values = set(numeric.unique().tolist())
        return unique_values.issubset({0, 1})

    normalized = cleaned.astype(str).str.strip().str.lower()
    unique_tokens = set(normalized.unique().tolist())
    return unique_tokens.issubset({"0", "1"})


def _detect_target_column(df: pd.DataFrame, requested_target: str | None) -> str:
    if requested_target:
        if requested_target in df.columns:
            return requested_target
        raise HTTPException(
            status_code=400,
            detail=f"Requested target column not found: {requested_target}",
        )

    for candidate in DEFAULT_TARGET_CANDIDATES:
        if candidate in df.columns:
            return candidate

    for column in df.columns:
        if _is_binary_zero_one_column(df[column]):
            return str(column)

    if len(df.columns) == 0:
        raise HTTPException(status_code=400, detail="Dataset has no columns.")

    return str(df.columns[-1])


def run_bias_scan(dataset_path: str | None = None, target_column: str | None = None) -> dict:
    path = _resolve_dataset_path(dataset_path)

    try:
        df = pd.read_csv(path)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid CSV dataset: {exc}") from exc

    if df.empty:
        raise HTTPException(status_code=400, detail="Dataset is empty.")

    detected_target = _detect_target_column(df, target_column)
    print(f"[scan_service] Running scan on {path} with target={detected_target}")

    groups = scan_groups(df, detected_target)

    total_rows = len(df)

    # top biased groups: only underprivileged
    top_groups = [g for g in groups if g.get("category") == "underprivileged"][:10]

    # groups details: include all groups
    groups_details = groups

    # severity breakdown (count only underprivileged groups)
    severity_breakdown = {"high": 0, "medium": 0, "low": 0}
    for g in groups:
        if g.get("category") == "underprivileged":
            sev = g.get("severity")
            if sev in severity_breakdown:
                severity_breakdown[sev] += 1

    # fairness score: penalize only underprivileged gaps (negative gaps)
    penalty = 0.0
    for g in groups:
        if g.get("category") == "underprivileged":
            gap = g.get("gap") or 0.0
            count = g.get("count") or 0
            # only negative gaps (underprivileged) contribute
            if gap < 0:
                penalty += (abs(gap) * 100.0) * (count / total_rows)

    fairness_score = max(0.0, 100.0 - penalty)

    result = {
        "dataset_path": str(path),
        "total_rows": total_rows,
        "groups_scanned": len(groups_details),
        "top_groups": top_groups,
        "groups": groups_details,
        "severity_breakdown": severity_breakdown,
        "fairness_score": round(fairness_score, 3),
    }

    if not top_groups:
        result["message"] = "No harmful bias detected"

    # populate backwards-compatible fields to avoid frontend breakage
    result["biased_groups_found"] = len([g for g in groups_details if g.get("category") == "underprivileged"])
    result["top_biased_groups"] = result.get("top_groups", [])
    result["target_column"] = detected_target

    # store report in both state and shared cache for robustness
    try:
        set_latest_scan_report(result)
    except Exception:
        pass
    try:
        set_report(result)
    except Exception:
        pass

    return result
