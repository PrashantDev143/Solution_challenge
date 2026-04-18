from __future__ import annotations

from typing import Any

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from fairness_metrics import to_binary_outcome


RANDOM_STATE = 42


def train_predictive_model(df: pd.DataFrame, target_column: str) -> Pipeline:
    if target_column not in df.columns:
        raise ValueError(f"Missing target column: {target_column}")

    y = to_binary_outcome(df[target_column])
    X = df.drop(columns=[target_column]).copy()

    numeric_features = X.select_dtypes(include=["number"]).columns.tolist()
    categorical_features = [col for col in X.columns if col not in numeric_features]

    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, numeric_features),
            ("cat", categorical_pipeline, categorical_features),
        ],
        remainder="drop",
    )

    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "classifier",
                LogisticRegression(
                    max_iter=800,
                    random_state=RANDOM_STATE,
                    solver="liblinear",
                    C=2.0,
                ),
            ),
        ]
    )

    model.fit(X, y)
    return model


def predict_profile(model: Pipeline, profile: dict[str, Any]) -> dict:
    expected_columns = list(getattr(model, "feature_names_in_", []))
    input_payload = profile.copy()
    for col in expected_columns:
        input_payload.setdefault(col, None)

    input_df = pd.DataFrame([input_payload])
    if expected_columns:
        input_df = input_df[expected_columns]

    probabilities = model.predict_proba(input_df)[0]
    prediction = int(model.predict(input_df)[0])

    positive_probability = float(probabilities[1]) if len(probabilities) > 1 else float(probabilities[0])

    return {
        "prediction": prediction,
        "probability": round(positive_probability, 4),
    }
