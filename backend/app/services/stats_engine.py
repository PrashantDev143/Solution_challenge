from __future__ import annotations
import scipy.stats as stats
import math
from typing import Tuple


def chi2_test(table) -> Tuple[float, float]:
    try:
        chi2, p, dof, ex = stats.chi2_contingency(table)
        return float(chi2), float(p)
    except Exception:
        return math.nan, math.nan


def fisher_exact_test(table) -> Tuple[float, float]:
    try:
        # table expected 2x2
        oddsratio, p = stats.fisher_exact(table)
        return float(oddsratio), float(p)
    except Exception:
        return math.nan, math.nan


def confidence_interval_proportion(successes: int, n: int, z: float = 1.96) -> Tuple[float, float]:
    if n == 0:
        return 0.0, 0.0
    p = successes / n
    se = (p * (1 - p) / n) ** 0.5
    return float(max(0, p - z * se)), float(min(1, p + z * se))
