from __future__ import annotations
import threading
from pathlib import Path
import joblib
from app.services.cache_service import set_cache
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

try:
    from xgboost import XGBClassifier
except Exception:
    XGBClassifier = None

MODELS_DIR = Path(__file__).resolve().parents[2] / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


def _preprocess_simple(df: pd.DataFrame, target_col: str):
    df = df.copy()
    y = df[target_col]
    X = df.drop(columns=[target_col])

    # fill missing numeric with median and categorical with mode
    for col in X.columns:
        if pd.api.types.is_numeric_dtype(X[col]):
            X[col] = X[col].fillna(X[col].median())
        else:
            X[col] = X[col].fillna(X[col].mode().iloc[0] if not X[col].mode().empty else "")

    # one-hot encode categoricals (pandas.get_dummies)
    X = pd.get_dummies(X, drop_first=True)
    return X, y


def train_model(df: pd.DataFrame, target_col: str, model_name: str = "latest_model") -> dict:
    if target_col is None or target_col not in df.columns:
        raise ValueError("Invalid target column for training")

    X, y = _preprocess_simple(df, target_col)

    # simple train/test split
    stratify = y if len(np.unique(y)) == 2 else None
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=stratify
    )

    model = None
    if XGBClassifier is not None:
        try:
            model = XGBClassifier(use_label_encoder=False, eval_metric="logloss")
            model.fit(X_train, y_train)
        except Exception:
            model = None

    if model is None:
        model = RandomForestClassifier(n_estimators=100, n_jobs=-1, random_state=42)
        model.fit(X_train, y_train)

    preds = model.predict(X_test)
    metrics = {
        "accuracy": float(accuracy_score(y_test, preds)),
        "precision": float(precision_score(y_test, preds, zero_division=0, average="binary" if len(np.unique(y))==2 else "macro")),
        "recall": float(recall_score(y_test, preds, zero_division=0, average="binary" if len(np.unique(y))==2 else "macro")),
        "f1": float(f1_score(y_test, preds, zero_division=0, average="binary" if len(np.unique(y))==2 else "macro")),
    }

    model_path = MODELS_DIR / f"{model_name}.joblib"
    joblib.dump({"model": model, "columns": X.columns.tolist()}, model_path)
    try:
        set_cache("latest_model_path", str(model_path))
    except Exception:
        pass

    return {"model_path": str(model_path), "metrics": metrics}


def _train_thread(df, target_col, model_name):
    try:
        train_model(df, target_col, model_name=model_name)
    except Exception:
        pass


def train_model_background(df: pd.DataFrame, target_col: str, model_name: str = "latest_model"):
    t = threading.Thread(target=_train_thread, args=(df, target_col, model_name), daemon=True)
    t.start()
    return t
