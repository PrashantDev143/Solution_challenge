from fastapi import APIRouter

from app.schemas.explain import ExplainRequest, ExplainResponse
from app.services.explain_service import generate_explanation


router = APIRouter(prefix="", tags=["explain"])


@router.post("/explain", response_model=ExplainResponse)
def explain_bias(request: ExplainRequest):
    return generate_explanation(request.model_dump())
