from __future__ import annotations

from pathlib import Path

import pandas as pd
from fastapi import HTTPException

from app.services.ml_bridge import detect_bias
from app.services.state import (
    get_latest_uploaded_path,
    set_latest_scan_report,
)

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

    result = detect_bias(
        df=df,
        target_column=detected_target,
        sensitive_candidates=SENSITIVE_COLUMNS,
    )
    result["dataset_path"] = str(path)

    set_latest_scan_report(result)
    return result
