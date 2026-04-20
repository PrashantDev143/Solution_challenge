from __future__ import annotations
from typing import Dict, Any
import pandas as pd
from app.services.shap_engine import global_importance
from app.services.cache_service import get_cache


class ExplainabilityAgent:
    def __init__(self, df: pd.DataFrame, target: str):
        self.df = df
        self.target = target

    def run(self) -> Dict[str, Any]:
        model_info = get_cache("latest_model_path")
        if not model_info:
            return {"shap_summary": {}, "note": "No model available"}
        model_path = model_info
        gi = global_importance(model_path)
        return {"shap_summary": gi}
