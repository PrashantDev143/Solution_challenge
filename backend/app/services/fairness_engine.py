from __future__ import annotations
import pandas as pd
from typing import List, Dict, Any
import itertools


SENSITIVE_CANDIDATES = [
    "gender",
    "sex",
    "region",
    "caste",
    "race",
    "age_group",
    "education",
    "income_bucket",
    "location",
    "farmer_gender",
]


def _candidate_columns(df: pd.DataFrame) -> List[str]:
    cols = [c for c in df.columns if pd.api.types.is_object_dtype(df[c]) or c.lower() in SENSITIVE_CANDIDATES]
    if not cols:
        # fallback to categorical-ish columns
        cols = [c for c in df.columns if df[c].nunique() < min(50, len(df) // 2)]
    return cols


def scan_groups(df: pd.DataFrame, target_col: str, min_support: int = 30) -> List[Dict[str, Any]]:
    candidates = _candidate_columns(df.drop(columns=[target_col]))
    results = []
    # single and pair combinations
    combs = []
    for k in (1, 2):
        combs.extend(list(itertools.combinations(candidates, k)))

    base_rate = float(df[target_col].mean()) if pd.api.types.is_numeric_dtype(df[target_col]) else None

    for comb in combs:
        grp = df.groupby(list(comb))[target_col].agg(["count", "mean"]).reset_index()
        for _, row in grp.iterrows():
            support = int(row["count"])
            if support < min_support:
                continue
            group_rate = float(row["mean"])

            # compute gap (group_rate - baseline)
            gap = None
            if base_rate is not None:
                gap = group_rate - base_rate

            # categorize based on gap thresholds
            category = "balanced"
            severity = "none"
            if gap is not None:
                if gap <= -0.20:
                    category = "underprivileged"
                    severity = "high"
                elif gap <= -0.10:
                    category = "underprivileged"
                    severity = "medium"
                elif gap >= 0.20:
                    category = "privileged"
                    severity = "info"
                elif gap >= 0.10:
                    category = "privileged"
                    severity = "low"
                else:
                    category = "balanced"
                    severity = "none"

            results.append({
                "group": {k: row[k] for k in comb},
                "count": support,
                "approval_rate": group_rate,
                "baseline_rate": base_rate,
                "gap": gap,
                "category": category,
                "severity": severity,
            })

    # sort by absolute gap magnitude (largest disparities first)
    results = sorted(results, key=lambda x: abs(x.get("gap") or 0), reverse=True)
    return results
