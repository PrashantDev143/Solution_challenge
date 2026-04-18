from pydantic import BaseModel, Field


class ScanRequest(BaseModel):
    dataset_path: str | None = None
    target_column: str | None = None


class BiasedGroup(BaseModel):
    group: str
    approval_rate: float
    baseline_rate: float
    difference: float
    disparate_impact: float
    severity: str
    count: int
    ranking_reason: str | None = None


class ScanResponse(BaseModel):
    total_rows: int
    groups_scanned: int
    biased_groups_found: int
    fairness_score: float = Field(ge=0, le=100)
    target_column: str
    top_biased_groups: list[BiasedGroup]
