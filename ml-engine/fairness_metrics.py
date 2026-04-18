from __future__ import annotations

import numpy as np
import pandas as pd


TRUE_TOKENS = {"1", "true", "yes", "approved", "pass", "positive"}


def to_binary_outcome(series: pd.Series) -> pd.Series:
    if series.dtype.kind in {"i", "u", "f", "b"}:
        return (series.fillna(0).astype(float) > 0).astype(int)

    normalized = (
        series.astype(str)
        .str.strip()
        .str.lower()
        .map(lambda value: 1 if value in TRUE_TOKENS else 0)
    )
    return normalized.fillna(0).astype(int)


def disparate_impact(group_rate: float, baseline_rate: float) -> float:
    if baseline_rate <= 0:
        return 0.0
    return float(group_rate / baseline_rate)


def fairness_score_from_gaps(gaps: list[float]) -> float:
    """Convert mean approval-rate gap into a fairness score in [0, 100]."""
    if not gaps:
        return 100.0
    mean_gap = float(np.mean(gaps))
    return float(np.clip(100.0 - (mean_gap * 100.0), 0.0, 100.0))


def fairness_score_from_weighted_gaps(gaps: list[float], weights: list[float]) -> float:
    """Convert weighted average gap into a fairness score in [0, 100]."""
    if not gaps:
        return 100.0

    safe_weights = np.asarray(weights, dtype=float)
    if safe_weights.size != len(gaps) or float(safe_weights.sum()) <= 0:
        return fairness_score_from_gaps(gaps)

    safe_weights = safe_weights / safe_weights.sum()
    weighted_gap = float(np.dot(np.asarray(gaps, dtype=float), safe_weights))
    return float(np.clip(100.0 - (weighted_gap * 100.0), 0.0, 100.0))
