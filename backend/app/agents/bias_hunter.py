from __future__ import annotations
from typing import Dict, Any
import pandas as pd
from app.services.fairness_engine import scan_groups


class BiasHunter:
    def __init__(self, df: pd.DataFrame, target: str):
        self.df = df
        self.target = target

    def run(self) -> Dict[str, Any]:
        findings = scan_groups(self.df, self.target)
        return {"groups_scanned": len(findings), "top_groups": findings[:10]}
