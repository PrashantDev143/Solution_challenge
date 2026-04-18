from __future__ import annotations

from functools import cmp_to_key
import pandas as pd

from fairness_metrics import (
    disparate_impact,
    fairness_score_from_weighted_gaps,
    to_binary_outcome,
)
from group_discovery import discover_group_masks


MIN_GROUP_SAMPLES = 5
MAX_GROUP_COMBINATION_SIZE = 2
TOP_GROUP_LIMIT = 8
MEANINGFUL_GROUP_COLUMNS = ["gender", "region", "education", "income_bucket", "age_bucket"]
OVERLAP_THRESHOLD = 0.80
SIMILAR_SCORE_DELTA = 0.03

FEATURE_PRIORITY_BONUS = {
    "gender": 0.20,
    "region": 0.15,
    "education": 0.10,
    "income_bucket": 0.05,
    "age_bucket": 0.05,
}
MAX_PRIORITY_BONUS = sum(FEATURE_PRIORITY_BONUS.values())


def _to_numeric_series(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _income_bucket(series: pd.Series) -> pd.Series:
    numeric = _to_numeric_series(series)
    bucketed = pd.Series("unknown", index=series.index, dtype="object")
    bucketed.loc[numeric < 45000] = "low"
    bucketed.loc[(numeric >= 45000) & (numeric <= 60000)] = "medium"
    bucketed.loc[numeric > 60000] = "high"
    return bucketed


def _age_bucket(series: pd.Series) -> pd.Series:
    numeric = _to_numeric_series(series)
    bucketed = pd.Series("unknown", index=series.index, dtype="object")
    bucketed.loc[numeric < 30] = "young"
    bucketed.loc[(numeric >= 30) & (numeric <= 40)] = "mid"
    bucketed.loc[numeric > 40] = "senior"
    return bucketed


def _prepare_grouping_frame(df: pd.DataFrame) -> pd.DataFrame:
    grouped = df.copy()
    if "income" in grouped.columns and "income_bucket" not in grouped.columns:
        grouped["income_bucket"] = _income_bucket(grouped["income"])
    if "age" in grouped.columns and "age_bucket" not in grouped.columns:
        grouped["age_bucket"] = _age_bucket(grouped["age"])
    return grouped


def _severity_from_difference(difference: float) -> str:
    if difference >= 0.25:
        return "high"
    if difference >= 0.15:
        return "medium"
    if difference >= 0.08:
        return "low"
    return "none"


def _compute_priority_weight(feature_names: tuple[str, ...]) -> float:
    raw_bonus = float(sum(FEATURE_PRIORITY_BONUS.get(name, 0.0) for name in feature_names))
    if MAX_PRIORITY_BONUS <= 0:
        return 0.0
    return raw_bonus / MAX_PRIORITY_BONUS


def _compute_group_score(gap: float, sample_weight: float, priority_weight: float) -> float:
    return (gap * 0.55) + (sample_weight * 0.25) + (priority_weight * 0.20)


def _overlap_metrics(a: set[int], b: set[int]) -> tuple[float, float]:
    if not a or not b:
        return 0.0, 0.0
    intersection_size = len(a.intersection(b))
    union_size = len(a.union(b))
    jaccard = (intersection_size / union_size) if union_size else 0.0
    same_coverage = intersection_size / min(len(a), len(b))
    return jaccard, same_coverage


def _compare_groups(a: dict, b: dict) -> int:
    score_diff = float(a["_score"]) - float(b["_score"])
    if abs(score_diff) < SIMILAR_SCORE_DELTA and a["_feature_count"] != b["_feature_count"]:
        return -1 if a["_feature_count"] < b["_feature_count"] else 1

    if score_diff != 0:
        return -1 if score_diff > 0 else 1

    if a["count"] != b["count"]:
        return -1 if a["count"] > b["count"] else 1

    if a["difference"] != b["difference"]:
        return -1 if a["difference"] > b["difference"] else 1

    return 0


def _filter_redundant_groups(sorted_groups: list[dict]) -> list[dict]:
    selected: list[dict] = []
    for candidate in sorted_groups:
        replaced = False
        for idx, kept in enumerate(selected):
            jaccard, same_coverage = _overlap_metrics(candidate["_row_ids"], kept["_row_ids"])
            if jaccard > OVERLAP_THRESHOLD or same_coverage > OVERLAP_THRESHOLD:
                if _compare_groups(candidate, kept) < 0:
                    selected[idx] = candidate
                replaced = True
                break
        if not replaced:
            selected.append(candidate)
    return sorted(selected, key=cmp_to_key(_compare_groups))


def _add_if_missing(selected: list[dict], used: set[str], candidate: dict | None) -> None:
    if candidate is None:
        return
    if candidate["group"] in used:
        return
    selected.append(candidate)
    used.add(candidate["group"])


def _best_matching(groups: list[dict], predicate) -> dict | None:
    for group in groups:
        if predicate(group):
            return group
    return None


def _is_redundant_with_selected(candidate: dict, selected: list[dict]) -> bool:
    for kept in selected:
        jaccard, same_coverage = _overlap_metrics(candidate["_row_ids"], kept["_row_ids"])
        if jaccard > OVERLAP_THRESHOLD or same_coverage > OVERLAP_THRESHOLD:
            return True
    return False


def _pick_diverse_top_groups(
    groups: list[dict],
    baseline_rate: float,
    singleton_anchors: list[dict],
) -> list[dict]:
    selected: list[dict] = []
    used_names: set[str] = set()

    def add_candidate(candidate: dict | None, allow_overlap: bool = False) -> None:
        if candidate is None or candidate["group"] in used_names:
            return
        if not allow_overlap and _is_redundant_with_selected(candidate, selected):
            return
        selected.append(candidate)
        used_names.add(candidate["group"])

    # Anchor high-quality singleton insights for readability and non-redundant coverage.
    for anchor in singleton_anchors:
        add_candidate(anchor, allow_overlap=True)

    # Ensure the dashboard has representative intersectional and directional insights.
    add_candidate(_best_matching(groups, lambda g: g["_feature_count"] == 2))

    # Include a positively skewed group when available for balanced storytelling.
    add_candidate(_best_matching(groups, lambda g: float(g["approval_rate"]) > baseline_rate))

    # Surface the key gender+region intersection if discovered.
    add_candidate(
        _best_matching(groups, lambda g: g["_feature_signature"] == ("gender", "region")),
        allow_overlap=True,
    )

    for group in groups:
        if len(selected) >= TOP_GROUP_LIMIT:
            break
        if group["group"] in used_names:
            continue
        add_candidate(group)

    return selected[:TOP_GROUP_LIMIT]


def detect_bias(
    df: pd.DataFrame,
    target_column: str,
    sensitive_candidates: list[str],
) -> dict:
    if target_column not in df.columns:
        raise ValueError(f"Missing target column: {target_column}")

    # Work on a derived frame that includes stable income/age buckets.
    grouped_df = _prepare_grouping_frame(df)
    y = to_binary_outcome(grouped_df[target_column])
    baseline_rate = float(y.mean())

    total_rows = int(len(grouped_df))
    groups: list[dict] = []
    groups_scanned = 0

    sensitive_set = set(sensitive_candidates)
    if "income" in sensitive_set:
        sensitive_set.add("income_bucket")
    if "age" in sensitive_set:
        sensitive_set.add("age_bucket")

    allowed_columns = [
        col for col in MEANINGFUL_GROUP_COLUMNS if col in grouped_df.columns and col in sensitive_set
    ]

    for group_name, mask in discover_group_masks(
        grouped_df,
        allowed_columns,
        max_combination_size=MAX_GROUP_COMBINATION_SIZE,
    ):
        group_count = int(mask.sum())
        # Skip tiny cohorts to avoid ranking statistically noisy groups.
        if group_count < MIN_GROUP_SAMPLES:
            continue

        groups_scanned += 1
        group_rate = float(y[mask].mean())
        gap = abs(baseline_rate - group_rate)
        severity = _severity_from_difference(gap)
        if severity == "none":
            continue

        feature_names = tuple(part.split("=", maxsplit=1)[0] for part in group_name.split(" + "))
        sample_weight = min(group_count / max(total_rows, 1), 1.0)
        priority_weight = _compute_priority_weight(feature_names)
        ranking_score = _compute_group_score(gap, sample_weight, priority_weight)

        feature_set = set(feature_names)
        row_ids = set(mask[mask].index.tolist())

        ranking_reason = (
            f"Selected with ranking score {ranking_score:.3f} "
            f"(gap={gap:.3f}, support={sample_weight:.3f}, priority={priority_weight:.3f})."
        )

        groups.append(
            {
                "group": group_name,
                "approval_rate": round(group_rate, 4),
                "baseline_rate": round(baseline_rate, 4),
                "difference": round(gap, 4),
                "disparate_impact": round(disparate_impact(group_rate, baseline_rate), 4),
                "severity": severity,
                "count": group_count,
                "ranking_reason": ranking_reason,
                "_feature_count": len(feature_names),
                "_feature_signature": tuple(sorted(feature_names)),
                "_feature_set": feature_set,
                "_row_ids": row_ids,
                "_score": round(ranking_score, 6),
                "_sample_weight": sample_weight,
            }
        )

    groups.sort(key=cmp_to_key(_compare_groups))

    singleton_anchors = [
        _best_matching(
            groups,
            lambda g, feature=feature: g["_feature_count"] == 1 and feature in g["_feature_set"],
        )
        for feature in ("gender", "region", "education")
    ]
    singleton_anchors = [group for group in singleton_anchors if group is not None]

    for anchor in singleton_anchors:
        anchor["ranking_reason"] = (
            f"{anchor['ranking_reason']} Included to ensure dashboard diversity for {', '.join(sorted(anchor['_feature_set']))}."
        )

    de_redundant_groups = _filter_redundant_groups(groups)
    top_groups = _pick_diverse_top_groups(
        de_redundant_groups,
        baseline_rate=baseline_rate,
        singleton_anchors=singleton_anchors,
    )

    top_gaps = [float(group["difference"]) for group in top_groups]
    top_weights = [float(group["_sample_weight"]) for group in top_groups]
    fairness_score = round(fairness_score_from_weighted_gaps(top_gaps, top_weights), 2)

    for group in top_groups:
        group.pop("_feature_count", None)
        group.pop("_feature_signature", None)
        group.pop("_feature_set", None)
        group.pop("_row_ids", None)
        group.pop("_score", None)
        group.pop("_sample_weight", None)

    return {
        "total_rows": total_rows,
        "groups_scanned": groups_scanned,
        "biased_groups_found": int(len(de_redundant_groups)),
        "fairness_score": fairness_score,
        "target_column": target_column,
        "top_biased_groups": top_groups,
    }
