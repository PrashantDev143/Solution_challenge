from pydantic import BaseModel


class ExplainRequest(BaseModel):
    group: str
    count: int | None = None
    approval_rate: float
    baseline_rate: float
    difference: float
    severity: str
    ranking_reason: str | None = None


class ExplainResponse(BaseModel):
    explanation: str
    recommendations: list[str]
