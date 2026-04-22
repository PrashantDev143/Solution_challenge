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


def _group_dict_to_string(group_dict: Dict) -> str:
    """Convert group dictionary to string representation like 'gender=male + region=urban'"""
    parts = []
    for key, value in sorted(group_dict.items()):
        parts.append(f"{key}={value}")
    return " + ".join(parts)


def _compute_disparate_impact(group_rate: float, baseline_rate: float) -> float:
    """Compute disparate impact ratio (selection rate of group / selection rate of baseline)"""
    if baseline_rate == 0:
        return 1.0
    return round(group_rate / baseline_rate, 3)


def _get_ranking_reason(gap: float, severity: str, group_rate: float, baseline_rate: float) -> str:
    """Generate a ranking reason string based on the gap and severity"""
    if severity == "high":
        return f"Severe disparity: {abs(gap):.1%} approval rate gap"
    elif severity == "medium":
        return f"Moderate disparity: {abs(gap):.1%} approval rate gap"
    elif severity == "low":
        return f"Minor advantage: {gap:.1%} approval rate gap"
    else:
        return f"Group rate {group_rate:.1%} vs baseline {baseline_rate:.1%}"


def scan_groups(df: pd.DataFrame, target_col: str, min_support: int = None) -> List[Dict[str, Any]]:
    # Adaptive min_support: 10% of dataset size, but at least 2 and at most 30
    if min_support is None:
        min_support = max(2, min(int(len(df) * 0.1), 30))
    
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
            severity = "low"  # default to low
            if gap is not None:
                if gap <= -0.20:
                    category = "underprivileged"
                    severity = "high"
                elif gap <= -0.10:
                    category = "underprivileged"
                    severity = "medium"
                elif gap >= 0.20:
                    category = "privileged"
                    severity = "low"
                elif gap >= 0.10:
                    category = "privileged"
                    severity = "low"
                else:
                    category = "balanced"
                    severity = "low"

            # Build group dictionary for conversion
            group_dict = {k: row[k] for k in comb}
            group_str = _group_dict_to_string(group_dict)
            
            # Compute disparate impact
            di = _compute_disparate_impact(group_rate, base_rate) if base_rate else 1.0
            
            # Get ranking reason
            ranking_reason = _get_ranking_reason(gap if gap else 0, severity, group_rate, base_rate if base_rate else 0)

            results.append({
                "group": group_str,
                "count": support,
                "approval_rate": round(group_rate, 3),
                "baseline_rate": round(base_rate, 3) if base_rate else None,
                "difference": round(gap, 3) if gap is not None else 0,
                "disparate_impact": di,
                "gap": gap,
                "category": category,
                "severity": severity,
                "ranking_reason": ranking_reason,
            })

    # sort by absolute gap magnitude (largest disparities first)
    results = sorted(results, key=lambda x: abs(x.get("gap") or 0), reverse=True)
    return results
