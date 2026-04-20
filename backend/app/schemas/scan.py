from pydantic import BaseModel
from typing import Any, Optional


class ScanRequest(BaseModel):
    dataset_path: str
    target_column: Optional[str] = None


class ScanResponse(BaseModel):
    dataset_path: str
    total_rows: int
    groups_scanned: int
    fairness_score: float
    severity_breakdown: dict[str, int]

    groups: list[dict[str, Any]] = []
    top_groups: list[dict[str, Any]] = []

    biased_groups_found: int = 0
    top_biased_groups: list[dict[str, Any]] = []
    target_column: Optional[str] = None
    message: Optional[str] = None