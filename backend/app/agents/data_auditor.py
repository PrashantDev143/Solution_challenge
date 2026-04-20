from __future__ import annotations
import pandas as pd
from typing import Dict, Any


class DataAuditor:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def run(self) -> Dict[str, Any]:
        dq = {
            "rows": int(len(self.df)),
            "columns": list(self.df.columns),
            "missing_per_column": {c: int(self.df[c].isna().sum()) for c in self.df.columns},
            "duplicate_rows": int(self.df.duplicated().sum()),
        }
        return dq
