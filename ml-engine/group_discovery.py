from __future__ import annotations

from itertools import combinations
from typing import Iterable

import pandas as pd


def _normalize_group_value(value: object) -> str:
    if pd.isna(value):
        return "unknown"
    return str(value).strip().lower()


def discover_group_masks(
    df: pd.DataFrame,
    sensitive_columns: list[str],
    max_combination_size: int = 2,
) -> Iterable[tuple[str, pd.Series]]:
    """Yield group names and masks for single and intersectional groups."""
    usable_columns = [col for col in sensitive_columns if col in df.columns]

    if not usable_columns:
        return

    grouped_frame = df.copy()
    for col in usable_columns:
        grouped_frame[col] = grouped_frame[col].map(_normalize_group_value)

    for combo_size in range(1, min(max_combination_size, len(usable_columns)) + 1):
        for combo in combinations(usable_columns, combo_size):
            grouped = grouped_frame.groupby(list(combo), dropna=False)
            for key, indices in grouped.groups.items():
                values = key if isinstance(key, tuple) else (key,)
                parts = [f"{col}={val}" for col, val in zip(combo, values)]
                group_name = " + ".join(parts)
                mask = grouped_frame.index.isin(indices)
                yield group_name, pd.Series(mask, index=grouped_frame.index)
