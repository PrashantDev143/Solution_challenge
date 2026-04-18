from typing import Any

from pydantic import BaseModel


class SimulateRequest(BaseModel):
    dataset_path: str | None = None
    target_column: str | None = None
    baseline_features: dict[str, Any]
    scenario_features: dict[str, Any]


class PredictionResult(BaseModel):
    prediction: int
    probability: float


class SimulateField(BaseModel):
    name: str
    label: str
    type: str
    options: list[str] | None = None
    default: str | float | int | None = None


class SimulateSchemaResponse(BaseModel):
    dataset_path: str
    target_column: str
    fields: list[SimulateField]


class SimulateResponse(BaseModel):
    baseline: PredictionResult
    scenario: PredictionResult
    baseline_prediction: int | None = None
    baseline_probability: float | None = None
    scenario_prediction: int | None = None
    scenario_probability: float | None = None
    changed: bool | None = None
    message: str
