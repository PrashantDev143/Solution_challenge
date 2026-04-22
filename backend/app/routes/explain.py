import logging
from fastapi import APIRouter, HTTPException, status

from app.schemas.explain import ExplainRequest, ExplainResponse
from app.services.explain_service import generate_explanation

logger = logging.getLogger(__name__)
router = APIRouter(prefix="", tags=["explain"])


@router.post("/explain", response_model=ExplainResponse, summary="Generate explanation for biased group")
def explain_bias(request: ExplainRequest):
    """Generate AI-powered explanation and recommendations for a biased group.
    
    Uses Gemini API to provide clear, actionable insights about detected bias.
    If Gemini is unavailable, returns sensible local fallback explanation.
    """
    logger.info(f"Explanation request for group: {request.group}")
    try:
        result = generate_explanation(request.model_dump())
        logger.info(f"Explanation generated successfully for group: {request.group}")
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Error generating explanation: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate explanation."
        ) from exc
