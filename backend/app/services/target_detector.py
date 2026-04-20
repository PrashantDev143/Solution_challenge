from typing import Optional
import pandas as pd

KNOWN_TARGETS = {
    "approved",
    "prediction",
    "outcome",
    "loan_status",
    "hired",
    "selected",
    "subsidy_approved",
    "claim_approved",
}


def detect_target(df: pd.DataFrame) -> Optional[str]:
    cols = [c.lower().strip() for c in df.columns]
    # exact match
    for orig, c in zip(df.columns, cols):
        if c in KNOWN_TARGETS:
            return orig

    # binary 0/1 detection
    for col in df.columns:
        try:
            ser = df[col].dropna().unique()
            # allow booleans and numeric 0/1
            vals = set([v for v in ser if v is not None])
            if vals <= {0, 1} or vals <= {0.0, 1.0} or vals <= {"0", "1"}:
                return col
        except Exception:
            continue

    # fallback to last column
    if len(df.columns) > 0:
        return df.columns[-1]
    return None
