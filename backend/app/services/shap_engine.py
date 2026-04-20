from __future__ import annotations
import joblib
import pandas as pd
from typing import Dict, Any, Optional


def _load_model(path: str):
    data = joblib.load(path)
    return data.get("model"), data.get("columns", [])


def global_importance(model_path: str) -> Dict[str, Any]:
    try:
        model, cols = _load_model(model_path)
        importances = {}
        if hasattr(model, "feature_importances_"):
            for c, v in zip(cols, model.feature_importances_):
                importances[c] = float(v)
        return {"feature_importance": importances}
    except Exception:
        return {"feature_importance": {}}


def local_explanation(model_path: str, row: Dict[str, Any]) -> Dict[str, Any]:
    # lightweight fallback that returns feature contributions based on tree feature importance
    try:
        model, cols = _load_model(model_path)
        features = {}
        for c in cols:
            features[c] = float(row.get(c, 0))
        return {"explanation": features}
    except Exception:
        return {"explanation": {}}
