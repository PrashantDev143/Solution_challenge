from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import HTTPException

from app.services.ml_bridge import predict_profile, train_predictive_model
from app.services.state import get_latest_uploaded_path

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


_model_cache: dict[tuple[str, str], Any] = {}


def _pretty_label(column_name: str) -> str:
    return " ".join(part.capitalize() for part in column_name.replace("_", " ").split())


def _resolve_dataset_path(dataset_path: str | None) -> Path:
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


def _resolve_target_column(df: pd.DataFrame, target_column: str | None) -> str:
    if target_column:
        if target_column in df.columns:
            return target_column
        raise HTTPException(status_code=400, detail=f"Requested target column not found: {target_column}")

    for candidate in DEFAULT_TARGET_CANDIDATES:
        if candidate in df.columns:
            return candidate

    for column in df.columns:
        if _is_binary_zero_one_column(df[column]):
            return str(column)

    if len(df.columns) == 0:
        raise HTTPException(status_code=400, detail="Dataset has no columns.")

    return str(df.columns[-1])


def _field_type(series: pd.Series) -> str:
    return "numeric" if pd.api.types.is_numeric_dtype(series) else "categorical"


def _field_default(series: pd.Series, inferred_type: str) -> str | float | int | None:
    cleaned = series.dropna()
    if cleaned.empty:
        return 0 if inferred_type == "numeric" else ""

    if inferred_type == "numeric":
        value = pd.to_numeric(cleaned, errors="coerce").median()
        if pd.isna(value):
            return 0
        return float(value)

    return str(cleaned.iloc[0])


def _categorical_options(series: pd.Series) -> list[str]:
    cleaned = series.dropna().astype(str).str.strip()
    unique_values = sorted(set(value for value in cleaned.tolist() if value != ""))
    return unique_values[:100]


def get_simulation_schema(dataset_path: str | None = None, target_column: str | None = None) -> dict:
    path = _resolve_dataset_path(dataset_path)

    try:
        df = pd.read_csv(path)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid CSV dataset: {exc}") from exc

    if df.empty:
        raise HTTPException(status_code=400, detail="Dataset is empty.")

    target = _resolve_target_column(df, target_column)

    fields: list[dict[str, Any]] = []
    for column in df.columns:
        if column == target:
            continue

        inferred_type = _field_type(df[column])
        field: dict[str, Any] = {
            "name": str(column),
            "label": _pretty_label(str(column)),
            "type": inferred_type,
            "default": _field_default(df[column], inferred_type),
        }

        if inferred_type == "categorical":
            field["options"] = _categorical_options(df[column])

        fields.append(field)

    if not fields:
        raise HTTPException(status_code=400, detail="No feature columns available for simulation.")

    return {
        "dataset_path": str(path),
        "target_column": target,
        "fields": fields,
    }


def run_simulation(
    dataset_path: str | None,
    target_column: str | None,
    baseline_features: dict[str, Any],
    scenario_features: dict[str, Any],
) -> dict:
    path = _resolve_dataset_path(dataset_path)

    try:
        df = pd.read_csv(path)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid CSV dataset: {exc}") from exc

    if df.empty:
        raise HTTPException(status_code=400, detail="Dataset is empty.")

    target = _resolve_target_column(df, target_column)
    cache_key = (str(path), target)

    model = _model_cache.get(cache_key)
    if model is None:
        model = train_predictive_model(df, target)
        _model_cache[cache_key] = model

    before = predict_profile(model, baseline_features)
    after = predict_profile(model, scenario_features)

    changed = before["prediction"] != after["prediction"]
    probability_changed = abs(float(before["probability"]) - float(after["probability"])) >= 0.01

    if changed:
        message = "Changing profile inputs changed the predicted outcome."
    elif probability_changed:
        message = "Risk score changed even though final decision stayed same."
    else:
        message = "The prediction stayed the same for these what-if changes."

    return {
        "baseline": before,
        "scenario": after,
        "baseline_prediction": int(before["prediction"]),
        "baseline_probability": float(before["probability"]),
        "scenario_prediction": int(after["prediction"]),
        "scenario_probability": float(after["probability"]),
        "changed": changed,
        "message": message,
    }
